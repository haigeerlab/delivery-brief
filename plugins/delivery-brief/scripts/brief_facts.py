#!/usr/bin/env python3
"""Collect the facts a delivery brief is written from, as one JSON object on stdout.

Read-only: never writes the project or its git state, never calls a model. Exit codes:
0 ok, 2 usage error, 3 the range cannot be resolved, 4 git error or not a repository.
The field list lives in docs/facts-schema.md.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import facts_git  # noqa: E402
import facts_links  # noqa: E402
import facts_specguard  # noqa: E402

SCHEMA_VERSION = 1
MODULE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAP_PATH = "spec/CAPABILITY-MAP.md"
OTHER_MODULE_PATH = re.compile(r"^(?:spec/([a-z0-9-]+)\.md|tasks/([a-z0-9-]+)/)")


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError("参数错误：%s" % message)


def parse_args(argv):
    parser = _Parser(prog="brief_facts.py", add_help=True)
    parser.add_argument("--project", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--module")
    group.add_argument("--range", dest="range_")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    if args.module is not None and not MODULE_ID.match(args.module):
        raise UsageError("参数错误：模块 id 要是 kebab-case：%s" % args.module)
    if args.range_ is not None:
        base, sep, head = args.range_.partition("..")
        if not sep or not base or not head or head.startswith("."):
            raise UsageError("参数错误：--range 要写成 <base>..<head>")
    return args


def range_facts(project, base, head):
    """Commits, per-file changes and size for base..head (base None = from the root commit)."""
    files = facts_git.numstat(project, base, head)
    commits = [facts_git.commit_info(project, sha) for sha in facts_git.commit_shas(project, base, head)]
    changed = sum(facts_git.blob_size(project, head, f["path"]) for f in files if f["status"] != "D")
    diff = facts_git.diff_bytes(project, base, head)
    totals = {"files": len(files),
              "added": sum(f["added"] or 0 for f in files),
              "deleted": sum(f["deleted"] or 0 for f in files)}
    size = dict(totals, diffBytes=diff, changedFileBytes=changed, estimatedTokens=(diff + changed) // 4)
    return commits, files, totals, size


def _gate_key(text):
    return re.split("[：:]", text, maxsplit=1)[0].strip()


def _checked_gates(todo_text):
    return {_gate_key(item["text"]) for item in facts_specguard.parse_todo(todo_text or "")
            if item["kind"] == "gate" and item["checked"]}


def infer_module_range(root, module_id, warnings):
    """spec-guard file conventions -> (base, head, inProgress, basis). See docs/facts-schema.md."""
    todo_path = "tasks/%s/todo.md" % module_id
    touched = facts_git.path_commits(root, "HEAD", ["spec/%s.md" % module_id, "tasks/%s/" % module_id])
    if not touched:
        raise facts_git.RangeError("模块 %s 在能力图上，但还没有任何改动 spec/%s.md 或 tasks/%s/ 的提交"
                                   % (module_id, module_id, module_id))
    start = touched[0]
    head_gates = _checked_gates(facts_git.show(root, "HEAD", todo_path))
    end, end_gate = None, None
    for sha in facts_git.path_commits(root, "HEAD", [todo_path]):
        before = facts_git.parent(root, sha)
        newly = _checked_gates(facts_git.show(root, sha, todo_path)) - (
            _checked_gates(facts_git.show(root, before, todo_path)) if before else set())
        kept = [gate for gate in newly if gate in head_gates]
        if kept:
            end, end_gate = sha, sorted(kept)[-1]
    in_progress = end is None
    if in_progress:
        end = touched[-1]
    later = touched[touched.index(end) + 1:] if end in touched else []
    open_items = [item for item in facts_specguard.parse_todo(facts_git.show(root, "HEAD", todo_path) or "")
                  if not item["checked"] and not item["deferred"]]
    if in_progress:
        warnings.append("模块 %s 的 todo 里还没有勾上的（gate）检查点，按进行中处理，终点取最后一个改动模块文件的提交" % module_id)
    elif later:
        warnings.append("终点之后还有 %d 个改动模块文件的提交（%s）没算进范围：可能是发版收尾，也可能是中途 gate 之后的开发；"
                        "需要时用 --range 指定" % (len(later), "、".join(sha[:8] for sha in later)))
    basis = {
        "start": {"sha": start, "rule": "第一个改动 spec/<id>.md 或 tasks/<id>/ 的非合并提交"},
        "end": {"sha": end, "gate": end_gate,
                "rule": "最后一个把（gate）检查点勾上、且 HEAD 上仍勾着的提交" if not in_progress
                else "没有已勾的（gate）检查点，取最后一个改动模块文件的提交"},
        "laterModuleCommits": later,
        "openItemsAtHead": open_items,
    }
    return facts_git.parent(root, start), end, in_progress, basis


def mixed_module_warnings(commits, module_id, known_modules):
    warnings = []
    for commit in commits:
        others = set()
        for path in commit["files"]:
            match = OTHER_MODULE_PATH.match(path)
            name = match and (match.group(1) or match.group(2))
            if name and name != module_id and name in known_modules:
                others.add(name)
        if others:
            warnings.append("提交 %s（%s）还改了别的模块的文件：%s" % (commit["short"], commit["subject"], "、".join(sorted(others))))
    return warnings


def module_facts(root, module_id, entry, end, warnings):
    spec_path = "spec/%s.md" % module_id
    todo_path = "tasks/%s/todo.md" % module_id
    spec_text = facts_git.show(root, end, spec_path) or facts_git.show(root, "HEAD", spec_path)
    if spec_text is None:
        warnings.append("读不到 %s" % spec_path)
    spec = facts_specguard.parse_spec(spec_text or "")
    if spec_text is not None and spec["acs"] and not spec["numbered"]:
        warnings.append("%s 的成功标准没有 AC 编号，按条目顺序列出" % spec_path)
    return {
        "id": module_id,
        "responsibility": entry["responsibility"],
        "dependsOn": entry["dependsOn"],
        "spec": {"path": spec_path, "marker": spec["marker"], "acs": spec["acs"], "acsNumbered": spec["numbered"]},
        "plan": {"path": "tasks/%s/plan.md" % module_id,
                 "exists": facts_git.show(root, "HEAD", "tasks/%s/plan.md" % module_id) is not None},
        "todo": {"path": todo_path,
                 "atEnd": facts_specguard.parse_todo(facts_git.show(root, end, todo_path) or ""),
                 "atHead": facts_specguard.parse_todo(facts_git.show(root, "HEAD", todo_path) or "")},
    }


def usage_facts(root, module_id, warnings):
    drafts = {}
    for name in facts_git.list_dir(root, "HEAD", "spec/usage"):
        if name.endswith(".md"):
            drafts["spec/usage/" + name] = facts_git.show(root, "HEAD", "spec/usage/" + name) or ""
    return facts_specguard.usage_for_module(drafts, module_id, warnings) if drafts else None


def collect(args):
    root = facts_git.ensure_repo(args.project)
    head_sha = facts_git.resolve(root, "HEAD")
    warnings = []
    module = None
    usage = None
    if args.range_ is not None:
        base_rev, _, head_rev = args.range_.partition("..")
        base, head = facts_git.resolve(root, base_rev), facts_git.resolve(root, head_rev)
        range_info = {"base": base, "head": head, "source": "explicit", "inProgress": False, "basis": None}
    else:
        map_text = facts_git.show(root, "HEAD", MAP_PATH)
        if map_text is None:
            raise facts_git.RangeError("没有 %s，不是 spec-guard 项目：请改用 --range <base>..<head>" % MAP_PATH)
        known = facts_specguard.parse_map(map_text)["modules"]
        if args.module not in known:
            raise facts_git.RangeError("模块 %s 不在能力图 %s 上" % (args.module, MAP_PATH))
        base, head, in_progress, basis = infer_module_range(root, args.module, warnings)
        range_info = {"base": base, "head": head, "source": "inferred-spec-guard", "inProgress": in_progress,
                      "basis": basis}
        module = module_facts(root, args.module, known[args.module], head, warnings)
        usage = usage_facts(root, args.module, warnings)
    commits, files, totals, size = range_facts(root, range_info["base"], range_info["head"])
    if module is not None:
        warnings.extend(mixed_module_warnings(commits, args.module, known))
    return {
        "schemaVersion": SCHEMA_VERSION,
        "project": {"root": root, "name": os.path.basename(root), "head": head_sha},
        "range": range_info,
        "commits": commits,
        "files": files,
        "totals": totals,
        "size": size,
        "module": module,
        "usageDraft": usage,
        "links": facts_links.link_base(root, range_info["head"], args.offline),
        "warnings": warnings,
    }


def main(argv=None):
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        result = collect(args)
    except UsageError as error:
        print(str(error), file=sys.stderr)
        return 2
    except facts_git.RangeError as error:
        print(str(error), file=sys.stderr)
        return 3
    except facts_git.GitError as error:
        print(str(error), file=sys.stderr)
        return 4
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
