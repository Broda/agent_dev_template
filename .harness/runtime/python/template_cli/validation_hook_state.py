from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

LEDGER_FILE_LIMIT = 20_000
LEDGER_BACKUP_LIMIT = 32 * 1024 * 1024
_LEDGER_EXCLUDED_PARTS = {
    ".git",
    ".harness-update-backups",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class _FileState:
    digest: str
    mode: int
    content: bytes | None
    tracked_clean: bool


@dataclass
class ProtectedStateLedger:
    root: Path
    states: dict[str, _FileState]
    git_backed: bool

    @classmethod
    def capture(cls, root: Path) -> ProtectedStateLedger:
        root = root.resolve()
        tracked = _git_paths(root, ["ls-files", "-z"])
        if tracked is None:
            paths = _filesystem_paths(root)
            return cls(root, _capture_states(root, paths, snapshot_all=True), False)

        filesystem_paths = _filesystem_paths(root)
        untracked = filesystem_paths - tracked
        dirty = _git_dirty_paths(root)
        paths = {path for path in tracked | untracked if _is_protected_path(path)}
        states = _capture_states(root, paths, snapshot_paths=(dirty | untracked))
        return cls(root, states, True)

    def changed_paths(self) -> list[str]:
        current_paths = self._current_paths()
        changed: list[str] = []
        for relative_path in sorted(set(self.states) | current_paths):
            before = self.states.get(relative_path)
            after = _path_fingerprint(self.root / relative_path)
            if before is None or after is None:
                changed.append(relative_path)
            elif (before.digest, before.mode) != after:
                changed.append(relative_path)
        return changed

    def restore(self, changed_paths: list[str]) -> list[str]:
        failures: list[str] = []
        for relative_path in changed_paths:
            before = self.states.get(relative_path)
            path = self.root / relative_path
            try:
                if before is None:
                    if path.is_dir() and not path.is_symlink():
                        shutil.rmtree(path)
                    elif path.exists() or path.is_symlink():
                        path.unlink()
                    continue
                if before.tracked_clean and self.git_backed:
                    _restore_from_git_index(self.root, relative_path)
                    continue
                if before.content is None:
                    raise OSError("pre-hook content was not retained")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(before.content)
                path.chmod(before.mode)
            except OSError as exc:
                failures.append(f"{relative_path}: {exc}")
        return failures

    def _current_paths(self) -> set[str]:
        if self.git_backed:
            tracked = _git_paths(self.root, ["ls-files", "-z"]) or set()
            return {path for path in tracked | _filesystem_paths(self.root) if _is_protected_path(path)}
        return _filesystem_paths(self.root)


def _capture_states(
    root: Path,
    paths: set[str],
    *,
    snapshot_all: bool = False,
    snapshot_paths: set[str] | None = None,
) -> dict[str, _FileState]:
    if len(paths) > LEDGER_FILE_LIMIT:
        raise RuntimeError(f"protected worktree exceeds {LEDGER_FILE_LIMIT} files")
    snapshot_paths = snapshot_paths or set()
    backup_bytes = 0
    states: dict[str, _FileState] = {}
    for relative_path in sorted(paths):
        path = root / relative_path
        fingerprint = _path_fingerprint(path)
        if fingerprint is None:
            continue
        content = None
        tracked_clean = not snapshot_all and relative_path not in snapshot_paths
        if snapshot_all or relative_path in snapshot_paths:
            content = path.read_bytes()
            backup_bytes += len(content)
            if backup_bytes > LEDGER_BACKUP_LIMIT:
                raise RuntimeError(f"protected-state backup exceeds {LEDGER_BACKUP_LIMIT} bytes")
        states[relative_path] = _FileState(
            digest=fingerprint[0],
            mode=fingerprint[1],
            content=content,
            tracked_clean=tracked_clean,
        )
    return states


def _path_fingerprint(path: Path) -> tuple[str, int] | None:
    if not path.is_file():
        return None
    stat_result = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest, stat_result.st_mode & 0o777


def _filesystem_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for current_root, directory_names, file_names in os.walk(root, followlinks=False, onerror=_raise_walk_error):
        directory_names[:] = sorted(name for name in directory_names if name not in _LEDGER_EXCLUDED_PARTS)
        current_path = Path(current_root)
        for file_name in sorted(file_names):
            relative_path = (current_path / file_name).relative_to(root).as_posix()
            if _is_protected_path(relative_path):
                paths.add(relative_path)
                if len(paths) > LEDGER_FILE_LIMIT:
                    raise RuntimeError(f"protected worktree exceeds {LEDGER_FILE_LIMIT} files")
    return paths


def _raise_walk_error(error: OSError) -> None:
    raise error


def _is_protected_path(relative_path: str) -> bool:
    return not any(part in _LEDGER_EXCLUDED_PARTS for part in Path(relative_path).parts)


def _git_paths(root: Path, arguments: list[str]) -> set[str] | None:
    process = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        return None
    return {value.decode("utf-8", errors="surrogateescape") for value in process.stdout.split(b"\0") if value}


def _git_dirty_paths(root: Path) -> set[str]:
    process = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        return set()
    dirty: set[str] = set()
    records = [record for record in process.stdout.split(b"\0") if record]
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) >= 4:
            dirty.add(record[3:].decode("utf-8", errors="surrogateescape"))
            if record[:1] in {b"R", b"C"} or record[1:2] in {b"R", b"C"}:
                index += 1
        index += 1
    return dirty


def _restore_from_git_index(root: Path, relative_path: str) -> None:
    process = subprocess.run(
        ["git", "checkout-index", "--force", "--", relative_path],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()[:500]
        raise OSError(detail or "git checkout-index failed")
