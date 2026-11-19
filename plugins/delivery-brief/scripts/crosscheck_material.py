#!/usr/bin/env python3
"""Prepare the review material for a --cross-check: a throwaway git repository delegate can review.

It holds the brief source, the facts, the range diff and every cited file as it is at the end commit, plus
MATERIAL.md saying what each file is. delegate inlines files up to about 1 MiB, so when the material is over the
limit the largest cited files are cut to windows around their citations (with line numbers) until it fits;
if it still does not fit, exit 3 rather than let the reviewer see less than it thinks.
Exit codes: 0 written, 2 usage error or unreadable input, 3 over the limit, 4 git error.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brief_markdown as md  # noqa: E402
import facts_git  # noqa: E402

DEFAULT_LIMIT = 900000
CONTEXT = 40
HEAD_LINES = 80


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print("参数错误：%s" % message, file=sys.stderr)
        sys.exit(2)


def windows(text, spans):
    """Keep the lines around each (start, end) span, numbered; a span of None keeps the first HEAD_LINES lines."""
    lines = text.splitlines()
    keep = set()
    for start, end in spans:
        if start is None:
            keep.update(range(1, min(len(lines), HEAD_LINES) + 1))
        else:
            keep.update(range(max(1, start - CONTEXT), min(len(lines), end + CONTEXT) + 1))
    out, previous = [], 0
    for number in sorted(keep):
        if number != previous + 1:
            out.append("…（省略第 %d–%d 行）" % (previous + 1, number - 1))
        out.append("%d: %s" % (number, lines[number - 1]))
        previous = number
    if previous < len(lines):
        out.append("…（省略第 %d–%d 行）" % (previous + 1, len(lines)))
    return "\n".join(out) + "\n"


def build(facts, source_text, limit):
    """Return ({relative path: text}, notes) or raise ValueError when it cannot fit."""
    root, head = facts["project"]["root"], facts["range"]["head"]
    base = facts["range"]["base"]
    files = {
        "brief.md": source_text,
        "facts.json": json.dumps(facts, ensure_ascii=False, indent=1) + "\n",
        "range.diff": facts_git.run(root, "diff", "-M", base or facts_git.EMPTY_TREE, head).stdout.decode("utf-8", "replace"),
    }
    spans, missing = {}, []
    for _, path, start, end in md.citations(md.parse(source_text)):
        spans.setdefault(path, []).append((start, end))
    for path in sorted(spans):
        text = facts_git.show(root, head, path)
        if text is None:
            missing.append(path)
        else:
            files["source/" + path] = text
    windowed = []

    def size():
        return sum(len(text.encode("utf-8")) for text in files.values())

    candidates = sorted((p for p in files if p.startswith("source/")), key=lambda p: -len(files[p].encode("utf-8")))
    for path in candidates:
        if size() <= limit:
            break
        files[path] = windows(files[path], spans[path[len("source/"):]])
        windowed.append(path)
    if size() > limit:
        listing = "；".join("%s %d 字节" % (p, len(t.encode("utf-8"))) for p, t in sorted(files.items()))
        raise ValueError("材料 %d 字节，截取后仍超过上限 %d：%s" % (size(), limit, listing))
    return files, windowed, missing


def material_doc(files, windowed, missing, facts):
    rng = facts["range"]
    lines = ["# 审查材料", "",
             "讲解的范围：`%s..%s`（%s）。被引用的文件都取自终点提交 `%s`，不是工作区。" % (
                 (rng["base"] or "")[:8], rng["head"][:8], rng["source"], rng["head"][:8]), "",
             "| 文件 | 是什么 | 字节 |", "|---|---|---|"]
    what = {"brief.md": "讲解源文件（要核对的对象）", "facts.json": "脚本从 git 收集的事实，页头与附录的数字来自这里",
            "range.diff": "本次范围的完整 diff"}
    for path in sorted(files):
        kind = what.get(path) or ("被引用的文件，**截取**：只保留引用行前后各 %d 行，行首是原行号" % CONTEXT
                                  if path in windowed else "被引用的文件（完整）")
        lines.append("| `%s` | %s | %d |" % (path, kind, len(files[path].encode("utf-8"))))
    if missing:
        lines += ["", "终点提交上不存在、没有放进来的被引用文件：%s" % "、".join("`%s`" % p for p in missing)]
    return "\n".join(lines) + "\n"


def write_repo(out, files):
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for path, text in files.items():
        target = os.path.join(out, path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
    env = dict(os.environ, GIT_AUTHOR_NAME="delivery-brief", GIT_AUTHOR_EMAIL="delivery-brief@localhost",
               GIT_COMMITTER_NAME="delivery-brief", GIT_COMMITTER_EMAIL="delivery-brief@localhost")
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "审查材料"]):
        proc = subprocess.run(["git", *args], cwd=out, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise facts_git.GitError("材料仓库 git %s 失败：%s" % (args[0], proc.stderr.decode("utf-8", "replace").strip()))


def main(argv=None):
    parser = _Parser(prog="crosscheck_material.py")
    parser.add_argument("--facts", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args(argv)
    try:
        with open(args.facts, encoding="utf-8") as handle:
            facts = json.load(handle)
        with open(args.source, encoding="utf-8") as handle:
            source_text = handle.read()
    except (OSError, ValueError) as error:
        print("读不了输入：%s" % error, file=sys.stderr)
        return 2
    try:
        files, windowed, missing = build(facts, source_text, args.limit)
        files["MATERIAL.md"] = material_doc(files, windowed, missing, facts)
        write_repo(os.path.abspath(args.out), files)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 3
    except facts_git.GitError as error:
        print(str(error), file=sys.stderr)
        return 4
    total = sum(len(t.encode("utf-8")) for t in files.values())
    print("material %s" % os.path.abspath(args.out))
    print("bytes %d" % total)
    print("paths %s" % " ".join(sorted({p.split("/")[0] for p in files})))
    for path in windowed:
        print("windowed %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
