"""Explicit --range: commits, per-file numstat, size, exit codes, read-only (AC1, AC6, AC7, AC8)."""
import json
import os
import subprocess
import unittest

from fixtures import RepoCase, GIT_ENV


class RangeTest(RepoCase):
    def build(self):
        r = self.repo
        r.write("a.txt", "one\ntwo\n")
        r.write("old name.txt", "keep\nthis\ncontent\nstable\n")
        self.base = r.commit("init")
        r.write("a.txt", "one\nTWO\nthree\n")
        r.write("目录/中文.md", "你好\n")
        c1 = r.commit("feat: 改 a 并加中文文件")
        r.git("mv", "old name.txt", "new name.txt")
        r.write("img.bin", b"\x00\x01\x02binary\x00")
        c2 = r.commit("chore: 重命名并加二进制")
        r.git("checkout", "-q", "-b", "side", c1)
        r.write("side.txt", "s\n")
        r.commit("side")
        r.git("checkout", "-q", "main")
        r.git("merge", "-q", "--no-ff", "-m", "merge side", "side")
        r.remove("a.txt")
        self.head = r.commit("remove a")
        return c1, c2

    def test_commits_match_git(self):
        self.build()
        facts = self.facts("--range", "%s..%s" % (self.base, self.head), "--offline")
        expected = self.repo.git("rev-list", "--no-merges", "--reverse", "%s..%s" % (self.base, self.head)).split()
        self.assertEqual([c["sha"] for c in facts["commits"]], expected)
        self.assertEqual(facts["range"]["source"], "explicit")
        self.assertEqual(facts["range"]["base"], self.base)
        self.assertEqual(facts["range"]["head"], self.head)
        first = facts["commits"][0]
        self.assertEqual(first["subject"], "feat: 改 a 并加中文文件")
        self.assertIn("目录/中文.md", first["files"])
        self.assertTrue(first["date"])
        self.assertEqual(first["short"], first["sha"][:8])

    def test_numstat_matches_git(self):
        self.build()
        facts = self.facts("--range", "%s..%s" % (self.base, self.head), "--offline")
        by_path = {f["path"]: f for f in facts["files"]}
        self.assertEqual(by_path["目录/中文.md"]["status"], "A")
        self.assertEqual(by_path["目录/中文.md"]["added"], 1)
        self.assertEqual(by_path["a.txt"]["status"], "D")
        self.assertEqual(by_path["a.txt"]["deleted"], 2)
        renamed = by_path["new name.txt"]
        self.assertEqual(renamed["status"], "R")
        self.assertEqual(renamed["oldPath"], "old name.txt")
        self.assertTrue(by_path["img.bin"]["binary"])
        self.assertIsNone(by_path["img.bin"]["added"])
        self.assertIn("side.txt", by_path)
        shortstat = self.repo.git("diff", "--shortstat", "-M", self.base, self.head)
        totals = facts["totals"]
        self.assertIn("%d files changed" % totals["files"], shortstat)
        self.assertIn("%d insertion" % totals["added"], shortstat)
        self.assertIn("%d deletion" % totals["deleted"], shortstat)

    def test_size(self):
        self.build()
        size = self.facts("--range", "%s..%s" % (self.base, self.head), "--offline")["size"]
        self.assertGreater(size["diffBytes"], 0)
        self.assertGreater(size["changedFileBytes"], 0)
        self.assertEqual(size["estimatedTokens"], (size["diffBytes"] + size["changedFileBytes"]) // 4)
        self.assertEqual(size["files"], 5)

    def test_schema_header(self):
        self.build()
        facts = self.facts("--range", "%s..%s" % (self.base, self.head), "--offline")
        self.assertEqual(facts["schemaVersion"], 1)
        self.assertEqual(facts["project"]["name"], "proj")
        self.assertEqual(facts["project"]["head"], self.head)
        self.assertIsNone(facts["module"])
        self.assertIsInstance(facts["warnings"], list)

    def test_usage_errors(self):
        self.build()
        code, _out, err = self.run_cli("--project", str(self.repo.root))
        self.assertOneLineError(code, 2, err)
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--range", "abc")
        self.assertOneLineError(code, 2, err)
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--range", "a..b", "--module", "x")
        self.assertOneLineError(code, 2, err)

    def test_unknown_revision_is_range_error(self):
        self.build()
        code, _out, err = self.run_cli("--project", str(self.repo.root), "--range", "nope..HEAD", "--offline")
        self.assertOneLineError(code, 3, err)

    def test_not_a_repository(self):
        plain = os.path.join(self.tmp.name, "plain")
        os.mkdir(plain)
        with open(os.path.join(plain, "keep.txt"), "w") as handle:
            handle.write("x\n")
        code, _out, err = self.run_cli("--project", plain, "--range", "a..b", "--offline", plain_dir=plain)
        self.assertOneLineError(code, 4, err)

    def test_non_utf8_path_is_a_warning_not_a_traceback(self):
        r = self.repo
        r.write("a.txt", "a\n")
        base = r.commit("init")
        blob = r.git("hash-object", "-w", "a.txt").strip()
        subprocess.run(["git", "update-index", "--add", "--cacheinfo", b"100644," + blob.encode() + b",bad\xff.txt"],
                       cwd=str(r.root), check=True, env=dict(os.environ, **GIT_ENV))
        r.git("commit", "-q", "-m", "add non-utf8 path")
        head = r.git("rev-parse", "HEAD").strip()
        code, out, err = self.run_cli("--project", str(r.root), "--range", "%s..%s" % (base, head), "--offline")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", err)
        facts = json.loads(out)
        self.assertEqual(facts["totals"]["files"], 1)
        self.assertTrue(any("不是 UTF-8" in w for w in facts["warnings"]), facts["warnings"])


if __name__ == "__main__":
    unittest.main()
