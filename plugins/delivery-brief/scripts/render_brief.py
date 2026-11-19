#!/usr/bin/env python3
"""Render a brief source (Markdown subset) and the facts JSON into one self-contained HTML page.

The header numbers, status tags, warnings and the appendix (file and commit tables) come only from the facts,
never from the source, so a model cannot get them wrong. Citations become links from facts["links"].
Exit codes: 0 written, 2 usage error or unreadable input.
"""
import argparse
import datetime
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brief_markdown as md  # noqa: E402

SECTION_IDS = [("为什么改", "why"), ("产出清单", "inventory"), ("分层讲改动", "layers"), ("阅读路线", "route"),
               ("需要你判断的", "judge"), ("附录", "appendix")]
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
STATUS = {"A": "新增", "M": "修改", "D": "删除", "R": "重命名", "C": "复制", "T": "类型变化"}

CSS = """
:root{
  --bg:#fbfaf7; --panel:#ffffff; --ink:#1d1d1b; --muted:#6b6a65; --line:#e4e1d8;
  --accent:#b4532a; --accent-soft:#f6e7de; --add:#2f7a3d; --add-soft:#e3f1e5;
  --mod:#8a6512; --mod-soft:#f5ecd6; --warn:#a23b2a; --warn-soft:#f8e3df;
  --code-bg:#f3f1ec; --link:#1f5fa8;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#171716; --panel:#1f1f1d; --ink:#ecebe6; --muted:#a3a19a; --line:#34332f;
    --accent:#e08a5c; --accent-soft:#3a2a21; --add:#7fc68b; --add-soft:#1f3123;
    --mod:#e0bb62; --mod-soft:#362e1a; --warn:#ef8c7c; --warn-soft:#3b2320;
    --code-bg:#262623; --link:#86b6ef;
  }
}
:root[data-theme="dark"]{
  --bg:#171716; --panel:#1f1f1d; --ink:#ecebe6; --muted:#a3a19a; --line:#34332f;
  --accent:#e08a5c; --accent-soft:#3a2a21; --add:#7fc68b; --add-soft:#1f3123;
  --mod:#e0bb62; --mod-soft:#362e1a; --warn:#ef8c7c; --warn-soft:#3b2320;
  --code-bg:#262623; --link:#86b6ef;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Noto Sans SC",sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 16px 80px}
a{color:var(--link);text-decoration:none} a:hover{text-decoration:underline}
h1{font-size:28px;margin:0 0 6px;letter-spacing:.01em}
h2{font-size:21px;margin:48px 0 12px;padding-top:12px;border-top:1px solid var(--line)}
h3{font-size:17px;margin:28px 0 8px}
h4{font-size:15px;margin:22px 0 6px}
p{margin:8px 0}
code{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:13px;background:var(--code-bg);padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
pre{background:var(--code-bg);padding:12px 14px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.55;margin:10px 0}
pre code{background:none;padding:0}
.meta{color:var(--muted);font-size:13px}
.meta span{margin-right:14px;display:inline-block}
.tldr{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:14px 18px;margin:20px 0}
.tldr p{margin:4px 0}
.notice{background:var(--warn-soft);border-radius:8px;padding:10px 14px;margin:12px 0;font-size:14px}
.notice ul{margin:4px 0;padding-left:20px}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:8px 0 0}
table{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0;background:var(--panel)}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--code-bg);font-weight:600;white-space:nowrap}
.scroll{overflow-x:auto}
.tag{display:inline-block;font-size:12px;padding:0 7px;border-radius:10px;line-height:20px;white-space:nowrap}
.new{background:var(--add-soft);color:var(--add)}
.mod{background:var(--mod-soft);color:var(--mod)}
.flag{background:var(--warn-soft);color:var(--warn)}
.why{color:var(--muted);font-size:14px}
figure{margin:16px 0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
figcaption{font-weight:600;margin-bottom:6px}
.mermaid{text-align:center;background:none}
.output .label{font-size:12px;color:var(--muted)}
.unsupported{white-space:pre-wrap;color:var(--muted)}
.badcite{color:var(--warn)}
.filelink{font-size:12px;margin-left:2px}
details summary{cursor:pointer;color:var(--muted)}
.terms{margin:4px 0 8px;font-size:14px}
.terms dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:8px 0 0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 14px}
.terms dt{font-weight:600}
.terms dd{margin:0}
@media (max-width:560px){.terms dl{grid-template-columns:1fr}.terms dd{margin-bottom:6px}}
footer{margin-top:48px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:12px}
"""

MERMAID_INIT = """(function(){
  var t=document.documentElement.getAttribute('data-theme');
  var dark=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;
  if(window.mermaid){
    mermaid.initialize({startOnLoad:true,theme:dark?'dark':'neutral',securityLevel:'strict',flowchart:{htmlLabels:true,curve:'basis'}});
  }
})();"""


def esc(text):
    return html.escape(text, quote=True)


