"""take_screenshots.py: wait for the server, one PNG per screenshot block, honest failures (AC1)."""
import functools
import glob
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from fixtures import SCRIPTS

SHOOT = SCRIPTS / "take_screenshots.py"
sys.path.insert(0, str(SCRIPTS))
import take_screenshots  # noqa: E402

CHROME = take_screenshots.find_chrome(None)


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def png_size(path):
    with open(path, "rb") as handle:
        head = handle.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def leftover_profiles():
    return set(glob.glob(os.path.join(tempfile.gettempdir(), "delivery-brief-chrome-*")))


class ShotCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        site = os.path.join(self.tmp.name, "site")
        os.makedirs(os.path.join(site, "dash"))
        with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as handle:
            handle.write("<h1>首页</h1>")
        with open(os.path.join(site, "dash", "index.html"), "w", encoding="utf-8") as handle:
            handle.write("<h1>看板</h1>")
        handler = functools.partial(_Quiet, directory=site)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]
        self.out = os.path.join(self.tmp.name, "brief.shots")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def source(self, *pages):
        path = os.path.join(self.tmp.name, "brief.md")
        body = "".join("```screenshot %s\n%s\n```\n\n" % page for page in pages)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("## 产出清单\n\n" + body)
        return path

    def shoot(self, source, *extra, env=None):
        proc = subprocess.run([sys.executable, "-B", str(SHOOT), "--source", source, "--out", self.out, *extra],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, **(env or {})))
        err = proc.stderr.decode("utf-8")
        self.assertNotIn("Traceback", err)
        return proc.returncode, err

    def record(self):
        with open(os.path.join(self.out, "shots.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def requireChrome(self):
        if CHROME is None:
            self.skipTest("本机找不到 Chrome，跳过要真截图的用例")


class ScreenshotTest(ShotCase):
    def test_two_pages_give_two_pngs(self):
        self.requireChrome()
        before = leftover_profiles()
        code, err = self.shoot(self.source(("首页", "/"), ("看板", "/dash/")), "--base-url", self.base)
        self.assertEqual(code, 0, err)
        record = self.record()
        self.assertEqual(record["baseUrl"], self.base)
        self.assertEqual(record["viewport"], [1280, 800])
        self.assertTrue(record["chrome"])
        shots = record["shots"]
        self.assertEqual([s["file"] for s in shots], ["01.png", "02.png"])
        for shot in shots:
            self.assertEqual(shot["status"], "ok", shot)
            self.assertEqual(shot["httpStatus"], 200)
            self.assertEqual(png_size(os.path.join(self.out, shot["file"])), (1280, 800))
            self.assertEqual(set(shot), {"title", "path", "file", "status", "reason", "httpStatus", "finalUrl"})
        self.assertEqual(shots[1]["finalUrl"], self.base + "/dash/")
        self.assertEqual(leftover_profiles() - before, set())

    def test_404_page_is_still_shot_and_others_unaffected(self):
        self.requireChrome()
        code, err = self.shoot(self.source(("没有", "/nope"), ("首页", "/")), "--base-url", self.base)
        self.assertEqual(code, 0, err)
        first, second = self.record()["shots"]
        self.assertEqual(first["httpStatus"], 404)
        self.assertIn("404", first["reason"])
        self.assertEqual(second["status"], "ok")

    def test_old_pngs_are_removed(self):
        self.requireChrome()
        os.makedirs(self.out)
        stale = os.path.join(self.out, "07.png")
        open(stale, "wb").close()
        self.shoot(self.source(("首页", "/")), "--base-url", self.base)
        self.assertFalse(os.path.exists(stale))


class FailureTest(ShotCase):
    def test_unreachable_address_fails_every_shot(self):
        dead = "http://127.0.0.1:%d" % free_port()
        code, err = self.shoot(self.source(("首页", "/"), ("看板", "/dash/")), "--base-url", dead, "--wait", "2",
                               "--chrome", CHROME or "/bin/false")
        self.assertEqual(code, 0, err)
        shots = self.record()["shots"]
        self.assertEqual([s["status"] for s in shots], ["failed", "failed"])
        self.assertIn("2 秒内不可访问", shots[0]["reason"])

    def test_missing_chrome_fails_every_shot(self):
        missing = os.path.join(self.tmp.name, "no-chrome")
        for extra, env in ((("--chrome", missing), None), ((), {"DELIVERY_BRIEF_CHROME": missing})):
            code, err = self.shoot(self.source(("首页", "/")), "--base-url", self.base, *extra, env=env)
            self.assertEqual(code, 0, err)
            shot = self.record()["shots"][0]
            self.assertEqual(shot["status"], "failed")
            self.assertIn("没有找到 Chrome", shot["reason"])

    def test_no_screenshot_blocks_writes_empty_record(self):
        code, err = self.shoot(self.source(), "--base-url", self.base)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.record()["shots"], [])

    def test_usage_error_exits_2(self):
        code, err = self.shoot(self.source(("首页", "/")))
        self.assertEqual(code, 2)
        self.assertRegex(err, "[一-鿿]")


if __name__ == "__main__":
    unittest.main()
