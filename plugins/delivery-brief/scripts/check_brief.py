#!/usr/bin/env python3
"""Check a brief source (Markdown subset) against the facts JSON before it is rendered.

Only what a machine can judge reliably: the six sections and their order, every citation resolves at the end
commit, every AC and every judgement item carries evidence (a citation or a real-run output), the reading
route, the layer count, commit ids stay inside the range. Whether the narrative is right is not checked.

Exit codes: 0 pass (warnings allowed), 1 errors, 2 usage error. Each report line is `error|warn <where>：<what>`.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brief_markdown as md  # noqa: E402
import facts_git  # noqa: E402

SECTIONS = ("为什么改", "产出清单", "分层讲改动", "阅读路线", "需要你判断的", "附录")
HEX = re.compile(r"(?<![0-9A-Za-z])[0-9a-f]{7,40}(?![0-9A-Za-z])")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print("参数错误：%s" % message, file=sys.stderr)
        sys.exit(2)


def _has_evidence(tokens):
    return any(token[0] in ("cite", "outref") for token in tokens)


def _item_tokens(item):
    tokens = list(item["inlines"])
    if item["children"]:
        for sub in item["children"]["items"]:
            tokens.extend(sub["inlines"])
    return tokens


class Checker:
    def __init__(self, facts, blocks):
        self.facts = facts
        self.blocks = blocks
        self.errors, self.warnings = [], []
        self.root = facts["project"]["root"]
        self.head = facts["range"]["head"]
        self._lines = {}

    def error(self, where, what):
        self.errors.append("error %s：%s" % (where, what))

    def warn(self, where, what):
        self.warnings.append("warn %s：%s" % (where, what))

    def run(self):
        sections = md.sections(self.blocks)
        found = {title: blocks for title, blocks in sections if title}
        self.check_sections([title for title, _ in sections if title])
        self.check_citations()
        self.check_unsupported(self.blocks)
        if "为什么改" in found:
            self.check_why(found["为什么改"])
        if "分层讲改动" in found:
            layers = [b for b in found["分层讲改动"] if b["type"] == "heading" and b["level"] == 3]
            if not 3 <= len(layers) <= 7:
                self.error("分层讲改动", "要分 3～7 层（三级标题），现在 %d 层" % len(layers))
        if "阅读路线" in found:
            self.check_route(found["阅读路线"])
        if "需要你判断的" in found:
            self.check_judgements(found["需要你判断的"])
        if "附录" in found and any(b["type"] != "paragraph" for b in found["附录"]):
            self.warn("附录", "附录由渲染脚本从 facts 生成，这里写的表格、列表不会显示，只留一行占位即可")
        self.check_commit_ids()

    def check_sections(self, titles):
        for name in SECTIONS:
            if name not in titles:
                self.error("结构", "缺少「%s」一节（二级标题）" % name)
        present = [t for t in titles if t in SECTIONS]
        if present != [s for s in SECTIONS if s in present]:
            self.error("结构", "六节的顺序应为 %s，现在是 %s" % ("、".join(SECTIONS), "、".join(present)))
        for title in titles:
            if title not in SECTIONS:
                self.warn("结构", "多出一节「%s」：页面会照样显示，但不在固定的六问里" % title)

    def line_count(self, path):
        if path not in self._lines:
            text = facts_git.show(self.root, self.head, path)
            self._lines[path] = None if text is None else max(1, len(text.splitlines()))
        return self._lines[path]

    def check_citations(self):
        outputs = md.output_blocks(self.blocks)
        for _, path, start, end in md.citations(self.blocks):
            count = self.line_count(path)
            if count is None:
                self.error("引用 %s" % path, "终点提交 %s 上不存在这个文件" % self.head[:8])
            elif end is not None and end > count:
                self.error("引用 %s:L%d-L%d" % (path, start, end), "行号超出文件行数（%d 行）" % count)
        for token in md.tokens_of(self.blocks, "badcite"):
            self.error("引用 %s" % token[1], "引用写法不对：应为 [[路径]]、[[路径:L12]]、[[路径:L12-L30]] 或 [[out:O1]]")
        for token in md.tokens_of(self.blocks, "outref"):
            if token[1] not in outputs:
                self.error("引用 out:%s" % token[1], "没有编号为 %s 的实跑输出块（```output %s）" % (token[1], token[1]))
        for name, block in outputs.items():
            if not block["text"].startswith("$ "):
                self.error("实跑输出 %s（第 %d 行）" % (name, block["line"]), "第一行要是所跑的命令，以「$ 」开头")

    def check_unsupported(self, blocks):
        for block in blocks:
            if block["type"] == "code" and block["lang"] == "mermaid" and not block["info"]:
                self.warn("第 %d 行" % block["line"], "图没有标题：写成 ```mermaid <一句结论>，标题写结论不写图名")
            if block["type"] == "unsupported":
                self.warn("第 %d 行" % block["line"], "不支持的写法，会原样显示：%s" % block["text"][:40])
            elif block["type"] == "details":
                self.check_unsupported(block["blocks"])
            elif block["type"] == "list":
                for item in block["items"]:
                    extras = list(item["extra"])
                    if item["children"]:
                        for sub in item["children"]["items"]:
                            extras.extend(sub["extra"])
                    self.check_unsupported(extras)

    def check_why(self, blocks):
        module = self.facts.get("module")
        if not module:
            return
        tables = [b for b in blocks if b["type"] == "table" and md.plain(b["header"][0]).strip().upper().startswith("AC")]
        if not tables:
            self.error("为什么改", "没有 AC 表（第一列表头以 AC 开头），每条验收标准要逐条给证据")
            return
        seen = set()
        for table in tables:
            for index, row in enumerate(table["rows"], 1):
                label = md.plain(row[0]).strip()
                seen.add(label)
                if not any(_has_evidence(cell) for cell in row[1:]):
                    self.error("为什么改 %s" % (label or "第 %d 行" % index),
                               "证据格没有引用或实跑输出（证据只能是测试断言、代码行或实跑输出）")
        if module["spec"].get("acsNumbered"):
            for ac in module["spec"]["acs"]:
                if ac["id"] not in seen:
                    self.error("为什么改", "AC 表里缺 %s" % ac["id"])

    def check_route(self, blocks):
        lists = [b for b in blocks if b["type"] == "list"]
        if not lists or not lists[0]["ordered"]:
            self.error("阅读路线", "要写成有序列表（1. 2. 3.），按阅读顺序")
            return
        items = lists[0]["items"]
        if not 3 <= len(items) <= 7:
            self.error("阅读路线", "要列 3～7 处，现在 %d 处" % len(items))
        for index, item in enumerate(items, 1):
            if not any(t[0] == "cite" for t in item["inlines"]):
                self.error("阅读路线 第 %d 条" % index, "没有指向代码的引用")

    def check_judgements(self, blocks):
        lists = [b for b in blocks if b["type"] == "list"]
        if not lists:
            self.error("需要你判断的", "要写成列表，每条一个事实并附证据")
            return
        for index, item in enumerate(lists[0]["items"], 1):
            if not _has_evidence(_item_tokens(item)):
                self.error("需要你判断的 第 %d 条" % index, "没有引用或实跑输出")

    def check_commit_ids(self):
        allowed = [c["sha"] for c in self.facts["commits"]]
        rng = self.facts["range"]
        allowed += [s for s in (rng["base"], rng["head"], self.facts["project"]["head"]) if s]
        if rng.get("basis"):
            allowed += rng["basis"].get("laterModuleCommits", [])
        marker = (self.facts.get("module") or {}).get("spec", {}).get("marker") or ""
        texts = [t[1] for kind in ("text", "code", "bold") for t in md.tokens_of(self.blocks, kind)]
        for text in texts:
            for match in HEX.finditer(text):
                word = match.group(0)
                if not re.search(r"[a-f]", word) or not re.search(r"\d", word) or word in marker:
                    continue
                if not any(sha.startswith(word) for sha in allowed):
                    self.error("提交号 %s" % word, "不在本次范围内（也不是范围端点或终点之后的模块提交）")


def main(argv=None):
    parser = _Parser(prog="check_brief.py")
    parser.add_argument("--facts", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.facts, encoding="utf-8") as handle:
            facts = json.load(handle)
        with open(args.source, encoding="utf-8") as handle:
            blocks = md.parse(handle.read())
    except (OSError, ValueError) as error:
        print("读不了输入：%s" % error, file=sys.stderr)
        return 2
    checker = Checker(facts, blocks)
    try:
        checker.run()
    except facts_git.GitError as error:
        print("git 出错：%s" % error, file=sys.stderr)
        return 2
    for line in checker.errors + checker.warnings:
        print(line)
    print("结果：%d 个错误，%d 个提醒" % (len(checker.errors), len(checker.warnings)))
    return 1 if checker.errors else 0


if __name__ == "__main__":
    sys.exit(main())
