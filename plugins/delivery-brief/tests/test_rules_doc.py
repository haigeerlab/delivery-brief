"""The command file and the brief rules agree with the scripts they describe (no drift)."""
import re
import subprocess
import sys
import unittest

from fixtures import SCRIPTS
import check_brief

PLUGIN = SCRIPTS.parent
COMMAND = (PLUGIN / "commands" / "brief.md").read_text(encoding="utf-8")
RULES = (PLUGIN / "references" / "brief-rules.md").read_text(encoding="utf-8")


def help_text(script):
    proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / script), "--help"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout.decode("utf-8")


class CommandOptionsTest(unittest.TestCase):
    def test_every_option_used_exists(self):
        for script in ("brief_facts.py", "check_brief.py", "render_brief.py"):
            lines = [line for line in COMMAND.splitlines() if script in line]
            self.assertTrue(lines, "%s is not used in commands/brief.md" % script)
            usage = help_text(script)
            for line in lines:
                for option in re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", line):
                    self.assertIn(option, usage, "%s: %s not in --help" % (script, option))

    def test_scripts_referenced_by_plugin_root(self):
        for script in ("brief_facts.py", "check_brief.py", "render_brief.py"):
            self.assertIn('"${CLAUDE_PLUGIN_ROOT}/scripts/%s"' % script, COMMAND)
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/references/brief-rules.md"', COMMAND)

    def test_threshold_matches_spec(self):
        self.assertIn("`size.diffBytes` 超过 200000", COMMAND)
        self.assertIn("--no-open", COMMAND)
        self.assertIn("git -C \"$PROJECT\" archive", COMMAND)


class RulesTemplateTest(unittest.TestCase):
    def test_template_has_the_checked_sections_in_order(self):
        template = RULES.split("````markdown", 1)[1].split("````", 1)[0]
        titles = re.findall(r"^## (.+)$", template, flags=re.M)
        self.assertEqual(tuple(titles), check_brief.SECTIONS)

    def test_rules_explain_each_section(self):
        for name in check_brief.SECTIONS:
            self.assertIn("### %s" % name, RULES)

    def test_rules_cover_evidence_and_charts(self):
        for phrase in ("证据硬规则", "不照抄 Spec", "选图规则", "一图一问", "标题写结论", "读取策略", "[[out:O1]]"):
            self.assertIn(phrase, RULES)


if __name__ == "__main__":
    unittest.main()
