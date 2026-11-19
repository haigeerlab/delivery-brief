"""docs/facts-schema.md documents exactly the fields brief_facts.py outputs (no drift either way)."""
import re
import unittest
from pathlib import Path

from fixtures import RepoCase
import test_milestone
import test_module_range

DOC = Path(__file__).resolve().parents[3] / "docs" / "facts-schema.md"
FIELD_ROW = re.compile(r"^\| `([A-Za-z0-9_.\[\]]+)` \|")


def paths(value, prefix=""):
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            path = prefix + "." + key if prefix else key
            found.add(path)
            found |= paths(item, path)
    elif isinstance(value, list):
        for item in value:
            found |= paths(item, prefix + "[]")
    return found


class SchemaDocTest(RepoCase):
    base_repo = test_module_range.ModuleRangeTest.base_repo
    finished_alpha = test_module_range.ModuleRangeTest.finished_alpha

    def test_doc_matches_output(self):
        self.finished_alpha()
        self.repo.write("tasks/alpha/todo.md", self.repo.read("tasks/alpha/todo.md") + "- [ ] 后续检查\n")
        self.repo.commit("docs: alpha 加一项未勾")
        output = paths(self.facts("--module", "alpha", "--offline"))
        self.repo.git("mv", "README.md", "README.txt")
        renamed = self.repo.commit("rename")
        output |= paths(self.facts("--range", "%s~1..%s" % (renamed, renamed), "--offline"))
        output |= self.milestone_paths()
        documented = set()
        for line in DOC.read_text(encoding="utf-8").splitlines():
            match = FIELD_ROW.match(line)
            if match:
                documented.add(match.group(1))
        self.assertEqual(sorted(output - documented), [], "fields missing from docs/facts-schema.md")
        self.assertEqual(sorted(documented - output), [], "documented fields the collector never outputs")

    def milestone_paths(self):
        """A --milestone run on a fresh fixture; a module's basis is documented once as "same as range.basis"."""
        case = test_milestone.MilestoneCase("run")
        case.setUp()
        try:
            case.build()
            nested = "milestone.modules[].range.basis."
            return {p for p in paths(case.facts("--milestone", "M1", "--offline")) if not p.startswith(nested)}
        finally:
            case.tearDown()


if __name__ == "__main__":
    unittest.main()
