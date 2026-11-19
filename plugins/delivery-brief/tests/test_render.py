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
        bracket = self.render(GOOD.replace("[[src/a.py]]", "[[`src/app/[[...slug]]/page.tsx`:L1]]"))
        self.assertIn('href="%ssrc/app/%%5B%%5B...slug%%5D%%5D/page.tsx#L1-L1"' % facts["links"]["base"], bracket)
        self.assertIn("<code>src/app/[[...slug]]/page.tsx:1</code>", bracket)

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


CROSS = {"status": "complete", "backend": "codex", "model": "unknown", "reportPath": "/tmp/r.json",
         "coverage": {"reviewed": 6, "unreviewed": 0},
         "findings": [{"title": "AC1 证据写过头", "verdict": "confirmed", "note": "已改为只证明了一部分"},
                      {"title": "提交数写错", "verdict": "rejected", "note": "页头数字由脚本生成，见 facts.commits"},
                      {"title": "边界没测到", "verdict": "unverified", "note": "需要装依赖才能跑"}]}


class CrossCheckRenderTest(CheckCase):
    render = RenderTest.render
    def render_with(self, cross, expect=0):
        path = os.path.join(self.tmp.name, "cross.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(cross if isinstance(cross, str) else json.dumps(cross, ensure_ascii=False))
        src = os.path.join(self.tmp.name, "brief.md")
        out = os.path.join(self.tmp.name, "brief.html")
        with open(src, "w", encoding="utf-8") as handle:
            handle.write(GOOD)
        proc = subprocess.run([sys.executable, "-B", str(RENDER), "--facts", self.facts_path, "--source", src,
                               "--out", out, "--cross-check", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = proc.stderr.decode("utf-8")
        self.assertEqual(proc.returncode, expect, err)
        self.assertNotIn("Traceback", err)
        if expect:
            return err
        with open(out, encoding="utf-8") as handle:
            return handle.read()

    def test_complete_record_and_footer(self):
        html = self.render_with(CROSS)
        appendix = html.split('id="appendix"')[1]
        self.assertIn("交叉核对记录", appendix)
        for finding in CROSS["findings"]:
            self.assertIn(finding["title"], appendix)
            self.assertIn(finding["note"], appendix)
        for label in ("成立，已改", "不成立", "没有核实"):
            self.assertIn(label, appendix)
        footer = html.split("<footer>")[1]
        self.assertIn("交叉核对（codex）：3 条发现，1 条成立已改，1 条不成立，1 条没有核实", footer)

    def test_incomplete(self):
        cross = dict(CROSS, status="incomplete", reason="delegate 报告有 2 个文件没审查", findings=[])
        footer = self.render_with(cross).split("<footer>")[1]
        self.assertIn("交叉核对没有完成：delegate 报告有 2 个文件没审查", footer)

    def test_invalid_records_exit_2(self):
        bad = json.loads(json.dumps(CROSS))
        bad["findings"][0]["verdict"] = "maybe"
        self.assertIn("verdict", self.render_with(bad, expect=2))
        missing = dict(CROSS)
        missing.pop("coverage")
        self.assertIn("coverage", self.render_with(missing, expect=2))
        self.assertIn("reason", self.render_with(dict(CROSS, status="incomplete"), expect=2))
        self.render_with("{not json", expect=2)

    def test_without_flag_nothing_changes(self):
        first = re.sub(r"生成于 [0-9: -]+", "", self.render())
        second = re.sub(r"生成于 [0-9: -]+", "", self.render())
        self.assertEqual(first, second)
        self.assertNotIn("交叉核对", first)


SHOT_SOURCE = GOOD.replace("## 分层讲改动", "```screenshot 登录页\n/login\n```\n\n```screenshot 看板\n/dash\n```\n\n## 分层讲改动")


def shot_record(**changes):
    record = {"baseUrl": "http://127.0.0.1:5173", "chrome": "/x/Chrome", "viewport": [1280, 800], "origin": "export",
              "shots": [{"title": "登录页", "path": "/login", "file": "01.png", "status": "ok", "reason": "",
                         "httpStatus": 200, "finalUrl": "http://127.0.0.1:5173/login"},
                        {"title": "看板", "path": "/dash", "file": "02.png", "status": "failed",
                         "reason": "需要登录，未截到", "httpStatus": 200, "finalUrl": "http://127.0.0.1:5173/login"}]}
    record.update(changes)
    return record


class ScreenshotRenderTest(CheckCase):
    def run_render(self, source, *extra, record=None, expect=0):
        src = os.path.join(self.tmp.name, "brief.md")
        out = os.path.join(self.tmp.name, "brief.html")
        with open(src, "w", encoding="utf-8") as handle:
            handle.write(source)
        args = list(extra)
        if record is not None:
            shots_dir = os.path.join(self.tmp.name, "brief.shots")
            os.makedirs(shots_dir, exist_ok=True)
            path = os.path.join(shots_dir, "shots.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(record if isinstance(record, str) else json.dumps(record, ensure_ascii=False))
            args += ["--shots", path]
        proc = subprocess.run([sys.executable, "-B", str(RENDER), "--facts", self.facts_path, "--source", src,
                               "--out", out, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = proc.stderr.decode("utf-8")
        self.assertEqual(proc.returncode, expect, err)
        self.assertNotIn("Traceback", err)
        if expect:
            return err
        with open(out, encoding="utf-8") as handle:
            return re.sub(r"生成于 [0-9: -]+", "", handle.read())

    def inventory(self, html):
        return html.split('id="inventory"')[1].split("<h2")[0]

    def test_ok_and_failed_shots(self):
        part = self.inventory(self.run_render(SHOT_SOURCE, record=shot_record()))
        self.assertIn('<img src="brief.shots/01.png" alt="登录页"', part)
        self.assertIn('width="1280" height="800"', part)
        self.assertNotIn("loading=", part)
        self.assertIn("登录页", part)
        self.assertIn("截图未生成：需要登录，未截到", part)
        self.assertNotIn("02.png", part)

    def test_appendix_names_the_source(self):
        appendix = self.run_render(SHOT_SOURCE, record=shot_record()).split('id="appendix"')[1]
        self.assertIn("截图来源", appendix)
        self.assertIn("导出", appendix)
        user = self.run_render(SHOT_SOURCE, record=shot_record(origin="base-url")).split('id="appendix"')[1]
        self.assertIn("未核对与终点提交一致", user)

    def test_without_record_or_skipped(self):
        part = self.inventory(self.run_render(SHOT_SOURCE))
        self.assertEqual(part.count("截图未生成：没有截图"), 2)
        part = self.inventory(self.run_render(SHOT_SOURCE, "--shots-skipped", "指定了 --no-screenshots"))
        self.assertEqual(part.count("截图未生成：指定了 --no-screenshots"), 2)

    def test_record_that_does_not_match_the_source(self):
        record = shot_record()
        record["shots"][0]["path"] = "/other"
        part = self.inventory(self.run_render(SHOT_SOURCE, record=record))
        self.assertIn("截图未生成：截图记录和讲解对不上", part)

    def test_invalid_record_exits_2(self):
        self.assertIn("shots", self.run_render(SHOT_SOURCE, record={"baseUrl": "x"}, expect=2))
        bad = shot_record()
        bad["shots"][1]["status"] = "maybe"
        self.assertIn("status", self.run_render(SHOT_SOURCE, record=bad, expect=2))
        self.run_render(SHOT_SOURCE, record="{not json", expect=2)

    def test_brief_without_screenshot_blocks_is_unchanged(self):
        plain = self.run_render(GOOD)
        self.assertEqual(plain, self.run_render(GOOD, record=shot_record(shots=[])))
        self.assertEqual(plain, self.run_render(GOOD, "--shots-skipped", "指定了 --no-screenshots"))
        self.assertNotIn("截图", plain)


from test_check import MILESTONE_GOOD, MilestoneCheckCase  # noqa: E402


class MilestoneRenderTest(MilestoneCheckCase):
    def render_milestone(self, facts=None):
        if facts is not None:
            with open(self.facts_path, "w", encoding="utf-8") as handle:
                json.dump(facts, handle, ensure_ascii=False)
        out_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(out_dir, exist_ok=True)
        src = os.path.join(out_dir, "milestone-M1.md")
        out = os.path.join(out_dir, "milestone-M1.html")
        with open(src, "w", encoding="utf-8") as handle:
            handle.write(MILESTONE_GOOD)
        proc = subprocess.run([sys.executable, "-B", str(RENDER), "--facts", self.facts_path, "--source", src, "--out", out],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8"))
        with open(out, encoding="utf-8") as handle:
            return handle.read()

    def load(self):
        with open(self.facts_path, encoding="utf-8") as handle:
            return json.load(handle)

    def section(self, html, anchor):
        return html.split('id="%s"' % anchor)[1].split("<h2")[0]

    def test_header(self):
        header = self.render_milestone().split('<nav class="toc">')[0]
        self.assertIn("里程碑讲解", header)
        self.assertIn("M1", header)
        self.assertIn("U1 跑一次", header)
        self.assertIn("2 个模块", header)
        self.assertIn("还没确认", header)
        facts = self.load()
        facts["milestone"]["confirmed"] = True
        self.assertIn("已确认", self.render_milestone(facts).split('<nav class="toc">')[0])
        facts["range"]["inProgress"] = True
        self.assertIn("进行中", self.render_milestone(facts).split('<nav class="toc">')[0])

    def test_sections_and_toc(self):
        html = self.render_milestone()
        for number, title in enumerate(("这一站做成了什么", "代码地图", "沿典型用法走一遍", "跨模块约定", "各模块讲解", "需要你判断的"), 1):
            self.assertIn("%d %s" % (number, title), html)
        self.assertNotIn('id="why"', html)

    def test_code_map_from_facts(self):
        facts = self.load()
        part = self.section(self.render_milestone(), "codemap")
        self.assertIn("新增都在", part)
        for group in facts["codeMap"]:
            self.assertIn("<code>%s</code>" % group["path"], part)
        changed, unchanged = part.split("<details")[0], part.split("<details")[1]
        self.assertIn("<code>src/alpha</code>", changed)
        self.assertIn("<code>spec/usage</code>", unchanged)
        self.assertNotIn("<code>spec/usage</code>", changed)

    def test_module_table_links(self):
        out_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(out_dir, exist_ok=True)
        open(os.path.join(out_dir, "alpha.html"), "w").close()
        part = self.section(self.render_milestone(), "modules")
        self.assertIn('<a href="alpha.html">', part)
        self.assertIn("还没生成", part)
        self.assertIn("/delivery-brief:brief beta", part)
        self.assertIn("做 A", part)
        self.assertNotIn('href="beta.html"', part)
        self.assertNotIn("（由脚本生成）", part)
