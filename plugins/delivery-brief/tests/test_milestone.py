"""--milestone: range = union of the milestone's module ranges, milestone facts, code map, errors (AC1)."""
import unittest

from fixtures import RepoCase

MAP = """# Capability Map: demo

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| alpha | 做 A | — |
| beta | 做 B | alpha |
| gamma | 做 C | beta |

Build order: alpha → beta → gamma
"""

USAGE = """# Usage draft: demo

## Entry points

| Entry | Does | Module |
|---|---|---|
| `/demo run` | 跑 | alpha |
| `/demo show` | 看 | beta |
| `/demo more` | 多 | gamma |

## Typical usage

### U1: 跑一次
x

### U2: 看结果
y

## Milestones

| Milestone | Usage | Modules |
|---|---|---|
| M1 | U1, U2 | alpha, beta |
| M2 | U1, U2 | gamma |
"""


def todo(done):
    return "# Todo\n\n- [x] Task 1：实现\n- [%s] Checkpoint 1（gate）：最终验收\n" % ("x" if done else " ")


class MilestoneCase(RepoCase):
    def module(self, name, finish=True):
        """Spec + plan + todo commit (start), a code commit, then the gate commit (end) when finish."""
        r = self.repo
        r.write("spec/%s.md" % name, "# Spec: %s\n\n## 成功标准\n\n- AC1：可以\n" % name)
        r.write("tasks/%s/plan.md" % name, "# Plan\n")
        r.write("tasks/%s/todo.md" % name, todo(False))
        start = r.commit("docs: %s Spec" % name)
        r.write("src/%s/main.py" % name, "print('%s')\n" % name)
        end = r.commit("feat: %s" % name)
        if finish:
            r.write("tasks/%s/todo.md" % name, todo(True))
            end = r.commit("docs: %s 验收" % name)
        return start, end

    def build(self, gamma_done=False):
        r = self.repo
        r.write("spec/CAPABILITY-MAP.md", MAP)
        r.write("spec/usage/demo.md", USAGE)
        r.write("README.md", "demo\n")
        r.write("old/keep.txt", "keep\n")
        r.write("old/change.txt", "v1\n")
        r.write("old/gone.txt", "bye\n")
        r.commit("init")
        self.alpha = self.module("alpha")
        r.write("old/change.txt", "v2\n")
        r.remove("old/gone.txt")
        r.commit("chore: 顺手改两个旧文件")
        self.beta = self.module("beta")
        self.gamma = self.module("gamma", finish=gamma_done)

    def parent(self, sha):
        return self.repo.git("rev-parse", sha + "^").strip()


class MilestoneRangeTest(MilestoneCase):
    def test_range_is_union_of_module_ranges(self):
        self.build()
        facts = self.facts("--milestone", "M1", "--offline")
        rng = facts["range"]
        self.assertEqual(rng["base"], self.parent(self.alpha[0]))
        self.assertEqual(rng["head"], self.beta[1])
        self.assertEqual(rng["source"], "inferred-spec-guard-milestone")
        self.assertFalse(rng["inProgress"])
        self.assertIsNone(rng["basis"])
        self.assertIsNone(facts["module"])
        self.assertIsNone(facts["usageDraft"])
        subjects = [c["subject"] for c in facts["commits"]]
        self.assertEqual(subjects[0], "docs: alpha Spec")
        self.assertEqual(subjects[-1], "docs: beta 验收")
        self.assertNotIn("docs: gamma Spec", subjects)

    def test_milestone_facts(self):
        self.build()
        milestone = self.facts("--milestone", "M1", "--offline")["milestone"]
        self.assertEqual(milestone["id"], "M1")
        self.assertEqual(milestone["draft"], "spec/usage/demo.md")
        self.assertEqual(milestone["usages"], [{"id": "U1", "title": "跑一次"}, {"id": "U2", "title": "看结果"}])
        self.assertFalse(milestone["confirmed"])
        self.assertEqual([m["id"] for m in milestone["modules"]], ["alpha", "beta"])
        alpha = milestone["modules"][0]
        self.assertEqual(alpha["responsibility"], "做 A")
        self.assertEqual(alpha["status"], "done")
        self.assertEqual(alpha["range"]["head"], self.alpha[1])
        self.assertEqual(alpha["range"]["basis"]["start"]["sha"], self.alpha[0])

    def test_unconfirmed_and_confirmed(self):
        self.build()
        facts = self.facts("--milestone", "M1", "--offline")
        self.assertTrue(any("M1" in w and "还没确认" in w for w in facts["warnings"]), facts["warnings"])
        self.repo.write("spec/usage/demo.md", USAGE + "\n<!-- spec-guard: milestone M1 confirmed alpha, beta -->\n")
        self.repo.commit("docs: M1 确认")
        facts = self.facts("--milestone", "M1", "--offline")
        self.assertTrue(facts["milestone"]["confirmed"])
        self.assertFalse(any("还没确认" in w for w in facts["warnings"]), facts["warnings"])

    def test_module_in_progress(self):
        self.build()
        facts = self.facts("--milestone", "M2", "--offline")
        self.assertTrue(facts["range"]["inProgress"])
        self.assertEqual(facts["milestone"]["modules"][0]["status"], "inProgress")
        self.assertTrue(any(w.startswith("模块 gamma：") for w in facts["warnings"]), facts["warnings"])

    def test_module_without_commits_is_missing(self):
        self.build()
        self.repo.write("spec/usage/demo.md", USAGE.replace("| M2 | U1, U2 | gamma |", "| M2 | U1, U2 | gamma, delta |"))
        self.repo.commit("docs: 草案加 delta")
        facts = self.facts("--milestone", "M2", "--offline")
        delta = facts["milestone"]["modules"][1]
        self.assertEqual((delta["id"], delta["status"], delta["range"]), ("delta", "missing", None))
        self.assertTrue(any(w.startswith("模块 delta：") for w in facts["warnings"]), facts["warnings"])


