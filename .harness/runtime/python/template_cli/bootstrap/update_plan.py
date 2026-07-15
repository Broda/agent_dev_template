from __future__ import annotations

import subprocess
from pathlib import Path

from template_cli.posix_modes import has_posix_executable_mode, manifest_posix_executable_paths
from template_cli.validator_manifest import MANIFEST_PATH

DRY_RUN_EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}


def _build_update_plan(
    root: Path,
    source_root: Path,
    current_manifest: dict,
    target_manifest: dict,
) -> tuple[dict[str, list[str]], bool]:
    inventory = current_manifest.get("artifactInventory", {})
    categories: dict[str, list[str]] = {
        "harness-owned": [],
        "project-owned-preserved": [],
        "mixed-generated": [],
        "missing": [],
        "added": [],
        "removed": [],
        "conflicted": [],
        "unchanged": [],
    }
    current_files = _tracked_candidate_files(root)
    source_files = _tracked_candidate_files(source_root)
    baseline_commit = str(current_manifest.get("sourceCommit", "")).strip()
    baseline_files = _baseline_candidate_files(source_root, baseline_commit)
    baseline_available = baseline_files is not None
    executable_paths = set(manifest_posix_executable_paths(target_manifest))
    all_files = sorted(current_files | source_files | (baseline_files or set()))
    for relative_path in all_files:
        if relative_path == MANIFEST_PATH:
            categories["unchanged"].append(relative_path)
            continue
        ownership = _update_ownership_class(relative_path, inventory, target_manifest)
        current_path = root / relative_path
        source_path = source_root / relative_path
        current_exists = current_path.exists()
        source_exists = source_path.exists()

        if ownership in {"projectOwned", "archival"}:
            categories["project-owned-preserved"].append(relative_path)
            continue
        if not current_exists and source_exists:
            categories["missing"].append(relative_path)
            continue
        if current_exists and not source_exists:
            if ownership == "harnessOwned":
                if _cleanly_removed_from_source(root, source_root, baseline_commit, baseline_available, relative_path):
                    categories["removed"].append(relative_path)
                else:
                    categories["conflicted"].append(relative_path)
            else:
                categories["added"].append(relative_path)
            continue
        if not current_exists or not source_exists:
            continue
        if _same_file(current_path, source_path, require_executable=relative_path in executable_paths):
            categories["unchanged"].append(relative_path)
            continue

        if baseline_available:
            current_content = _file_content(current_path)
            baseline_content = _baseline_file_content(source_root, baseline_commit, relative_path)
            source_content = _file_content(source_path)
            if current_content == baseline_content:
                _add_update_category(categories, ownership, relative_path)
            elif ownership == "mixedGenerated" and source_content == baseline_content:
                categories["project-owned-preserved"].append(relative_path)
            else:
                categories["conflicted"].append(relative_path)
            continue

        if _git_file_dirty(root, relative_path):
            categories["conflicted"].append(relative_path)
        elif ownership == "mixedGenerated":
            categories["mixed-generated"].append(relative_path)
        elif ownership == "harnessOwned":
            categories["harness-owned"].append(relative_path)
        else:
            categories["mixed-generated"].append(relative_path)
    return categories, baseline_available


def _add_update_category(categories: dict[str, list[str]], ownership: str, relative_path: str) -> None:
    if ownership == "harnessOwned":
        categories["harness-owned"].append(relative_path)
    elif ownership == "mixedGenerated":
        categories["mixed-generated"].append(relative_path)
    else:
        categories["mixed-generated"].append(relative_path)


def _cleanly_removed_from_source(
    root: Path,
    source_root: Path,
    baseline_commit: str,
    baseline_available: bool,
    relative_path: str,
) -> bool:
    if baseline_available:
        current_content = _file_content(root / relative_path)
        baseline_content = _baseline_file_content(source_root, baseline_commit, relative_path)
        return current_content == baseline_content and baseline_content is not None
    return not _git_file_dirty(root, relative_path)


def _tracked_candidate_files(root: Path) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in DRY_RUN_EXCLUDE_DIRS for part in relative_parts):
            continue
        files.add(path.relative_to(root).as_posix())
    return files


def _ownership_class(relative_path: str, inventory: dict) -> str:
    best_class = "mixedGenerated"
    best_length = -1
    for ownership_class, entries in inventory.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, str):
                continue
            if _matches_inventory_entry(relative_path, entry) and len(entry) > best_length:
                best_class = ownership_class
                best_length = len(entry)
    return best_class


def _update_ownership_class(relative_path: str, current_inventory: dict, target_manifest: dict) -> str:
    target_schema_path = str(target_manifest.get("compatibility", {}).get("stateSchemaPath", "") or "").strip()
    target_inventory = target_manifest.get("artifactInventory", {})
    is_schema_artifact = target_schema_path.startswith("state/project-init.schema.") and target_schema_path.endswith(
        ".json"
    )
    if (
        is_schema_artifact
        and relative_path == target_schema_path
        and _ownership_class(relative_path, target_inventory) == "harnessOwned"
    ):
        return "harnessOwned"
    return _ownership_class(relative_path, current_inventory)


def _matches_inventory_entry(relative_path: str, entry: str) -> bool:
    entry = entry.strip()
    if not entry:
        return False
    if entry.endswith("/"):
        return relative_path.startswith(entry)
    return relative_path == entry


def _same_file(left: Path, right: Path, *, require_executable: bool = False) -> bool:
    try:
        if left.read_bytes() != right.read_bytes():
            return False
        return not require_executable or has_posix_executable_mode(left)
    except OSError:
        return False


def _file_content(path: Path) -> bytes | None:
    if not path.exists():
        return None
    try:
        # CRLF working-tree copies must compare equal to LF git blobs under the
        # repo-wide `* text=auto eol=lf` policy, so comparisons are LF-normalized.
        return path.read_bytes().replace(b"\r\n", b"\n")
    except OSError:
        return None


def _baseline_candidate_files(source_root: Path, commit: str) -> set[str] | None:
    if not _looks_like_commit(commit):
        return None
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit],
        cwd=source_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    files = set()
    for line in result.stdout.splitlines():
        relative_parts = Path(line).parts
        if any(part in DRY_RUN_EXCLUDE_DIRS for part in relative_parts):
            continue
        files.add(line.strip())
    return files


def _baseline_file_content(source_root: Path, commit: str, relative_path: str) -> bytes | None:
    if not _looks_like_commit(commit):
        return None
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=source_root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.replace(b"\r\n", b"\n")


def _looks_like_commit(value: str) -> bool:
    return len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def _git_file_dirty(root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", relative_path],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())
