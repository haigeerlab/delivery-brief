"""Where code links in a brief point: GitHub blob at the end commit, or local files.

GitHub links are used only when the repository is public and the end commit is on GitHub, so every link
resolves to exactly the code the brief describes. The only network access is `gh api`, skipped with --offline.
"""
import os
import re
import shutil
import subprocess

import facts_git

GITHUB = re.compile(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/(.+?)(?:\.git)?/?$")
GH_TIMEOUT = 10
MISSING_COMMIT = re.compile(r"HTTP 4(?:04|22)\b")


def _gh(*args):
    try:
        proc = subprocess.run(["gh", *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=GH_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, "", str(error)
    return (proc.returncode, proc.stdout.decode("utf-8", "replace").strip(),
            proc.stderr.decode("utf-8", "replace").strip())


def _local(root, end, reason):
    clean = facts_git.run(root, "diff", "--quiet", end, "--", ".", check=False).returncode == 0
    return {"kind": "local", "base": root.rstrip("/") + "/", "lineFormat": None, "repo": None,
            "workingTreeMatchesEnd": clean, "reason": reason}


def link_base(root, end, offline):
    root = os.path.realpath(root)
    if offline:
        return _local(root, end, "指定了 --offline，不查询 GitHub，链接指向本机文件")
    proc = facts_git.run(root, "remote", "get-url", "origin", check=False)
    match = GITHUB.match(proc.stdout.decode("utf-8").strip()) if proc.returncode == 0 else None
    if not match:
        return _local(root, end, "origin 不是 GitHub 仓库（或没有 origin），链接指向本机文件")
    repo = "%s/%s" % (match.group(1), match.group(2))
    if shutil.which("gh") is None:
        return _local(root, end, "没有 gh 命令，查不了 %s 是否公开，链接指向本机文件" % repo)
    code, visibility, _err = _gh("api", "repos/%s" % repo, "--jq", ".visibility")
    if code != 0:
        return _local(root, end, "gh 查询 %s 失败，链接指向本机文件" % repo)
    if visibility != "public":
        return _local(root, end, "%s 不是公开仓库（%s），链接指向本机文件" % (repo, visibility or "未知"))
    code, _out, err = _gh("api", "repos/%s/commits/%s" % (repo, end), "--silent")
    if code != 0 and MISSING_COMMIT.search(err):
        return _local(root, end, "终点提交 %s 不在远端 %s，链接指向本机文件" % (end[:8], repo))
    if code != 0:
        why = (err.splitlines() or ["没有输出"])[-1]
        return _local(root, end, "gh 查询终点提交失败（%s），不确定 %s 是否在远端，链接指向本机文件" % (why, end[:8]))
    return {"kind": "github", "base": "https://github.com/%s/blob/%s/" % (repo, end), "lineFormat": "#L{start}-L{end}",
            "repo": repo, "workingTreeMatchesEnd": None, "reason": "%s 是公开仓库，终点提交已在远端" % repo}
