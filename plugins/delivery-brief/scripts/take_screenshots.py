#!/usr/bin/env python3
"""Screenshot every ```screenshot block of a brief source with the local Chrome in headless mode.

Waits until --base-url answers, then takes one viewport PNG per block (01.png, 02.png, ...) into --out and writes
--out/shots.json:

  {"baseUrl", "chrome", "viewport": [w, h],
   "shots": [{"title", "path", "file", "status": "ok"|"failed", "reason", "httpStatus", "finalUrl"}]}

A failure is recorded per shot and never stops the run: exit 0 whenever shots.json is written, 2 for usage errors.
The agent looks at every PNG afterwards and may turn a shot into "failed" (login page, error page, blank page).
Starting and stopping the dev server is not this script's job (see commands/brief.md).
"""
import argparse
import glob
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brief_markdown as md  # noqa: E402

MAC_CHROMES = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Chromium.app/Contents/MacOS/Chromium")
PATH_CHROMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
SHOT_TIMEOUT = 60
PROFILE_PREFIX = "delivery-brief-chrome-"


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError("参数错误：%s" % message)


def find_chrome(explicit):
    """An explicit path (--chrome, then DELIVERY_BRIEF_CHROME) is used as given; otherwise the usual places."""
    chosen = explicit or os.environ.get("DELIVERY_BRIEF_CHROME")
    if chosen:
        return chosen if os.path.isfile(chosen) and os.access(chosen, os.X_OK) else None
    for path in MAC_CHROMES:
        if os.path.isfile(path):
            return path
    for name in PATH_CHROMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def probe(url, timeout=10):
    """(HTTP status, final URL after redirects), or (None, reason) when nothing answers."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.geturl()
    except urllib.error.HTTPError as error:
        return error.code, error.geturl() or url
    except (urllib.error.URLError, OSError, ValueError) as error:
        return None, str(getattr(error, "reason", error))


def wait_for(url, seconds):
    deadline = time.time() + seconds
    while True:
        status, _ = probe(url, timeout=5)
        if status is not None:
            return True
        if time.time() >= deadline:
            return False
        time.sleep(1)


def shoot(chrome, url, target, width, height):
    """Run headless Chrome once; returns an error reason or None."""
    profile = tempfile.mkdtemp(prefix=PROFILE_PREFIX)
    args = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", "--force-device-scale-factor=1",
            "--user-data-dir=%s" % profile, "--window-size=%d,%d" % (width, height), "--screenshot=%s" % target, url]
    try:
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            proc.wait(timeout=SHOT_TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            return "Chrome 截图超过 %d 秒没有完成" % SHOT_TIMEOUT
    except OSError as error:
        return "Chrome 启动失败：%s" % error
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    try:
        with open(target, "rb") as handle:
            if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                return "Chrome 写出的不是 PNG 文件"
    except OSError:
        return "Chrome 没有写出截图文件（退出码 %s）" % proc.returncode
    return None


def run(args):
    with open(args.source, encoding="utf-8") as handle:
        blocks = md.parse(handle.read())
    pages = md.screenshot_blocks(blocks)
    os.makedirs(args.out, exist_ok=True)
    for stale in glob.glob(os.path.join(args.out, "*.png")):
        os.remove(stale)
    base = args.base_url.rstrip("/")
    chrome = find_chrome(args.chrome)
    up = bool(pages) and chrome is not None and wait_for(base + "/", args.wait)
    shots = []
    for index, page in enumerate(pages, 1):
        name = "%02d.png" % index
        url = base + page["path"]
        shot = {"title": page["title"], "path": page["path"], "file": name, "status": "failed", "reason": "",
                "httpStatus": None, "finalUrl": None}
        if chrome is None:
            shot["reason"] = "没有找到 Chrome（可用 --chrome 或环境变量 DELIVERY_BRIEF_CHROME 指定）"
        elif not up:
            shot["reason"] = "地址 %s 在 %d 秒内不可访问" % (base, args.wait)
        else:
            status, final = probe(url)
            shot["httpStatus"], shot["finalUrl"] = (status, final) if status is not None else (None, None)
            problem = shoot(chrome, url, os.path.join(args.out, name), args.width, args.height)
            if problem:
                shot["reason"] = problem
            else:
                shot["status"] = "ok"
                if status is None:
                    shot["reason"] = "截图前查询地址失败：%s" % final
                elif status >= 400:
                    shot["reason"] = "页面返回 HTTP %d" % status
        shots.append(shot)
    record = {"baseUrl": base, "chrome": chrome, "viewport": [args.width, args.height], "shots": shots}
    with open(os.path.join(args.out, "shots.json"), "w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=1)
    return record


def main(argv=None):
    parser = _Parser(prog="take_screenshots.py", description="给讲解源文件里的截图块逐张截图，写 shots.json")
    parser.add_argument("--source", required=True, help="讲解源文件（.md）")
    parser.add_argument("--base-url", required=True, help="开发服务器地址，如 http://127.0.0.1:5173")
    parser.add_argument("--out", required=True, help="截图目录，如 <名字>.shots")
    parser.add_argument("--chrome", help="Chrome 可执行文件；缺省依次找 DELIVERY_BRIEF_CHROME、本机安装、PATH")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=800)
    parser.add_argument("--wait", type=int, default=120, help="等地址可访问的秒数")
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
        if not os.path.isfile(args.source):
            raise UsageError("参数错误：讲解源文件不存在：%s" % args.source)
    except UsageError as error:
        print(str(error), file=sys.stderr)
        return 2
    record = run(args)
    done = sum(1 for shot in record["shots"] if shot["status"] == "ok")
    print("截图 %d 张，成功 %d 张：%s" % (len(record["shots"]), done, os.path.join(args.out, "shots.json")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
