#!/usr/bin/env python3
"""Print a short view of a brief_facts.py JSON for the prepare step of /delivery-brief:brief.

Commits and files become one line each, each commit's file list and the per-module range basis of a milestone are
dropped, the code map becomes one line per group; every other field is printed as JSON. The full facts stay on disk.
Exit codes: 0 ok, 2 facts unreadable.
"""
import argparse
import copy
import json
import sys


def _commit(c):
    return "  %s %s %s" % (c.get("short", ""), (c.get("date") or "")[:10], c.get("subject", ""))


def _file(f):
    size = "binary" if f.get("binary") else "+%s -%s" % (f.get("added", 0), f.get("deleted", 0))
    return "  %s %s %s" % (f.get("status", ""), size, f.get("path", ""))


def _group(g):
    return "  %s 新增 %s 修改 %s 未改 %s 删除 %s" % (g.get("path", ""), g.get("added", 0), g.get("modified", 0),
                                               g.get("unchanged", 0), g.get("deleted", 0))


def summary(facts, path):
    rest = copy.deepcopy(facts)
    commits = rest.pop("commits")
    files = rest.pop("files")
    code_map = rest.pop("codeMap", None)
    for module in (rest.get("milestone") or {}).get("modules", []):
        if isinstance(module.get("range"), dict):
            module["range"].pop("basis", None)
    lines = []
    for key, value in rest.items():
        lines.append("%s: %s" % (key, json.dumps(value, ensure_ascii=False)))
    lines.append("commits（%d 个，每行：短号 日期 标题）:" % len(commits))
    lines.extend(_commit(c) for c in commits)
    lines.append("files（%d 个，每行：状态 增删 路径）:" % len(files))
    lines.extend(_file(f) for f in files)
    if code_map is not None:
        lines.append("codeMap（%d 组）:" % len(code_map))
        lines.extend(_group(g) for g in code_map)
    lines.append("完整 facts：%s（要每个提交改了哪些文件、各模块的推断依据时，用 python3 -c 读这个文件取对应字段）" % path)
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print a short view of brief_facts.py output.")
    parser.add_argument("--facts", required=True, help="facts JSON written by brief_facts.py")
    args = parser.parse_args(argv)
    try:
        with open(args.facts, encoding="utf-8") as fh:
            facts = json.load(fh)
        if not isinstance(facts.get("commits"), list) or not isinstance(facts.get("files"), list):
            raise ValueError("缺少 commits 或 files")
    except (OSError, ValueError, AttributeError) as exc:
        print("facts 读不了：%s（%s）" % (args.facts, str(exc).splitlines()[0]), file=sys.stderr)
        return 2
    sys.stdout.write(summary(facts, args.facts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
