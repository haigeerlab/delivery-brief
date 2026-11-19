"""Read-only git access for brief_facts: commits, numstat, file contents at a revision.

Never writes git state: no fetch, checkout or ref changes. Paths come from -z output so renames,
spaces and non-ASCII names parse correctly; bytes that are not UTF-8 become U+FFFD (see BAD_PATH_CHAR).
"""
import os
import subprocess

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
TIMEOUT = 60
BAD_PATH_CHAR = "\ufffd"


def _decode(raw):
    """git output as text; a path that is not UTF-8 is kept, with U+FFFD for the bad bytes."""
    return raw.decode("utf-8", "replace")


class GitError(Exception):
    """git itself failed or the project is not a repository (exit 4)."""


class RangeError(Exception):
    """A revision or range cannot be resolved (exit 3)."""


def run(project, *args, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    try:
        proc = subprocess.run(["git", "-c", "core.quotepath=off", "--no-pager", *args], cwd=project, env=env,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=TIMEOUT)
    except FileNotFoundError:
        raise GitError("找不到 git 命令")
    except subprocess.TimeoutExpired:
        raise GitError("git %s 超过 %d 秒没有返回" % (args[0], TIMEOUT))
    if check and proc.returncode != 0:
        raise GitError("git %s 失败：%s" % (args[0], proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]))
    return proc


def text(project, *args):
    return run(project, *args).stdout.decode("utf-8", "replace")


def ensure_repo(project):
    if not os.path.isdir(project):
        raise GitError("--project 不是目录：%s" % project)
    proc = run(project, "rev-parse", "--show-toplevel", check=False)
    if proc.returncode != 0:
        raise GitError("不是 git 仓库：%s" % project)
    return _decode(proc.stdout).strip()


def resolve(project, rev):
    proc = run(project, "rev-parse", "--verify", "--quiet", rev + "^{commit}", check=False)
    if proc.returncode != 0:
        raise RangeError("解析不出提交：%s" % rev)
    return proc.stdout.decode("utf-8").strip()


def parent(project, sha):
    """First parent of sha, or None for a root commit."""
    proc = run(project, "rev-parse", "--verify", "--quiet", sha + "^", check=False)
    return proc.stdout.decode("utf-8").strip() if proc.returncode == 0 else None


def _spec(base, head):
    return head if base is None else "%s..%s" % (base, head)


def commit_shas(project, base, head):
    return text(project, "rev-list", "--no-merges", "--reverse", _spec(base, head)).split()


def path_commits(project, rev, paths):
    """Non-merge commits reachable from rev that touch any of paths, oldest first."""
    return text(project, "log", "--reverse", "--no-merges", "--format=%H", rev, "--", *paths).split()


def list_dir(project, rev, path):
    """File names directly under path at rev ([] when it does not exist)."""
    proc = run(project, "ls-tree", "--name-only", "-z", "%s:%s" % (rev, path), check=False)
    if proc.returncode != 0:
        return []
    return [name for name in _decode(proc.stdout).split("\x00") if name]


def list_files(project, rev):
    """Every file path in the tree of rev."""
    raw = run(project, "ls-tree", "-r", "-z", "--name-only", rev).stdout
    return [path for path in _decode(raw).split("\x00") if path]


def commit_info(project, sha):
    subject, date = text(project, "show", "--no-patch", "--format=%s%x00%cI", sha).rstrip("\n").split("\x00")
    raw = run(project, "diff-tree", "--no-commit-id", "-r", "-z", "--name-only", "--root", "-M", sha).stdout
    files = [p for p in _decode(raw).split("\x00") if p]
    return {"sha": sha, "short": sha[:8], "subject": subject, "date": date, "files": files}


def _pairs(raw):
    return _decode(raw).split("\x00")


def numstat(project, base, head):
    """Per-file changes between base (None = empty tree) and head, with rename detection."""
    left = base or EMPTY_TREE
    status_parts = _pairs(run(project, "diff", "-M", "--name-status", "-z", left, head).stdout)
    statuses, i = [], 0
    while i < len(status_parts) and status_parts[i]:
        code = status_parts[i]
        if code[0] in "RC":
            statuses.append((code[0], status_parts[i + 2], status_parts[i + 1]))
            i += 3
        else:
            statuses.append((code[0], status_parts[i + 1], None))
            i += 2
    num_parts = _pairs(run(project, "diff", "-M", "--numstat", "-z", left, head).stdout)
    counts, i = {}, 0
    while i < len(num_parts) and num_parts[i]:
        added, deleted, path = num_parts[i].split("\t", 2)
        if path == "":
            path = num_parts[i + 2]
            i += 3
        else:
            i += 1
        binary = added == "-"
        counts[path] = (None if binary else int(added), None if binary else int(deleted), binary)
    files = []
    for status, path, old in statuses:
        added, deleted, binary = counts.get(path, (0, 0, False))
        entry = {"path": path, "status": status, "added": added, "deleted": deleted, "binary": binary}
        if old:
            entry["oldPath"] = old
        files.append(entry)
    return files


def diff_bytes(project, base, head):
    return len(run(project, "diff", "-M", base or EMPTY_TREE, head).stdout)


def blob_size(project, rev, path):
    proc = run(project, "cat-file", "-s", "%s:%s" % (rev, path), check=False)
    return int(proc.stdout.decode().strip()) if proc.returncode == 0 else 0


def show(project, rev, path):
    """File content at a revision, or None when it does not exist there."""
    proc = run(project, "show", "%s:%s" % (rev, path), check=False)
    return proc.stdout.decode("utf-8", "replace") if proc.returncode == 0 else None
