"""spec-guard file parsing: capability map, Spec marker and ACs, todo items, usage drafts (AC4)."""
import unittest

import fixtures  # noqa: F401  (puts scripts/ on sys.path)
import facts_specguard as sg

MAP = """# Capability Map: demo

## 目标

Demo.

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| alpha | 做 A，含 `代码` 与｜竖线 | — |
| beta | 做 B | alpha |
| gamma | 做 C | alpha, beta |

Build order: alpha → beta → gamma
"""

SPEC = """# Spec: beta

<!-- spec-guard: review approved 0123456789ab -->

## 成功标准

- AC1：第一条，
  续行也算这条。
- **AC2**: 第二条
- 不是 AC 的行
- AC10：第十条

```text
- AC9：围栏里的示例不算
```
"""

TODO = """# Todo: beta

- [x] Task 0：提交 Plan
- [ ] Task 1：实现 — 进行中
- [X] Checkpoint 1（report）：完整检查
- [ ] 延期：等外部接口；恢复条件：对方发版
- [x] Checkpoint 2（gate）：最终验收
- [ ] 发版（合并后按 Checkpoint 2 授权）
  - [ ] 子项不算
"""

USAGE = """# Usage draft: demo

## Entry points

| Entry | Does | Module |
|---|---|---|
| `/demo run` | 跑一次 | alpha |
| `/demo show` | 展示 | beta, gamma |

## Typical usage

### U1: 跑
x

### U2: 看
y

## Milestones

| Milestone | Usage | Modules |
|---|---|---|
| M1 | U1 | alpha |
| M2 | U1, U2 | beta、gamma |
"""


class MapTest(unittest.TestCase):
    def test_rows_and_build_order(self):
        parsed = sg.parse_map(MAP)
        self.assertEqual(parsed["modules"]["beta"], {"responsibility": "做 B", "dependsOn": ["alpha"]})
        self.assertEqual(parsed["modules"]["alpha"]["dependsOn"], [])
        self.assertEqual(parsed["modules"]["gamma"]["dependsOn"], ["alpha", "beta"])
        self.assertIn("`代码`", parsed["modules"]["alpha"]["responsibility"])
        self.assertEqual(parsed["buildOrder"], ["alpha", "beta", "gamma"])

    def test_no_table(self):
        self.assertEqual(sg.parse_map("# nothing\n")["modules"], {})


class SpecTest(unittest.TestCase):
    def test_marker_and_acs(self):
        facts = sg.parse_spec(SPEC)
        self.assertEqual(facts["marker"], "approved 0123456789ab")
        ids = [ac["id"] for ac in facts["acs"]]
        self.assertEqual(ids, ["AC1", "AC2", "AC10"])
        self.assertEqual(facts["acs"][0]["text"], "第一条，续行也算这条。")
        self.assertEqual(facts["acs"][1]["text"], "第二条")

    def test_ac_with_parenthetical_note(self):
        text = ("## 成功标准\n\n- AC9（2026-11-19 修订）：修订加的一条\n- **AC3**（补）: 半角冒号\n"
                "- AC4 (note): 半角括号\n- AC5（没有冒号的行不算）\n")
        acs = sg.parse_spec(text)["acs"]
        self.assertEqual([ac["id"] for ac in acs], ["AC9", "AC3", "AC4"])
        self.assertEqual([ac["text"] for ac in acs], ["修订加的一条", "半角冒号", "半角括号"])

    def test_continuation_stops_at_blank_line_and_section(self):
        text = "## 成功标准\n\n- AC1：最后一条\n\n## 文档建议\n\n- 本模块的文档：术语表\n  加一句。\n"
        self.assertEqual(sg.parse_spec(text)["acs"], [{"id": "AC1", "text": "最后一条"}])

    def test_unnumbered_success_criteria(self):
        facts = sg.parse_spec("# S\n\n## 成功标准\n\n- 第一条\n  续行\n- 第二条\n\n## 待定问题\n\n- 无。\n")
        self.assertFalse(facts["numbered"])
        self.assertEqual(facts["acs"], [{"id": None, "text": "第一条续行"}, {"id": None, "text": "第二条"}])
        self.assertTrue(sg.parse_spec(SPEC)["numbered"])

    def test_pending_and_missing_marker(self):
        self.assertEqual(sg.parse_spec("# S\n\n<!-- spec-guard: review pending -->\n")["marker"], "pending")
        self.assertIsNone(sg.parse_spec("# S\n")["marker"])


class TodoTest(unittest.TestCase):
    def test_items_and_kinds(self):
        items = sg.parse_todo(TODO)
        self.assertEqual(len(items), 6)
        self.assertEqual([i["checked"] for i in items], [True, False, True, False, True, False])
        self.assertEqual([i["kind"] for i in items], ["task", "task", "report", "task", "gate", "task"])
        self.assertTrue(items[3]["deferred"])
        self.assertFalse(items[0]["deferred"])
        self.assertTrue(items[4]["text"].startswith("Checkpoint 2（gate）"))

    def test_halfwidth_parentheses(self):
        items = sg.parse_todo("- [x] Checkpoint (gate): done\n- [ ] CP (report)\n")
        self.assertEqual([i["kind"] for i in items], ["gate", "report"])


class UsageTest(unittest.TestCase):
    def test_module_in_milestone_with_entries(self):
        found = sg.usage_for_module({"spec/usage/demo.md": USAGE}, "beta")
        self.assertEqual(found["file"], "spec/usage/demo.md")
        self.assertEqual(found["milestone"], "M2")
        self.assertEqual(found["usages"], ["U1", "U2"])
        self.assertEqual(found["entries"], [{"entry": "/demo show", "does": "展示"}])

    def test_entry_with_code_and_text_keeps_backticks(self):
        draft = USAGE.replace("| `/demo show` | 展示 | beta, gamma |", "| `/demo show` 预览 | 展示 | beta, gamma |")
        found = sg.usage_for_module({"spec/usage/demo.md": draft}, "beta")
        self.assertEqual(found["entries"][0]["entry"], "`/demo show` 预览")

    def test_module_not_in_any_draft(self):
        self.assertIsNone(sg.usage_for_module({"spec/usage/demo.md": USAGE}, "delta"))

    def test_broken_draft_reports_warning(self):
        warnings = []
        found = sg.usage_for_module({"spec/usage/bad.md": "# Usage draft\n\nno tables\n"}, "beta", warnings)
        self.assertIsNone(found)
        self.assertEqual(len(warnings), 1)
        self.assertIn("spec/usage/bad.md", warnings[0])


class MilestoneRowTest(unittest.TestCase):
    def test_row_with_usage_titles_and_modules(self):
        row = sg.milestone_row(USAGE, "M2")
        self.assertEqual(row["milestone"], "M2")
        self.assertEqual(row["usages"], [{"id": "U1", "title": "跑"}, {"id": "U2", "title": "看"}])
        self.assertEqual(row["modules"], ["beta", "gamma"])
        self.assertFalse(row["confirmed"])

    def test_confirmed_line(self):
        draft = USAGE + "\n<!-- spec-guard: milestone M2 confirmed beta, gamma -->\n"
        self.assertTrue(sg.milestone_row(draft, "M2")["confirmed"])
        self.assertFalse(sg.milestone_row(draft, "M1")["confirmed"])

    def test_missing_milestone_or_table(self):
        self.assertIsNone(sg.milestone_row(USAGE, "M9"))
        self.assertIsNone(sg.milestone_row("# Usage draft\n\nno tables\n", "M1"))


if __name__ == "__main__":
    unittest.main()
