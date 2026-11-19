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
        for script in ("brief_facts.py", "check_brief.py", "render_brief.py", "crosscheck_material.py",
                       "take_screenshots.py"):
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


class SafeRemovalTest(unittest.TestCase):
    def test_every_rm_target_is_guarded(self):
        """Claude Code refuses `rm` whose target is a bare "$VAR/..." (empty VAR -> /); use ${VAR:?}."""
        found = 0
        for line in COMMAND.splitlines():
            for target in re.findall(r"\brm (?:-[a-z]+ )*((?:\"[^\"]*\"\s*)+)", line):
                found += 1
                self.assertNotRegex(target, r"\$(?!\{)[A-Z_]", "unguarded rm target: %s" % line.strip())
        self.assertGreater(found, 0)


def bash_blocks():
    return re.findall(r"```bash\n(.*?)```", COMMAND, re.S)


def block_with(needle):
    found = [b for b in bash_blocks() if needle in b]
    assert len(found) == 1, "expected one bash block with %r, got %d" % (needle, len(found))
    return found[0]


class FewerTurnsTest(unittest.TestCase):
    """Spec assumption 10: steps that do not need each other's results go into one call."""

    def test_prepare_block_reads_rules_collects_facts_and_records_state(self):
        block = block_with("brief-rules.md")
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/scripts/brief_facts.py"', block)
        self.assertIn('"$OUT/.$NAME.before"', block)
        self.assertIn('cat "$OUT/$NAME.facts.json"', block)

    def test_reading_is_batched(self):
        for phrase in ("分批", "每批", "3 万字符"):
            self.assertIn(phrase, COMMAND)

    def test_write_and_check_in_one_message(self):
        self.assertIn("同一条消息", COMMAND.split("## 4. 检查")[0].split("## 3.")[1])

    def test_screenshot_export_install_and_start_in_one_call(self):
        block = block_with("nohup")
        self.assertIn('git -C "$PROJECT" archive', block)
        self.assertIn("install", block)

    def test_screenshots_viewed_together(self):
        self.assertIn("一次看完", COMMAND.split("## 4.6")[1].split("## 5.")[0])

    def test_render_block_opens_and_compares_state(self):
        block = block_with('"${CLAUDE_PLUGIN_ROOT}/scripts/render_brief.py"')
        self.assertIn('open "$OUT/$NAME.html"', block)
        self.assertIn('diff "$OUT/.$NAME.before"', block)
        self.assertIn('kill -- "-$PGID"', block)


class ScreenshotDocsTest(unittest.TestCase):
    def test_command_screenshot_flow(self):
        hint = COMMAND.split("argument-hint:")[1].splitlines()[0]
        for option in ("--no-screenshots", "--base-url"):
            self.assertIn(option, hint)
        for phrase in ("## 4.6 截图", "take_screenshots.py", "--shots \"$OUT/$NAME.shots/shots.json\"", "--shots-skipped",
                       ".claude/launch.json", "--frozen-lockfile", "npm ci", "空闲端口", "进程组",
                       "不替用户登录", "不输入任何账号密码", "逐张看", "停掉服务", "删掉导出目录", ".env",
                       "未核对与终点提交一致", "--origin base-url"):
            self.assertIn(phrase, COMMAND)
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/scripts/take_screenshots.py"', COMMAND)
        for option in ("--shots", "--shots-skipped"):
            self.assertIn(option, help_text("render_brief.py"))
        for option in ("--origin", "--wait"):
            self.assertIn(option, help_text("take_screenshots.py"))

    def test_rules_screenshot_block_parses(self):
        import brief_markdown as md
        example = RULES.split("<!-- screenshot-example -->")[1].split("<!-- /screenshot-example -->")[0]
        fence = re.search(r"(`{3}screenshot .*?\n`{3})", example, re.S).group(1)
        shots = md.screenshot_blocks(md.parse("## 产出清单\n\n" + fence + "\n"))
        self.assertEqual(len(shots), 1)
        self.assertTrue(shots[0]["path"].startswith("/"))
        self.assertIn("最多 %d 个" % check_brief.MAX_SHOTS, RULES)
        self.assertIn("本模块无界面", RULES)


class RulesTemplateTest(unittest.TestCase):
    def test_template_has_the_checked_sections_in_order(self):
        template = RULES.split("````markdown", 1)[1].split("````", 1)[0]
        titles = re.findall(r"^## (.+)$", template, flags=re.M)
        self.assertEqual(tuple(titles), check_brief.SECTIONS)

    def test_rules_explain_each_section(self):
        for name in check_brief.SECTIONS:
            self.assertIn("### %s" % name, RULES)

    def test_rules_cover_evidence_and_charts(self):
        for phrase in ("证据硬规则", "不照抄 Spec", "选图规则", "一图一问", "标题写结论", "读取策略", "[[out:O1]]",
                       "[[`src/app/[[...slug]]/page.tsx`:L10-L19]]"):
            self.assertIn(phrase, RULES)


class MilestoneDocsTest(unittest.TestCase):
    def test_rules_milestone_template_matches_checker(self):
        part = RULES.split("## 里程碑页", 1)[1]
        template = part.split("````markdown", 1)[1].split("````", 1)[0]
        self.assertEqual(tuple(re.findall(r"^## (.+)$", template, flags=re.M)), check_brief.MILESTONE_SECTIONS)
        for name in check_brief.MILESTONE_SECTIONS:
            self.assertIn("### %s" % name, part)
        for phrase in ("3～10", "两个不同文件", "没有新约定", "模块 id"):
            self.assertIn(phrase, part)

    def test_command_milestone_flow(self):
        hint = COMMAND.split("argument-hint:")[1].splitlines()[0]
        for option in ("--milestone <M>", "--draft"):
            self.assertIn(option, hint)
        for phrase in ("--milestone", "milestone-$M", "里程碑页暂不支持交叉核对", "不截图", "还没生成",
                       "成功标准", "<模块 id>.md"):
            self.assertIn(phrase, COMMAND)
        for option in ("--milestone", "--draft"):
            self.assertIn(option, help_text("brief_facts.py"))


if __name__ == "__main__":
    unittest.main()
