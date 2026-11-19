"""--module: range inference from spec-guard's files, module facts, warnings, errors (AC2, AC3, AC4, AC8)."""
import unittest

from fixtures import RepoCase

MAP = """# Capability Map: demo

## 目标

Demo.

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| alpha | 做 A | — |
| beta | 做 B | alpha |
| gamma | 做 C | alpha |

Build order: alpha → beta → gamma
"""

SPEC = """# Spec: alpha

<!-- spec-guard: review approved 0123456789ab -->

## 成功标准

- AC1：第一条
- AC2：第二条
"""

USAGE = """# Usage draft: demo

## Entry points

| Entry | Does | Module |
|---|---|---|
| `/demo` | 跑 | alpha |

## Typical usage

### U1: 跑
x

## Milestones

| Milestone | Usage | Modules |
|---|---|---|
| M1 | U1 | alpha, beta, gamma |
"""


def todo(*items):
    return "# Todo\n\n" + "".join("- [%s] %s\n" % ("x" if done else " ", text) for done, text in items)


class ModuleRangeTest(RepoCase):
    def base_repo(self):
        r = self.repo
        r.write("spec/CAPABILITY-MAP.md", MAP)
        r.write("spec/usage/demo.md", USAGE)
        r.write("README.md", "demo\n")
        return r.commit("init")

    def finished_alpha(self):
        """alpha: approved, built, final gate ticked, then a release commit that also touches its todo."""
        r = self.repo
        self.base_repo()
        steps = [(False, "Task 1：实现"), (False, "Checkpoint 1（report）：检查"),
                 (False, "Checkpoint 2（gate）：最终验收"), (False, "发版：打 tag")]
        r.write("spec/alpha.md", SPEC)
        r.write("tasks/alpha/plan.md", "# Plan\n")
        r.write("tasks/alpha/todo.md", todo(*steps))
        self.start = r.commit("docs: alpha Spec 与 Plan")
        r.write("src/a.py", "print('a')\n")
        steps[0] = (True, steps[0][1])
        r.write("tasks/alpha/todo.md", todo(*steps))
        r.commit("feat: alpha 实现")
        steps[1] = (True, steps[1][1] + " — 通过")
        r.write("tasks/alpha/todo.md", todo(*steps))
        r.commit("docs: alpha 检查记录")
        steps[2] = (True, steps[2][1] + " — 用户验收通过")
        r.write("tasks/alpha/todo.md", todo(*steps))
        self.end = r.commit("docs: alpha 最终验收通过")
        steps[3] = (True, steps[3][1])
        r.write("tasks/alpha/todo.md", todo(*steps))
        r.write("docs/releases/v1.json", "{}\n")
        self.release = r.commit("docs: 发版证据")

    def test_finished_module_ends_at_last_ticked_gate(self):
        self.finished_alpha()
        facts = self.facts("--module", "alpha", "--offline")
        rng = facts["range"]
        self.assertEqual(rng["source"], "inferred-spec-guard")
        self.assertEqual(rng["head"], self.end)
        self.assertEqual(rng["base"], self.repo.git("rev-parse", self.start + "^").strip())
        self.assertFalse(rng["inProgress"])
        self.assertEqual(rng["basis"]["start"]["sha"], self.start)
        self.assertEqual(rng["basis"]["end"]["sha"], self.end)
        self.assertIn("Checkpoint 2（gate）", rng["basis"]["end"]["gate"])
        shas = [c["sha"] for c in facts["commits"]]
        self.assertEqual(len(shas), 4)
        self.assertNotIn(self.release, shas)
        self.assertNotIn("docs/releases/v1.json", [f["path"] for f in facts["files"]])

    def test_module_facts(self):
        self.finished_alpha()
        module = self.facts("--module", "alpha", "--offline")["module"]
        self.assertEqual(module["id"], "alpha")
        self.assertEqual(module["responsibility"], "做 A")
        self.assertEqual(module["dependsOn"], [])
        self.assertEqual(module["spec"]["path"], "spec/alpha.md")
        self.assertEqual(module["spec"]["marker"], "approved 0123456789ab")
        self.assertEqual([ac["id"] for ac in module["spec"]["acs"]], ["AC1", "AC2"])
        at_end = module["todo"]["atEnd"]
        at_head = module["todo"]["atHead"]
        self.assertFalse(at_end[3]["checked"])
        self.assertTrue(at_head[3]["checked"])
        self.assertEqual(at_end[2]["kind"], "gate")

    def test_usage_draft(self):
        self.finished_alpha()
        usage = self.facts("--module", "alpha", "--offline")["usageDraft"]
        self.assertEqual(usage["file"], "spec/usage/demo.md")
        self.assertEqual(usage["milestone"], "M1")
        self.assertEqual(usage["entries"], [{"entry": "/demo", "does": "跑"}])

    def test_in_progress_without_gate(self):
        r = self.repo
        self.base_repo()
        r.write("spec/beta.md", "# Spec: beta\n")
        first = r.commit("docs: beta Spec")
        r.write("tasks/beta/todo.md", todo((True, "Task 1"), (False, "Checkpoint 1（gate）：验收")))
        r.write("src/b.py", "b\n")
        last = r.commit("feat: beta 一半")
        r.write("README.md", "unrelated\n")
        r.commit("docs: 无关提交")
        facts = self.facts("--module", "beta", "--offline")
        self.assertTrue(facts["range"]["inProgress"])
        self.assertEqual(facts["range"]["head"], last)
        self.assertEqual([c["sha"] for c in facts["commits"]], [first, last])
        self.assertIsNone(facts["range"]["basis"]["end"]["gate"])

    def test_open_items_after_gate_are_reported(self):
        """A middle gate is ticked and work goes on: the later module commits are named, not silently dropped."""
        r = self.repo
        self.base_repo()
        steps = [(True, "Task 1"), (False, "Checkpoint 1（gate）：中途确认"), (False, "Task 2"),
                 (False, "Checkpoint 2（gate）：最终验收")]
        r.write("spec/gamma.md", "# Spec: gamma\n")
        r.write("tasks/gamma/todo.md", todo(*steps))
        r.commit("docs: gamma")
        steps[1] = (True, steps[1][1])
        r.write("tasks/gamma/todo.md", todo(*steps))
        mid = r.commit("docs: gamma 中途 gate")
        steps[2] = (True, steps[2][1])
        r.write("tasks/gamma/todo.md", todo(*steps))
        r.write("src/c.py", "c\n")
        later = r.commit("feat: gamma Task 2")
        facts = self.facts("--module", "gamma", "--offline")
        self.assertEqual(facts["range"]["head"], mid)
        basis = facts["range"]["basis"]
        self.assertEqual(basis["laterModuleCommits"], [later])
        self.assertEqual([i["text"] for i in basis["openItemsAtHead"]], ["Checkpoint 2（gate）：最终验收"])
        self.assertTrue(any(later[:8] in w for w in facts["warnings"]))

    def test_commit_touching_other_module_is_warned(self):
        self.finished_alpha()
        r = self.repo
        r.git("reset", "-q", "--hard", self.start)
        r.write("tasks/beta/todo.md", todo((False, "Task 1")))
        r.write("tasks/alpha/todo.md", todo((True, "Task 1：实现"), (True, "Checkpoint 2（gate）：最终验收")))
        mixed = r.commit("docs: 混入 beta 的改动")
        facts = self.facts("--module", "alpha", "--offline")
        self.assertEqual(facts["range"]["head"], mixed)
        self.assertTrue(any(mixed[:8] in w and "beta" in w for w in facts["warnings"]))

    def test_merge_commits_are_skipped(self):
        r = self.repo
        self.base_repo()
        r.git("checkout", "-q", "-b", "work")
        r.write("spec/alpha.md", SPEC)
        r.write("tasks/alpha/todo.md", todo((False, "Checkpoint 1（gate）：验收")))
        start = r.commit("docs: alpha")
        r.git("checkout", "-q", "main")
        r.write("other.txt", "o\n")
        r.commit("main 上的改动")
        r.git("checkout", "-q", "work")
        r.git("merge", "-q", "--no-ff", "-m", "merge main", "main")
        r.write("tasks/alpha/todo.md", todo((True, "Checkpoint 1（gate）：验收")))
        end = r.commit("docs: alpha 验收")
        facts = self.facts("--module", "alpha", "--offline")
        subjects = [c["subject"] for c in facts["commits"]]
        self.assertNotIn("merge main", subjects)
        self.assertEqual(facts["range"]["basis"]["start"]["sha"], start)
        self.assertEqual(facts["range"]["head"], end)

    def test_errors(self):
        self.base_repo()
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--module", "nope", "--offline")
        self.assertOneLineError(code, 3, err)
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--module", "beta", "--offline")
        self.assertOneLineError(code, 3, err)
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--module", "Bad_ID", "--offline")
        self.assertOneLineError(code, 2, err)

    def test_no_capability_map(self):
        self.repo.write("x.txt", "x\n")
        self.repo.commit("init")
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--module", "alpha", "--offline")
        self.assertOneLineError(code, 3, err)
        self.assertIn("--range", err)


if __name__ == "__main__":
    unittest.main()
