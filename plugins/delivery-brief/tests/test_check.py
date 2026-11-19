"""check_brief.py: structure, citations, evidence and reading-route rules (AC3, AC4)."""
import json
import os
import subprocess
import sys

import test_module_range
from fixtures import GIT_ENV, SCRIPTS, RepoCase

CHECK = SCRIPTS / "check_brief.py"

GOOD = """<details>
<summary>先懂这几个词</summary>

- **能力图**：模块表。

</details>

## 为什么改

| AC | 证据 |
|---|---|
| AC1 | [[src/a.py:L1]] |
| AC2 | 实跑 [[out:O1]] |

```output O1
$ python3 src/a.py
a
```

## 产出清单

| 项 | 位置 |
|---|---|
| `a.py` | [[src/a.py]] |

## 分层讲改动

### L1 入口

说明 [[src/a.py:L1]]。

### L2 计划

见 [[tasks/alpha/plan.md]]。

### L3 记录

见 [[spec/alpha.md:L1-L3]]。

## 阅读路线

1. [[spec/alpha.md]]：先看 Spec。
2. [[src/a.py:L1]]：再看实现。
3. [[tasks/alpha/todo.md]]：最后看 todo。

## 需要你判断的

- 只有一行实现 [[src/a.py:L1]]。
- 跑出来是 a [[out:O1]]。

## 附录

（由脚本生成）
"""


