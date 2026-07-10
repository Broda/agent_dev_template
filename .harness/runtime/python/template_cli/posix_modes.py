from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from typing import Any

POSIX_EXECUTABLE_MODE = 0o755
POSIX_EXECUTABLE_PATHS = [
    "scripts/finalize-project",
    "scripts/finalize-project.sh",
    "scripts/harness-release-check",
    "scripts/harness-release-check.sh",
    "scripts/lab",
    "scripts/lab-note",
    "scripts/lab-note.sh",
    "scripts/lab-sync",
    "scripts/lab-sync.sh",
    "scripts/lab.sh",
    "scripts/project-harness",
    "scripts/project-harness.sh",
    "scripts/render-development-docs",
    "scripts/render-development-docs.sh",
    "scripts/render-intent-docs",
    "scripts/render-intent-docs.sh",
    "scripts/sync-plugin-skills",
    "scripts/sync-plugin-skills.sh",
    "scripts/validate-brainstorming",
    "scripts/validate-brainstorming.sh",
    "scripts/validate-development",
    "scripts/validate-development.sh",
    "scripts/validate-governance",
    "scripts/validate-governance.sh",
]


def manifest_posix_executable_paths(manifest: dict[str, Any]) -> list[str]:
    paths = manifest.get("posixExecutablePaths")
    if not isinstance(paths, list):
        return []
    return [path for path in paths if isinstance(path, str) and path]


def ensure_posix_executable_modes(root: Path, paths: list[str] | None = None) -> None:
    if os.name == "nt":
        return
    for relative_path in paths or POSIX_EXECUTABLE_PATHS:
        path = root / relative_path
        if path.is_file():
            path.chmod(POSIX_EXECUTABLE_MODE)


def has_posix_executable_mode(path: Path) -> bool:
    if os.name == "nt":
        return True
    # Working-tree modes follow the checkout umask (0775 under umask 002, 0700
    # under umask 077), so only the owner execute bit is required here; the Git
    # index and release archives carry the exact 100755 distribution contract.
    return bool(stat.S_IMODE(path.stat().st_mode) & stat.S_IXUSR)


def stage_posix_executable_modes(root: Path, paths: list[str] | None = None) -> int:
    tracked_paths = [path for path in paths or POSIX_EXECUTABLE_PATHS if (root / path).is_file()]
    if not tracked_paths:
        return 0
    result = subprocess.run(
        ["git", "update-index", "--chmod=+x", "--", *tracked_paths],
        cwd=root,
        check=False,
    )
    return result.returncode


def git_index_mode(root: Path, relative_path: str) -> str:
    if not (root / ".git").exists():
        return ""
    result = subprocess.run(
        ["git", "ls-files", "--stage", "--", relative_path],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return ""
    return result.stdout.split(maxsplit=1)[0]
