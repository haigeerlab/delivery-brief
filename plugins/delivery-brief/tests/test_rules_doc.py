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
        for script in ("brief_facts.py", "check_brief.py", "render_brief.py", "crosscheck_material.py"):
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


class CrossCheckDocsTest(unittest.TestCase):
    PROMPT = (PLUGIN / "references" / "cross-check-prompt.md").read_text(encoding="utf-8")

    def test_prompt_has_only_the_two_placeholders(self):
        self.assertEqual(sorted(set(re.findall(r"\{\{(\w+)\}\}", self.PROMPT))), ["project", "subject"])

    def test_prompt_carries_no_conclusions_or_hints(self):
        for phrase in ("可能有问题", "重点看", "我们认为", "已核实", "已知问题", "样张"):
            self.assertNotIn(phrase, self.PROMPT)
        self.assertIn("不要给代码质量打分", self.PROMPT)

    def test_command_flow(self):
        for phrase in ("delegate:review", "--cross-check", "crosscheck_material.py", "confirmed", "rejected", "unverified",
                       "不加任何别的话", "退出 0 不等于核对通过", "cross-check-prompt.md"):
            self.assertIn(phrase, COMMAND)
        render_line = [l for l in COMMAND.splitlines() if "--cross-check \"$OUT/$NAME.crosscheck.json\"" in l]
        self.assertTrue(render_line)
        self.assertIn("--cross-check", help_text("render_brief.py"))


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
