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

    def test_route_must_be_ordered_with_citations(self):
        self.assertError(GOOD.replace("1. [[spec/alpha.md]]", "- [[spec/alpha.md]]"), "阅读路线")
        self.assertError(GOOD.replace("2. [[src/a.py:L1]]：再看实现。", "2. 再看实现。"), "阅读路线", "第 2 条")
        self.assertError(GOOD.replace("3. [[tasks/alpha/todo.md]]：最后看 todo。\n", ""), "阅读路线", "3～7")

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
