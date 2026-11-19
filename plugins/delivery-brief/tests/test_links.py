"""Link base: GitHub blob links only for a public repository whose end commit is on the remote (AC5)."""
import os
import shutil
import stat
import unittest

from fixtures import RepoCase

FAKE_GH = """#!/bin/sh
echo "$*" >> "$FAKE_GH_LOG"
case "$*" in
  *"/commits/"*) [ "$FAKE_GH_COMMIT" = "yes" ] && { echo '{}'; exit 0; }; echo 'Not Found' >&2; exit 1 ;;
  *"repos/"*) [ "$FAKE_GH_FAIL" = "yes" ] && { echo 'auth required' >&2; exit 4; }; echo "$FAKE_GH_VISIBILITY"; exit 0 ;;
esac
exit 2
"""


class LinksTest(RepoCase):
    def setUp(self):
        super().setUp()
        r = self.repo
        r.write("a.txt", "a\n")
        self.base = r.commit("init")
        r.write("a.txt", "b\n")
        self.head = r.commit("change")
        r.git("remote", "add", "origin", "https://github.com/acme/demo.git")
        bindir = os.path.join(self.tmp.name, "bin")
        os.mkdir(bindir)
        gh = os.path.join(bindir, "gh")
        with open(gh, "w") as handle:
            handle.write(FAKE_GH)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC)
        self.log = os.path.join(self.tmp.name, "gh.log")
        open(self.log, "w").close()
        self.extra_path = bindir
        os.environ.update(FAKE_GH_LOG=self.log, FAKE_GH_VISIBILITY="public", FAKE_GH_COMMIT="yes", FAKE_GH_FAIL="no")

    def tearDown(self):
        for key in ("FAKE_GH_LOG", "FAKE_GH_VISIBILITY", "FAKE_GH_COMMIT", "FAKE_GH_FAIL"):
            os.environ.pop(key, None)
        super().tearDown()

    def links(self, *extra):
        return self.facts("--range", "%s..%s" % (self.base, self.head), *extra)["links"]

    def calls(self):
        with open(self.log) as handle:
            return handle.read().splitlines()

    def test_public_and_pushed_gives_github_blob_base(self):
        links = self.links()
        self.assertEqual(links["kind"], "github")
        self.assertEqual(links["repo"], "acme/demo")
        self.assertEqual(links["base"], "https://github.com/acme/demo/blob/%s/" % self.head)
        self.assertEqual(links["lineFormat"], "#L{start}-L{end}")
        self.assertTrue(any("repos/acme/demo/commits/%s" % self.head in call for call in self.calls()))

    def test_ssh_remote_is_recognised(self):
        self.repo.git("remote", "set-url", "origin", "git@github.com:acme/demo.git")
        self.assertEqual(self.links()["repo"], "acme/demo")

    def assertLocal(self, links, reason_part):
        self.assertEqual(links["kind"], "local")
        self.assertEqual(links["base"], str(self.repo.root.resolve()) + "/")
        self.assertIsNone(links["lineFormat"])
        self.assertIn(reason_part, links["reason"])
        self.assertTrue(links["workingTreeMatchesEnd"])

    def test_private_repository(self):
        os.environ["FAKE_GH_VISIBILITY"] = "private"
        self.assertLocal(self.links(), "不是公开")

    def test_end_commit_not_on_remote(self):
        os.environ["FAKE_GH_COMMIT"] = "no"
        self.assertLocal(self.links(), "不在远端")

    def test_gh_failure(self):
        os.environ["FAKE_GH_FAIL"] = "yes"
        self.assertLocal(self.links(), "gh")

    @unittest.skipIf(shutil.which("gh", path="/usr/bin:/bin"), "a real gh lives in /usr/bin or /bin")
    def test_gh_missing(self):
        self.extra_path = None
        os.environ["PATH_BACKUP"] = os.environ["PATH"]
        try:
            os.environ["PATH"] = "/usr/bin:/bin"
            links = self.links()
        finally:
            os.environ["PATH"] = os.environ.pop("PATH_BACKUP")
        self.assertLocal(links, "没有 gh")

    def test_offline_never_calls_gh(self):
        self.assertLocal(self.links("--offline"), "--offline")
        self.assertEqual(self.calls(), [])

    def test_not_github_remote(self):
        self.repo.git("remote", "set-url", "origin", "https://gitlab.example.com/acme/demo.git")
        self.assertLocal(self.links(), "GitHub")
        self.assertEqual(self.calls(), [])

    def test_working_tree_differs_from_end(self):
        self.repo.write("a.txt", "dirty\n")
        links = self.facts("--range", "%s..%s" % (self.base, self.base + "~0"), "--offline")["links"]
        self.assertFalse(links["workingTreeMatchesEnd"])


if __name__ == "__main__":
    unittest.main()