class CheckCase(RepoCase):
    base_repo = test_module_range.ModuleRangeTest.base_repo
    finished_alpha = test_module_range.ModuleRangeTest.finished_alpha

    def setUp(self):
        super().setUp()
        self.finished_alpha()
        self.facts_path = os.path.join(self.tmp.name, "facts.json")
        with open(self.facts_path, "w", encoding="utf-8") as handle:
            json.dump(self.facts("--module", "alpha", "--offline"), handle, ensure_ascii=False)

    def check(self, source):
        path = os.path.join(self.tmp.name, "brief.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(source)
        proc = subprocess.run([sys.executable, "-B", str(CHECK), "--facts", self.facts_path, "--source", path],
                              env=dict(os.environ, **GIT_ENV), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = proc.stdout.decode("utf-8").splitlines()
        self.assertNotIn("Traceback", proc.stderr.decode("utf-8"))
        return proc.returncode, [l for l in lines if l.startswith("error")], [l for l in lines if l.startswith("warn")]

    def assertError(self, source, *phrases):
        code, errors, _ = self.check(source)
        self.assertEqual(code, 1, errors)
        joined = "\n".join(errors)
        for phrase in phrases:
            self.assertIn(phrase, joined)


class CheckTest(CheckCase):
    def test_good_source_passes(self):
        code, errors, warnings = self.check(GOOD)
        self.assertEqual((code, errors, warnings), (0, [], []))

    def test_missing_section(self):
        self.assertError(GOOD.replace("## 阅读路线", "## 别的"), "缺少「阅读路线」")

    def test_section_order(self):
        swapped = GOOD.replace("## 为什么改", "## TMP").replace("## 产出清单", "## 为什么改").replace("## TMP", "## 产出清单")
        self.assertError(swapped, "顺序")

    def test_citation_file_missing(self):
        self.assertError(GOOD.replace("[[src/a.py]]", "[[src/nope.py]]"), "src/nope.py", "不存在")

    def test_citation_line_out_of_range(self):
        self.assertError(GOOD.replace("[[src/a.py:L1]]：再看", "[[src/a.py:L5-L9]]：再看"), "src/a.py", "行号")

    def test_bad_citation_syntax(self):
        self.assertError(GOOD.replace("[[src/a.py]]", "[[src/a.py:L3-L1]]"), "引用写法")

    def test_unknown_output_reference(self):
        self.assertError(GOOD.replace("跑出来是 a [[out:O1]]", "跑出来是 a [[out:O9]]"), "O9")

    def test_ac_without_evidence(self):
        self.assertError(GOOD.replace("| AC1 | [[src/a.py:L1]] |", "| AC1 | 见 Spec 原话 |"), "AC1", "证据")

    def test_ac_missing_from_table(self):
        self.assertError(GOOD.replace("| AC2 | 实跑 [[out:O1]] |\n", ""), "AC2")

    def test_judgement_without_evidence(self):
        self.assertError(GOOD.replace("- 只有一行实现 [[src/a.py:L1]]。", "- 只有一行实现。"), "需要你判断的", "第 1 条")

    def test_judgement_items_after_an_output_block_are_checked(self):
        source = GOOD.replace("- 跑出来是 a [[out:O1]]。", "- 跑出来是 a [[out:O1]]。\n\n```output O2\n$ true\n```\n\n- 第三条没有证据。")
        self.assertError(source, "需要你判断的", "第 3 条")

    def test_route_must_be_ordered_with_citations(self):
        self.assertError(GOOD.replace("1. [[spec/alpha.md]]", "- [[spec/alpha.md]]"), "阅读路线")
        self.assertError(GOOD.replace("2. [[src/a.py:L1]]：再看实现。", "2. 再看实现。"), "阅读路线", "第 2 条")
        self.assertError(GOOD.replace("3. [[tasks/alpha/todo.md]]：最后看 todo。\n", ""), "阅读路线", "3～7")

    def shot(self, *blocks):
        body = "".join("```screenshot %s\n%s\n```\n\n" % pair for pair in blocks)
        return GOOD.replace("## 分层讲改动", body + "## 分层讲改动")

    def test_screenshot_blocks_in_inventory_pass(self):
        code, errors, warnings = self.check(self.shot(*[("页面 %d" % i, "/p%d" % i) for i in range(8)]))
        self.assertEqual((code, errors, warnings), (0, [], []))

    def test_screenshot_rules(self):
        self.assertError(self.shot(("登录页", "login")), "截图", "/")
        self.assertError(self.shot(("登录页", "/a/../b")), "截图", "..")
        self.assertError(self.shot(("登录页", "/a b")), "截图")
        self.assertError(self.shot(("", "/login")), "截图", "页面名")
        self.assertError(self.shot(*[("页面 %d" % i, "/p%d" % i) for i in range(9)]), "截图", "8")
        outside = GOOD.replace("## 阅读路线", "```screenshot 登录页\n/login\n```\n\n## 阅读路线")
        self.assertError(outside, "截图", "产出清单")

    def test_layer_count(self):
        self.assertError(GOOD.replace("### L3 记录\n\n见 [[spec/alpha.md:L1-L3]]。\n", ""), "分层讲改动", "3～7")

    def test_commit_outside_range(self):
        foreign = "0123abc4567"
        self.assertError(GOOD.replace("说明 [[src/a.py:L1]]。", "说明 %s。" % foreign), foreign)

    def test_commit_inside_range_is_fine(self):
        sha = json.load(open(self.facts_path, encoding="utf-8"))["commits"][1]["short"]
        code, errors, _ = self.check(GOOD.replace("说明 [[src/a.py:L1]]。", "说明 `%s` [[src/a.py:L1]]。" % sha))
        self.assertEqual((code, errors), (0, []))

    def test_unsupported_is_only_a_warning(self):
        code, errors, warnings = self.check(GOOD.replace("## 产出清单", "> 一句引用\n\n## 产出清单"))
        self.assertEqual((code, errors), (0, []))
        self.assertTrue(any("不支持" in w for w in warnings))

    def test_mermaid_without_title_is_warned(self):
        code, errors, warnings = self.check(GOOD.replace("### L2 计划", "```mermaid\nflowchart LR\n  A --> B\n```\n\n### L2 计划"))
        self.assertEqual((code, errors), (0, []))
        self.assertTrue(any("标题" in w for w in warnings))
        code, _errors, warnings = self.check(GOOD.replace("### L2 计划", "```mermaid 入口只调一个脚本\nflowchart LR\n  A --> B\n```\n\n### L2 计划"))
        self.assertEqual(warnings, [])

    def test_output_block_in_appendix_is_an_error(self):
        source = GOOD.replace("```output O1\n$ python3 src/a.py\na\n```\n\n", "")
        source = source.replace("（由脚本生成）", "（由脚本生成）\n\n```output O1\n$ python3 src/a.py\na\n```")
        self.assertError(source, "附录", "O1")

    def test_appendix_content_is_warned(self):
        code, _errors, warnings = self.check(GOOD.replace("（由脚本生成）", "| a | b |\n|---|---|\n| 1 | 2 |"))
        self.assertEqual(code, 0)
        self.assertTrue(any("附录" in w for w in warnings))

    def test_usage_error(self):
        proc = subprocess.run([sys.executable, "-B", str(CHECK), "--facts", self.facts_path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr.decode("utf-8"))


class RangeOnlyTest(CheckCase):
    def test_range_facts_need_no_ac_table(self):
        facts = json.load(open(self.facts_path, encoding="utf-8"))
        facts["module"] = None
        with open(self.facts_path, "w", encoding="utf-8") as handle:
            json.dump(facts, handle, ensure_ascii=False)
        source = GOOD.replace("| AC1 | [[src/a.py:L1]] |\n| AC2 | 实跑 [[out:O1]] |\n", "")
        source = source.replace("| AC | 证据 |\n|---|---|\n", "改动目的 [[src/a.py:L1]]。\n")
        code, errors, _ = self.check(source)
        self.assertEqual((code, errors), (0, []))


class BracketPathCheckTest(RepoCase):
    PATH = "src/app/[[...slug]]/page.tsx"

    def test_bracket_path_checked_at_end_commit(self):
        self.repo.write("README.md", "x\n")
        base = self.repo.commit("init")
        self.repo.write(self.PATH, "a\nb\nc\n")
        head = self.repo.commit("add page")
        facts_path = os.path.join(self.tmp.name, "facts.json")
        with open(facts_path, "w", encoding="utf-8") as handle:
            json.dump(self.facts("--range", "%s..%s" % (base, head), "--offline"), handle, ensure_ascii=False)
        self.facts_path = facts_path
        source = GOOD.replace("[[src/a.py]]", "[[`%s`:L2-L3]]" % self.PATH)
        source = source.replace("| AC1 | [[src/a.py:L1]] |", "| AC1 | x |")
        code, errors, _ = CheckCase.check(self, source)
        self.assertFalse([e for e in errors if self.PATH in e], errors)
        code, errors, _ = CheckCase.check(self, source.replace("L2-L3", "L2-L9"))
        self.assertTrue(any(self.PATH in e and "行号" in e for e in errors), errors)


MILESTONE_GOOD = """# M1 里程碑讲解

**一句话**：alpha 跑、beta 看。

## 这一站做成了什么

| 用法 | 证据 |
|---|---|
| U1 跑一次 | [[src/alpha/main.py:L1]] |
| U2 看结果 | [[src/beta/main.py:L1]] |

## 代码地图

新增都在 `src/` 下，一个模块一个目录。

## 沿典型用法走一遍

1. alpha 先跑 [[src/alpha/main.py:L1]]。
2. beta 读结果 [[src/beta/main.py:L1]]。
3. 回头看 alpha 的验收标准 [[spec/alpha.md:L1-L5]]。

## 跨模块约定

- 两个模块都只用 print 输出 [[src/alpha/main.py:L1]] [[src/beta/main.py:L1]]。

## 各模块讲解

（由脚本生成）

## 需要你判断的

- beta 只有一行 [[src/beta/main.py:L1]]。

## 附录

（由脚本生成）
"""


class MilestoneCheckCase(CheckCase):
    def setUp(self):
        RepoCase.setUp(self)
        import test_milestone
        test_milestone.MilestoneCase.build(self)
        self.facts_path = os.path.join(self.tmp.name, "facts.json")
        with open(self.facts_path, "w", encoding="utf-8") as handle:
            json.dump(self.facts("--milestone", "M1", "--offline"), handle, ensure_ascii=False)

    module = __import__("test_milestone").MilestoneCase.module
    parent = __import__("test_milestone").MilestoneCase.parent


class MilestoneCheckTest(MilestoneCheckCase):
    def test_good_milestone_page_passes(self):
        self.assertEqual(self.check(MILESTONE_GOOD), (0, [], []))

    def test_sections(self):
        self.assertError(MILESTONE_GOOD.replace("## 跨模块约定", "## 别的"), "缺少「跨模块约定」")
        swapped = MILESTONE_GOOD.replace("## 代码地图", "## TMP").replace("## 沿典型用法走一遍", "## 代码地图").replace("## TMP", "## 沿典型用法走一遍")
        self.assertError(swapped, "顺序")

    def test_usage_table(self):
        self.assertError(MILESTONE_GOOD.replace("| U2 看结果 | [[src/beta/main.py:L1]] |\n", ""), "这一站做成了什么", "U2")
        self.assertError(MILESTONE_GOOD.replace("| U2 看结果 | [[src/beta/main.py:L1]] |", "| U2 看结果 | 看了 |"), "U2", "证据")
        self.assertError(MILESTONE_GOOD.split("| 用法")[0] + "## 代码地图" + MILESTONE_GOOD.split("## 代码地图")[1], "这一站做成了什么")

    def test_walk(self):
        two = MILESTONE_GOOD.replace("3. 回头看 alpha 的验收标准 [[spec/alpha.md:L1-L5]]。\n", "")
        self.assertError(two, "沿典型用法走一遍", "3～10")
        eleven = MILESTONE_GOOD.replace("3. 回头看", "".join("%d. alpha 第 %d 步 [[src/alpha/main.py:L1]]。\n" % (i, i) for i in range(3, 11)) + "11. 回头看")
        self.assertError(eleven, "沿典型用法走一遍", "3～10")
        self.assertError(MILESTONE_GOOD.replace("2. beta 读结果 [[src/beta/main.py:L1]]。", "2. beta 读结果。"), "沿典型用法走一遍 第 2 步", "引用")
        self.assertError(MILESTONE_GOOD.replace("2. beta 读结果", "2. 读结果"), "沿典型用法走一遍 第 2 步", "模块")
        self.assertError(MILESTONE_GOOD.replace("1. alpha 先跑", "- alpha 先跑"), "沿典型用法走一遍", "有序列表")

    def test_conventions(self):
        one = MILESTONE_GOOD.replace(" [[src/beta/main.py:L1]]。\n\n## 各模块", "。\n\n## 各模块")
        self.assertError(one, "跨模块约定 第 1 条", "两个")
        same = MILESTONE_GOOD.replace("[[src/alpha/main.py:L1]] [[src/beta/main.py:L1]]", "[[src/alpha/main.py:L1]] [[src/alpha/main.py]]")
        self.assertError(same, "跨模块约定 第 1 条", "两个")
        none = MILESTONE_GOOD.replace("- 两个模块都只用 print 输出 [[src/alpha/main.py:L1]] [[src/beta/main.py:L1]]。", "没有新约定。")
        self.assertEqual(self.check(none), (0, [], []))

    def test_generated_sections_warn_on_tables(self):
        code, errors, warnings = self.check(MILESTONE_GOOD.replace("## 各模块讲解\n\n（由脚本生成）", "## 各模块讲解\n\n- alpha\n- beta"))
        self.assertEqual((code, errors), (0, []))
        self.assertTrue(any("各模块讲解" in w for w in warnings), warnings)

    def test_module_commit_ids_allowed(self):
        source = MILESTONE_GOOD.replace("beta 只有一行", "beta 的起点是 %s，只有一行" % self.beta[0][:8])
        self.assertEqual(self.check(source), (0, [], []))
