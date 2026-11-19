"""facts_summary.py: a short view of facts for the prepare step (Spec assumption 10)."""
import json
import os
import subprocess
import sys
import tempfile

from fixtures import SCRIPTS
from test_milestone import MilestoneCase

SUMMARY = SCRIPTS / "facts_summary.py"


def summarize(path):
    proc = subprocess.run([sys.executable, "-B", str(SUMMARY), "--facts", str(path)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class FactsSummaryTest(MilestoneCase):
    def write(self, facts):
        fd, path = tempfile.mkstemp(suffix=".facts.json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(facts, fh, ensure_ascii=False)
        self.addCleanup(os.unlink, path)
        return path

    def check_common(self, facts, out, path):
        for key in facts:
            self.assertIn(key, out, "top-level key %s missing" % key)
        for commit in facts["commits"]:
            line = [l for l in out.splitlines() if l.strip().startswith(commit["short"])]
            self.assertEqual(len(line), 1, commit["short"])
            self.assertIn(commit["subject"], line[0])
        for f in facts["files"]:
            self.assertTrue(any(l.strip().endswith(" " + f["path"]) and l.strip().startswith(f["status"])
                                for l in out.splitlines()), f["path"])
        self.assertNotIn('"files": [', out)
        self.assertIn(str(path), out)

    def test_module_and_range(self):
        self.build()
        for args in (("--module", "alpha"), ("--range", "%s..%s" % (self.alpha[0], self.beta[1]))):
            facts = self.facts(*args, "--offline")
            path = self.write(facts)
            code, out, err = summarize(path)
            self.assertEqual((code, err), (0, ""))
            self.check_common(facts, out, path)

    def test_milestone_is_shorter_and_drops_basis(self):
        self.build()
        facts = self.facts("--milestone", "M1", "--offline")
        path = self.write(facts)
        code, out, _err = summarize(path)
        self.assertEqual(code, 0)
        self.check_common(facts, out, path)
        milestone_line = [l for l in out.splitlines() if l.startswith("milestone: ")]
        self.assertEqual(len(milestone_line), 1)
        self.assertNotIn('"basis"', milestone_line[0])
        for group in facts["codeMap"]:
            self.assertTrue(any(l.strip().startswith(group["path"] + " ") for l in out.splitlines()), group["path"])
        for module in facts["milestone"]["modules"]:
            self.assertIn(module["id"], out)
            self.assertIn(module["status"], out)
        self.assertLess(len(out), len(json.dumps(facts, ensure_ascii=False)))

    def test_bad_input(self):
        path = self.write({"no": "facts"})
        code, _out, err = summarize(path)
        self.assertEqual(code, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)
        code, _out, err = summarize(path + ".missing")
        self.assertEqual(code, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)
