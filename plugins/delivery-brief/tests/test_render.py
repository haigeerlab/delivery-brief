"""render_brief.py: header and appendix numbers come only from facts; links, tags, escaping (AC2, AC3)."""
import json
import os
import re
import subprocess
import sys

from fixtures import SCRIPTS
from test_check import GOOD, CheckCase

RENDER = SCRIPTS / "render_brief.py"


class RenderTest(CheckCase):
    def load(self):
        with open(self.facts_path, encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, facts):
        with open(self.facts_path, "w", encoding="utf-8") as handle:
            json.dump(facts, handle, ensure_ascii=False)

    def render(self, source=GOOD):
        src = os.path.join(self.tmp.name, "brief.md")
        out = os.path.join(self.tmp.name, "brief.html")
        with open(src, "w", encoding="utf-8") as handle:
            handle.write(source)
        proc = subprocess.run([sys.executable, "-B", str(RENDER), "--facts", self.facts_path, "--source", src,
                               "--out", out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8"))
        with open(out, encoding="utf-8") as handle:
            return handle.read()

    def test_header_numbers_come_from_facts(self):
        facts = self.load()
        html = self.render()
        totals = facts["totals"]
        header = html.split('<nav class="toc">')[0]
        self.assertIn("%d 个提交" % len(facts["commits"]), header)
        self.assertIn("%d 个文件 +%d / −%d" % (totals["files"], totals["added"], totals["deleted"]), header)
        self.assertIn(facts["range"]["head"][:8], header)

    def test_appendix_tables_from_facts(self):
        facts = self.load()
        appendix = self.render().split('id="appendix"')[1]
        for entry in facts["files"]:
            self.assertIn(entry["path"], appendix)
        for commit in facts["commits"]:
            self.assertIn(commit["short"], appendix)
            self.assertIn(commit["subject"], appendix)
        self.assertNotIn("（由脚本生成）", appendix)

    def test_status_tags(self):
        html = self.render()
        self.assertIn("推断", html)
        self.assertIn("已发版", html)
        facts = self.load()
        facts["range"]["source"] = "explicit"
        facts["range"]["inProgress"] = True
        facts["module"]["todo"]["atHead"] = []
        self.save(facts)
        html = self.render()
        header = html.split('<nav class="toc">')[0]
        self.assertIn("指定", header)
        self.assertIn("进行中", header)
        self.assertNotIn("已发版", header)

    def test_release_tag_only_for_a_release_item(self):
        facts = self.load()
        facts["module"]["todo"]["atHead"] = [{"text": "Task 1：骨架（版本在 M1 发版时定）", "checked": True,
                                              "kind": "task", "deferred": False}]
        self.save(facts)
        self.assertNotIn("已发版", self.render().split('<nav class="toc">')[0])

    def test_warnings_shown_in_header(self):
        facts = self.load()
        facts["warnings"] = ["终点之后还有 1 个提交没算进范围"]
        self.save(facts)
        header = self.render().split('<nav class="toc">')[0]
        self.assertIn("终点之后还有 1 个提交没算进范围", header)

    def test_local_links(self):
        facts = self.load()
        html = self.render()
        root = facts["links"]["base"]
        self.assertIn('href="vscode://file/%ssrc/a.py:1"' % root, html)
        self.assertIn("src/a.py:1", html)

    def test_github_links(self):
        facts = self.load()
        facts["links"] = {"kind": "github", "base": "https://github.com/acme/demo/blob/%s/" % facts["range"]["head"],
                          "lineFormat": "#L{start}-L{end}", "repo": "acme/demo", "workingTreeMatchesEnd": None,
                          "reason": "公开"}
        self.save(facts)
        html = self.render()
        self.assertIn('href="%sspec/alpha.md#L1-L3"' % facts["links"]["base"], html)
        self.assertIn('href="%ssrc/a.py"' % facts["links"]["base"], html)

    def test_working_tree_mismatch_is_flagged(self):
        facts = self.load()
        facts["links"]["workingTreeMatchesEnd"] = False
        self.save(facts)
        self.assertIn("本机工作区与终点提交不一致", self.render())

    def test_escaping_and_unsupported(self):
        source = GOOD.replace("说明 [[src/a.py:L1]]。", "说明 <script>alert(1)</script> 与 `a < b & c` [[src/a.py:L1]]。")
        source = source.replace("## 产出清单", "<div>原样显示</div>\n\n## 产出清单")
        html = self.render(source)
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("<code>a &lt; b &amp; c</code>", html)
        self.assertIn("&lt;div&gt;原样显示&lt;/div&gt;", html)

    def test_mermaid_and_output_blocks(self):
        source = GOOD.replace("### L2 计划", "```mermaid 入口只调一个脚本\nflowchart LR\n  A --> B\n```\n\n### L2 计划")
        html = self.render(source)
        self.assertIn('<figcaption>入口只调一个脚本</figcaption>', html)
        self.assertIn('<pre class="mermaid">flowchart LR\n  A --&gt; B</pre>', html)
        self.assertIn('id="out-O1"', html)
        self.assertIn('href="#out-O1"', html)

    def test_terms_and_tldr(self):
        source = "# alpha：做 A\n\n一句话总结。\n\n" + GOOD
        html = self.render(source)
        self.assertIn("<h1>alpha：做 A</h1>", html)
        self.assertIn('class="tldr"', html)
        self.assertIn("<dt>能力图</dt>", html)
        self.assertIn("<dd>模块表。</dd>", html)

    def test_single_file_only_mermaid_from_cdn(self):
        html = self.render()
        scripts = re.findall(r'<script[^>]*src="([^"]+)"', html)
        self.assertEqual(scripts, ["https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"])
        self.assertNotIn("<link", html)
        self.assertIn("prefers-color-scheme: dark", html)

    def test_sections_numbered_with_anchors(self):
        html = self.render()
        for anchor in ("why", "inventory", "layers", "route", "judge", "appendix"):
            self.assertIn('id="%s"' % anchor, html)
        self.assertIn("1 为什么改", html)
