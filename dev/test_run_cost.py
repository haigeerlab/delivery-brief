"""dev/run_cost.py counts one /delivery-brief:brief run in a Claude Code transcript."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_cost  # noqa: E402


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result(tid, text):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": [{"type": "text", "text": text}]}]}}


def assistant(mid, read, write, out, tool=None):
    content = [{"type": "tool_use", "id": tool, "name": "Bash", "input": {"command": "x"}}] if tool else \
        [{"type": "text", "text": "ok"}]
    return {"type": "assistant", "message": {"id": mid, "model": "m", "content": content, "usage": {
        "input_tokens": 1, "cache_read_input_tokens": read, "cache_creation_input_tokens": write, "output_tokens": out}}}


RUN = [
    user("before"),
    assistant("a0", 50, 0, 9),
    user("<command-name>/delivery-brief:brief</command-name>\n<command-args>alpha</command-args>"),
    dict(user([{"type": "text", "text": "expanded command body"}]), isMeta=True),   # not a new prompt
    assistant("a1", 100, 10, 5, tool="t1"),
    assistant("a1", 100, 10, 5),            # same reply split over two lines: counted once
    tool_result("t1", "x" * 30),
    user("继续"),                             # answer to the size stop: still the same run
    assistant("a2", 140, 20, 7),
    user("<command-name>/delivery-brief:brief</command-name>\n<command-args>beta</command-args>"),
    assistant("a3", 999, 999, 999),
]


class RunCostTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(json.dumps(r) for r in RUN) + "\n")

    def tearDown(self):
        os.unlink(self.path)

    def test_counts_one_run(self):
        runs = run_cost.runs(self.path)
        self.assertEqual([r["args"] for r in runs], ["alpha", "beta"])
        self.assertEqual(runs[1]["turns"], 1)
        r = runs[0]
        self.assertEqual(r["args"], "alpha")
        self.assertEqual(r["turns"], 2)
        self.assertEqual(r["firstContext"], 111)
        self.assertEqual(r["cacheRead"], 240)
        self.assertEqual(r["cacheWrite"], 30)
        self.assertEqual(r["output"], 12)
        self.assertEqual(r["toolCalls"], 1)
        self.assertEqual(r["toolResultChars"], 30)

    def test_cli_prints_a_line(self):
        out = subprocess.run([sys.executable, "-B", os.path.join(HERE, "run_cost.py"), self.path],
                             stdout=subprocess.PIPE, check=True).stdout.decode("utf-8")
        self.assertIn("alpha", out)
        self.assertIn("轮数 2", out)


if __name__ == "__main__":
    unittest.main()