class Renderer:
    def __init__(self, facts):
        self.facts = facts
        self.links = facts["links"]

    def cite(self, path, start, end):
        label = path if start is None else "%s:%d%s" % (path, start, "" if end == start else "-%d" % end)
        if self.links["kind"] == "github":
            href = self.links["base"] + path
            if start is not None:
                href += self.links["lineFormat"].format(start=start, end=end)
            return '<a href="%s"><code>%s</code></a>' % (esc(href), esc(label))
        absolute = self.links["base"] + path
        vscode = "vscode://file/%s%s" % (absolute, "" if start is None else ":%d" % start)
        return ('<a href="%s"><code>%s</code></a><a class="filelink" href="%s" title="用默认程序打开文件">↗</a>'
                % (esc(vscode), esc(label), esc("file://" + absolute)))

    def inline(self, tokens):
        out = []
        for token in tokens:
            kind = token[0]
            if kind == "text":
                out.append(esc(token[1]))
            elif kind == "code":
                out.append("<code>%s</code>" % esc(token[1]))
            elif kind == "bold":
                out.append("<b>%s</b>" % esc(token[1]))
            elif kind == "link":
                url = token[2]
                if url.startswith(("https://", "http://", "#")):
                    out.append('<a href="%s">%s</a>' % (esc(url), esc(token[1])))
                else:
                    out.append(esc(token[1]))
            elif kind == "cite":
                out.append(self.cite(token[1], token[2], token[3]))
            elif kind == "outref":
                out.append('<a href="#out-%s">输出 %s</a>' % (esc(token[1]), esc(token[1])))
            else:
                out.append('<span class="badcite">%s</span>' % esc(token[1]))
        return "".join(out)

    def list_html(self, block):
        tag = "ol" if block["ordered"] else "ul"
        items = []
        for item in block["items"]:
            inner = self.inline(item["inlines"])
            if item["children"]:
                inner += self.list_html(item["children"])
            inner += "".join(self.block(b) for b in item["extra"])
            items.append("<li>%s</li>" % inner)
        return "<%s>%s</%s>" % (tag, "".join(items), tag)

    def block(self, block):
        kind = block["type"]
        if kind == "heading":
            level = min(max(block["level"], 3), 6)
            return "<h%d>%s</h%d>" % (level, self.inline(block["inlines"]), level)
        if kind == "paragraph":
            return "<p>%s</p>" % self.inline(block["inlines"])
        if kind == "list":
            return self.list_html(block)
        if kind == "table":
            head = "".join("<th>%s</th>" % self.inline(cell) for cell in block["header"])
            rows = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % self.inline(cell) for cell in row)
                           for row in block["rows"])
            return '<div class="scroll"><table><tr>%s</tr>%s</table></div>' % (head, rows)
        if kind == "code":
            if block["lang"] == "mermaid":
                caption = "<figcaption>%s</figcaption>" % esc(block["info"]) if block["info"] else ""
                return '<figure>%s<pre class="mermaid">%s</pre></figure>' % (caption, esc(block["text"]))
            if block["lang"] == "output" and block["info"]:
                return ('<div class="output" id="out-%s"><span class="label">实跑输出 %s</span><pre><code>%s</code></pre></div>'
                        % (esc(block["info"]), esc(block["info"]), esc(block["text"])))
            return "<pre><code>%s</code></pre>" % esc(block["text"])
        if kind == "details":
            inner = "".join(self.block(b) for b in block["blocks"])
            return "<details><summary>%s</summary>%s</details>" % (esc(block["summary"]), inner)
        return '<p class="unsupported">%s</p>' % esc(block["text"])

    def terms(self, block):
        rows = []
        lists = [b for b in block["blocks"] if b["type"] == "list"]
        for item in (lists[0]["items"] if lists else []):
            tokens = item["inlines"]
            if tokens and tokens[0][0] == "bold":
                rest = list(tokens[1:])
                if rest and rest[0][0] == "text":
                    rest[0] = ("text", rest[0][1].lstrip("：: "))
                rows.append("<dt>%s</dt><dd>%s</dd>" % (esc(tokens[0][1]), self.inline(rest)))
        if not rows:
            return '<details class="terms">%s</details>' % self.block(block)[len("<details>"):-len("</details>")]
        return '<details class="terms"><summary>%s</summary><dl>%s</dl></details>' % (esc(block["summary"]), "".join(rows))

    def header(self, title, intro_blocks, terms_block):
        facts = self.facts
        rng = facts["range"]
        totals = facts["totals"]
        module = facts.get("module")
        source = '<span class="tag mod">推断</span>' if rng["source"] == "inferred-spec-guard" else '<span class="tag new">指定</span>'
        span = "%s..%s" % (rng["base"][:8] if rng["base"] else "（根）", rng["head"][:8])
        meta = ["<span>%s · %s</span>" % (esc(facts["project"]["name"]), "模块讲解" if module else "提交段讲解"),
                "<span>范围 %s <code>%s</code>（%d 个提交）</span>" % (source, esc(span), len(facts["commits"])),
                "<span>%d 个文件 +%d / −%d</span>" % (totals["files"], totals["added"], totals["deleted"])]
        if rng.get("inProgress"):
            meta.append('<span><span class="tag flag">进行中</span> 还没有勾上的（gate）检查点</span>')
        elif module and any(item["checked"] and item["text"].startswith("发版") for item in module["todo"]["atHead"]):
            meta.append('<span><span class="tag new">已发版</span> todo 里的发版一项已勾</span>')
        meta.append("<span>生成于 %s</span>" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        parts = ["<header>", "<h1>%s</h1>" % self.inline(title), '<div class="meta">%s</div>' % "".join(meta)]
        notices = list(facts.get("warnings", []))
        if self.links["kind"] == "local" and self.links.get("workingTreeMatchesEnd") is False:
            notices.append("本机工作区与终点提交不一致：代码链接打开的是本机文件，行号可能对不上")
        if notices:
            parts.append('<div class="notice"><b>范围与链接说明</b><ul>%s</ul></div>'
                         % "".join("<li>%s</li>" % esc(n) for n in notices))
        if intro_blocks:
            parts.append('<div class="tldr">%s</div>' % "".join(self.block(b) for b in intro_blocks))
        if terms_block:
            parts.append(self.terms(terms_block))
        parts.append('<nav class="toc">%s</nav>' % "".join(
            '<a href="#%s">%s</a>' % (anchor, label) for anchor, label in self.toc()))
        parts.append("</header>")
        return "\n".join(parts)

    def toc(self):
        return [(anchor, ("附录 文件与提交" if title == "附录" else "%d %s" % (index, title)))
                for index, (title, anchor) in enumerate(SECTION_IDS, 1)]

    def appendix(self):
        files = "".join(
            "<tr><td><code>%s</code>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(f["path"]), (" ← <code>%s</code>" % esc(f["oldPath"])) if f.get("oldPath") else "",
                STATUS.get(f["status"], f["status"]),
                "二进制" if f["binary"] else "+%d −%d" % (f["added"], f["deleted"]))
            for f in self.facts["files"])
        commits = "".join("<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % (
            esc(c["short"]), esc(c["subject"]), esc(c["date"][:10])) for c in self.facts["commits"])
        totals = self.facts["totals"]
        return ('<details open><summary>文件表（%d 个，+%d / −%d）</summary><div class="scroll"><table>'
                '<tr><th>文件</th><th>状态</th><th>行</th></tr>%s</table></div></details>'
                '<details><summary>提交表（%d 个，不含合并提交）</summary><div class="scroll"><table>'
                '<tr><th>提交</th><th>说明</th><th>日期</th></tr>%s</table></div></details>'
                % (totals["files"], totals["added"], totals["deleted"], files, len(self.facts["commits"]), commits))

    def page(self, blocks):
        sections = md.sections(blocks)
        intro = sections[0][1]
        title_block = next((b for b in intro if b["type"] == "heading" and b["level"] == 1), None)
        module = self.facts.get("module")
        title = title_block["inlines"] if title_block else [("text", "%s 讲解" % (
            module["id"] if module else "%s..%s" % ((self.facts["range"]["base"] or "")[:8], self.facts["range"]["head"][:8])))]
        terms_block = next((b for b in intro if b["type"] == "details"), None)
        intro_blocks = [b for b in intro if b is not title_block and b is not terms_block]
        anchors = dict(SECTION_IDS)
        labels = dict(self.toc())
        body = []
        for name, section_blocks in sections[1:]:
            anchor = anchors.get(name)
            heading = labels.get(anchor, name) if anchor else name
            body.append('<h2%s>%s</h2>' % (' id="%s"' % anchor if anchor else "", esc(heading)))
            if name == "附录":
                body.append(self.appendix())
            else:
                body.extend(self.block(b) for b in section_blocks)
        rng = self.facts["range"]
        footer = ("<footer>讲解是代码的摘要，以链接指向的代码为准。范围 <code>%s..%s</code>（%s）；链接：%s。"
                  "页头与附录的数字由 delivery-brief 从 git 直接生成。</footer>"
                  % (esc((rng["base"] or "")[:8]), esc(rng["head"][:8]),
                     "按 spec-guard 文件约定推断" if rng["source"] == "inferred-spec-guard" else "指定",
                     esc(self.links["reason"])))
        title_text = md.plain(title)
        return ("<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n<main>\n%s\n%s\n%s\n</main>\n"
                "<script src=\"%s\"></script>\n<script>\n%s\n</script>\n</body>\n</html>\n"
                % (esc(title_text), CSS, self.header(title, intro_blocks, terms_block), "\n".join(body), footer,
                   MERMAID, MERMAID_INIT))


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print("参数错误：%s" % message, file=sys.stderr)
        sys.exit(2)


def main(argv=None):
    parser = _Parser(prog="render_brief.py")
    parser.add_argument("--facts", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.facts, encoding="utf-8") as handle:
            facts = json.load(handle)
        with open(args.source, encoding="utf-8") as handle:
            blocks = md.parse(handle.read())
    except (OSError, ValueError) as error:
        print("读不了输入：%s" % error, file=sys.stderr)
        return 2
    page = Renderer(facts).page(blocks)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(page)
    print(os.path.abspath(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
