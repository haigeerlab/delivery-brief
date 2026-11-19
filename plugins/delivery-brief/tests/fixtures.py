"""Helpers for building throwaway git repositories in tests."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
CLI = SCRIPTS / "brief_facts.py"
sys.path.insert(0, str(SCRIPTS))

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


class Repo:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args):
        env = dict(os.environ, **GIT_ENV)
        out = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=str(self.root), env=env,
                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return out.stdout.decode("utf-8", "surrogateescape")

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            target.write_bytes(text)
        else:
            target.write_text(text, encoding="utf-8")

    def read(self, path):
        return (self.root / path).read_text(encoding="utf-8")

    def remove(self, path):
        (self.root / path).unlink()

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def snapshot(self):
        """Working tree status, every ref and every file's content: must not change when the collector runs."""
        return (self.git("status", "--porcelain=v1", "-uall"),
                self.git("for-each-ref", "--format=%(refname) %(objectname)"),
                self.git("rev-parse", "--symbolic-full-name", "HEAD"),
                self.git("log", "-1", "--format=%H", "--all"),
                tree_digest(self.root))


def tree_digest(root):
    """Path and content digest of every file under root, .git included except its lock-free index stat noise."""
    entries = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, str(root))
            if rel == os.path.join(".git", "index"):
                continue
            with open(path, "rb") as handle:
                entries.append((rel, hashlib.sha256(handle.read()).hexdigest()))
    return entries


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(os.path.join(self.tmp.name, "proj"))
        self.extra_path = None

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, check_readonly=True, plain_dir=None):
        """Run the collector; the project (or plain_dir, for a non-repository) must be byte-for-byte unchanged."""
        before = None
        if check_readonly:
            before = tree_digest(plain_dir) if plain_dir else self.repo.snapshot()
        env = dict(os.environ, **GIT_ENV)
        if self.extra_path:
            env["PATH"] = self.extra_path + os.pathsep + env.get("PATH", "")
        proc = subprocess.run([sys.executable, "-B", str(CLI), *args], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if before is not None:
            after = tree_digest(plain_dir) if plain_dir else self.repo.snapshot()
            self.assertEqual(before, after, "collector changed the project")
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def facts(self, *args):
        code, out, err = self.run_cli("--project", str(self.repo.root), *args)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def assertOneLineError(self, code, expected_code, err):
        self.assertEqual(code, expected_code, err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        self.assertRegex(err, "[\u4e00-\u9fff]", "error message is not Chinese: %r" % err)
