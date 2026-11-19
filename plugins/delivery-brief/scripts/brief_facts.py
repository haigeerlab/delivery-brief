#!/usr/bin/env python3
"""Collect the facts a delivery brief is written from, as one JSON object on stdout.

Read-only: never writes the project or its git state, never calls a model. Exit codes:
0 ok, 2 usage error, 3 the range cannot be resolved, 4 git error or not a repository.
The field list lives in docs/facts-schema.md.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import facts_git  # noqa: E402

SCHEMA_VERSION = 1


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
        raise UsageError("参数错误：--module 尚未实现")
    commits, files, totals, size = range_facts(root, range_info["base"], range_info["head"])
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
        "links": None,
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
