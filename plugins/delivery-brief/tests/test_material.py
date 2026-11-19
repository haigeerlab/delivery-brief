"""crosscheck_material.py: review material for delegate, from the end commit, within the size limit (AC2)."""
import os
import re
import subprocess
import sys

from fixtures import GIT_ENV, SCRIPTS
from test_check import GOOD, CheckCase

MATERIAL = SCRIPTS / "crosscheck_material.py"


class MaterialTest(CheckCase):
    def make(self, *extra, check_readonly=True):
        self.src = os.path.join(self.tmp.name, "brief.md")
        with open(self.src, "w", encoding="utf-8") as handle:
            handle.write(GOOD)
        self.out = os.path.join(self.tmp.name, ".crosscheck-alpha")
        before = self.repo.snapshot()
        proc = subprocess.run([sys.executable, "-B", str(MATERIAL), "--facts", self.facts_path, "--source", self.src,
                               "--out", self.out, *extra], env=dict(os.environ, **GIT_ENV),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check_readonly:
            self.assertEqual(before, self.repo.snapshot())
        self.assertNotIn("Traceback", proc.stderr.decode("utf-8"))
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def read(self, path):
        with open(os.path.join(self.out, path), encoding="utf-8") as handle:
            return handle.read()

    def test_layout_and_end_commit_versions(self):
        self.repo.write("src/a.py", "工作区里的改动\n")
        code, out, err = self.make()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("source/src/a.py"), "print('a')\n")
        self.assertEqual(self.read("brief.md"), GOOD)
        for path in ("facts.json", "range.diff", "MATERIAL.md", "source/spec/alpha.md", "source/tasks/alpha/plan.md",
                     "source/tasks/alpha/todo.md"):
            self.assertTrue(os.path.exists(os.path.join(self.out, path)), path)
        material = self.read("MATERIAL.md")
        for path in ("brief.md", "facts.json", "range.diff", "source/src/a.py"):
            self.assertIn(path, material)
        self.assertIn("bytes", out)

    def test_range_diff_matches_git(self):
        self.make()
        import json
        facts = json.load(open(self.facts_path, encoding="utf-8"))
        expected = self.repo.git("diff", "-M", facts["range"]["base"], facts["range"]["head"])
        self.assertEqual(self.read("range.diff"), expected)

    def test_material_is_a_clean_single_commit_repo(self):
        self.make()
        run = lambda *a: subprocess.run(["git", *a], cwd=self.out, stdout=subprocess.PIPE).stdout.decode()
        self.assertEqual(run("rev-list", "--count", "HEAD").strip(), "1")
        self.assertEqual(run("status", "--porcelain"), "")

    def test_rebuild_removes_stale_files(self):
        self.make()
        with open(os.path.join(self.out, "stale.txt"), "w") as handle:
            handle.write("x")
        self.make()
        self.assertFalse(os.path.exists(os.path.join(self.out, "stale.txt")))

    def test_over_limit_windows_the_largest_cited_file(self):
        big = "".join("line %d\n" % i for i in range(1, 2001))
        self.repo.write("tasks/alpha/plan.md", big)
        self.repo.commit("bigger plan")
        self.facts_path = os.path.join(self.tmp.name, "facts2.json")
        with open(self.facts_path, "w", encoding="utf-8") as handle:
            import json
            json.dump(self.facts("--range", "%s..HEAD" % self.repo.git("rev-list", "--max-parents=0", "HEAD").strip(),
                                 "--offline"), handle, ensure_ascii=False)
        code, out, _ = self.make()
        total = int(re.search(r"bytes (\d+)", out).group(1))
        code, out, err = self.make("--limit", str(total - 1000))
        self.assertEqual(code, 0, err)
        windowed = self.read("source/tasks/alpha/plan.md")
        self.assertLess(len(windowed), len(big))
        self.assertIn("截取", self.read("MATERIAL.md"))
        self.assertIn("tasks/alpha/plan.md", self.read("MATERIAL.md"))
        self.assertIn("1: line 1", windowed)

    def test_still_over_limit_exits_3(self):
        code, _out, err = self.make("--limit", "100")
        self.assertEqual(code, 3, err)
        self.assertIn("range.diff", err)
        self.assertEqual(len(err.strip().splitlines()) >= 1, True)

    def test_usage_error(self):
        proc = subprocess.run([sys.executable, "-B", str(MATERIAL), "--facts", self.facts_path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr.decode("utf-8"))
