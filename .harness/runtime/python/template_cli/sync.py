from __future__ import annotations

import sys
from pathlib import Path

from template_cli.git_helpers import run_git as _run_git


def _warn(message: str) -> None:
    print(message, file=sys.stderr)


def _pending_sync_path(root: Path) -> Path | None:
    result = _run_git(root, ["rev-parse", "--git-path", "lab-pending-sync"], check=False)
    if result.returncode != 0:
        return None
    path_text = result.stdout.strip()
    if not path_text:
        return None
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def _read_pending_sync_files(root: Path) -> list[str]:
    path = _pending_sync_path(root)
    if path is None or not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_pending_sync_files(root: Path, files: list[str]) -> None:
    path = _pending_sync_path(root)
    if path is None:
        return
    if not files:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(files) + "\n", encoding="utf-8")


def _merge_file_lists(first: list[str], second: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*first, *second]:
        if item and item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def record_pending_sync_files(root: Path, files: list[str]) -> None:
    pending = _read_pending_sync_files(root)
    _write_pending_sync_files(root, _merge_file_lists(pending, files))


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
    pending_files = _read_pending_sync_files(root)
    if files:
        files = _merge_file_lists(files, pending_files)

    add_args = ["add", "--", *files] if files else ["add", "-A"]
    add_result = _run_git(root, add_args, check=False)
    if add_result.returncode != 0:
        if add_result.stderr:
            _warn(add_result.stderr.strip())
        return add_result.returncode

    staged_result = _run_git(root, ["diff", "--cached", "--name-only"], check=False)
    staged = staged_result.stdout.strip()
    if not staged:
        if pending_files:
            _write_pending_sync_files(root, [])
        if not quiet:
            print("No staged changes to commit.")
        return 0

    commit_result = _run_git(root, ["commit", "-m", message], check=False)
    if commit_result.returncode != 0:
        if commit_result.stderr:
            _warn(commit_result.stderr.strip())
        return commit_result.returncode
    if pending_files:
        _write_pending_sync_files(root, [])

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


def run_lab_commit(root: Path, *, message: str = "brainstorm: milestone update") -> int:
    add_result = _run_git(root, ["add", "-A"], check=False)
    if add_result.returncode != 0:
        if add_result.stderr:
            _warn(add_result.stderr.strip())
        return add_result.returncode

    staged_result = _run_git(root, ["diff", "--cached", "--name-only"], check=False)
    if not staged_result.stdout.strip():
        print("No staged changes to commit.")
        return 0

    commit_result = _run_git(root, ["commit", "-m", message], check=False)
    if commit_result.returncode != 0:
        if commit_result.stderr:
            _warn(commit_result.stderr.strip())
        return commit_result.returncode

    sha_result = _run_git(root, ["rev-parse", "--short", "HEAD"], check=False)
    print(f"Committed: {sha_result.stdout.strip()}")
    return 0


def run_lab_push(root: Path) -> int:
    branch_result = _run_git(root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    branch = branch_result.stdout.strip()
    if not branch:
        _warn("Warning: Detached HEAD detected. Push skipped.")
        return 2

    remote_result = _run_git(root, ["remote"], check=False)
    remotes = {line.strip() for line in remote_result.stdout.splitlines()}
    if "origin" not in remotes:
        _warn("Warning: Remote 'origin' not configured. Push skipped.")
        return 2

    dirty_result = _run_git(root, ["status", "--porcelain"], check=False)
    if dirty_result.stdout.strip():
        _warn("Warning: Working tree is not clean. Push skipped by policy.")
        return 2

    push_result = _run_git(root, ["push", "origin", branch], check=False)
    if push_result.returncode != 0:
        _warn(f"Warning: Push failed for origin/{branch}.")
        if push_result.stderr:
            _warn(push_result.stderr.strip())
        return push_result.returncode

    sha_result = _run_git(root, ["rev-parse", "--short", "HEAD"], check=False)
    print(f"Pushed: origin/{branch} @ {sha_result.stdout.strip()}")
    return 0
