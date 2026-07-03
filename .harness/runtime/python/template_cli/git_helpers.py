from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(root: Path, args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a git command in `root` with captured text output."""
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=check)


def git_stdout(root: Path, args: list[str]) -> str:
    """Return trimmed stdout for a git command, or "" when the command fails."""
    result = run_git(root, args)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
