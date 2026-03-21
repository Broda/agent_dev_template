from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=check,
    )


def _warn(message: str) -> None:
    print(message, file=sys.stderr)


def run_lab_sync(
    root: Path,
    *,
    message: str = "brainstorm: milestone update",
    no_push: bool = False,
    quiet: bool = False,
    no_warn_push_failure: bool = False,
    files: list[str] | None = None,
) -> int:
    files = files or []

    add_args = ["add", "--", *files] if files else ["add", "-A"]
    add_result = _run_git(root, add_args, check=False)
    if add_result.returncode != 0:
        if add_result.stderr:
            _warn(add_result.stderr.strip())
        return add_result.returncode

    staged_result = _run_git(root, ["diff", "--cached", "--name-only"], check=False)
    staged = staged_result.stdout.strip()
    if not staged:
        if not quiet:
            print("No staged changes to commit.")
        return 0

    commit_result = _run_git(root, ["commit", "-m", message], check=False)
    if commit_result.returncode != 0:
        if commit_result.stderr:
            _warn(commit_result.stderr.strip())
        return commit_result.returncode

    sha_result = _run_git(root, ["rev-parse", "--short", "HEAD"], check=False)
    commit_sha = sha_result.stdout.strip()
    if not quiet:
        print(f"Committed: {commit_sha}")

    if no_push:
        if not quiet:
            print("Push skipped due to --no-push.")
        return 0

    branch_result = _run_git(root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    branch = branch_result.stdout.strip()
    if not branch:
        _warn("Warning: Detached HEAD detected. Commit kept locally; push skipped.")
        return 2

    remote_result = _run_git(root, ["remote"], check=False)
    remotes = {line.strip() for line in remote_result.stdout.splitlines()}
    if "origin" not in remotes:
        _warn("Warning: Remote 'origin' not configured. Commit kept locally; push skipped.")
        return 2

    dirty_result = _run_git(root, ["status", "--porcelain"], check=False)
    dirty = dirty_result.stdout.strip()
    if dirty:
        _warn("Warning: Working tree is not clean after commit. Push skipped by policy.")
        _warn("Warning: Commit kept locally. Resolve local changes, then push manually.")
        return 2

    push_result = _run_git(root, ["push", "origin", branch], check=False)
    if push_result.returncode != 0:
        if no_warn_push_failure:
            return 0
        _warn(f"Warning: Push failed for origin/{branch}. Commit {commit_sha} is local and safe.")
        _warn(f"Warning: Retry: git push origin {branch}")
        if push_result.stderr:
            _warn(push_result.stderr.strip())
        return 3

    if not quiet:
        print(f"Pushed: origin/{branch} @ {commit_sha}")
    return 0


def run_lab_sync_from_argv(root: Path, argv: list[str]) -> int:
    message = "brainstorm: milestone update"
    no_push = False
    quiet = False
    no_warn_push_failure = False
    files: list[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--no-push":
            no_push = True
            i += 1
        elif arg == "--quiet":
            quiet = True
            i += 1
        elif arg == "--no-warn-push-failure":
            no_warn_push_failure = True
            i += 1
        elif arg in {"-m", "--message"}:
            if i + 1 >= len(argv):
                _warn(f"Error: {arg} requires a value.")
                return 1
            message = argv[i + 1]
            i += 2
        elif arg == "--":
            files.extend(argv[i + 1 :])
            break
        else:
            if len(argv) == 1 and not files and not arg.startswith("-"):
                message = arg
            else:
                files.append(arg)
            i += 1

    return run_lab_sync(
        root,
        message=message,
        no_push=no_push,
        quiet=quiet,
        no_warn_push_failure=no_warn_push_failure,
        files=files,
    )