class CodeMapTest(MilestoneCase):
    def test_code_map_counts(self):
        self.build()
        groups = {g["path"]: g for g in self.facts("--milestone", "M1", "--offline")["codeMap"]}
        def counts(path):
            g = groups[path]
            return (g["added"], g["modified"], g["unchanged"], g["deleted"])
        self.assertEqual(counts("."), (0, 0, 1, 0))
        self.assertEqual(counts("old"), (0, 1, 1, 1))
        self.assertEqual(counts("src/alpha"), (1, 0, 0, 0))
        self.assertEqual(counts("src/beta"), (1, 0, 0, 0))
        self.assertEqual(counts("spec"), (2, 0, 1, 0))
        self.assertEqual(counts("spec/usage"), (0, 0, 1, 0))
        self.assertEqual(counts("tasks/alpha"), (2, 0, 0, 0))
        self.assertNotIn("src/gamma", groups)
        self.assertEqual(list(groups), sorted(groups))

    def test_module_facts_have_no_milestone_fields(self):
        self.build()
        facts = self.facts("--module", "alpha", "--offline")
        self.assertNotIn("codeMap", facts)
        self.assertNotIn("milestone", facts)


class MilestoneErrorTest(MilestoneCase):
    def test_bad_milestone_id(self):
        self.build()
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--milestone", "m1", "--offline")
        self.assertOneLineError(code, 2, err)

    def test_draft_only_with_milestone(self):
        self.build()
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--module", "alpha", "--draft",
                                       "spec/usage/demo.md", "--offline")
        self.assertOneLineError(code, 2, err)

    def test_unknown_milestone_or_draft(self):
        self.build()
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--milestone", "M9", "--offline")
        self.assertOneLineError(code, 3, err)
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--milestone", "M1", "--draft",
                                       "spec/usage/nope.md", "--offline")
        self.assertOneLineError(code, 3, err)

    def test_several_drafts_need_draft_option(self):
        self.build()
        self.repo.write("spec/usage/other.md", USAGE)
        self.repo.commit("docs: 第二份草案")
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--milestone", "M1", "--offline")
        self.assertOneLineError(code, 2, err)
        self.assertIn("spec/usage/other.md", err)
        facts = self.facts("--milestone", "M1", "--draft", "spec/usage/other.md", "--offline")
        self.assertEqual(facts["milestone"]["draft"], "spec/usage/other.md")

    def test_no_capability_map(self):
        self.repo.write("a.txt", "a\n")
        self.repo.commit("init")
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--milestone", "M1", "--offline")
        self.assertOneLineError(code, 3, err)


if __name__ == "__main__":
    unittest.main()
