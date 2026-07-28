from __future__ import annotations

import copy
import subprocess
from pathlib import Path

from template_cli.posix_modes import has_posix_executable_mode, manifest_posix_executable_paths
from template_cli.validator_manifest import MANIFEST_PATH

DRY_RUN_EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}
TRANSITION_GENERATED_COMMAND_DOCS = {
    ".harness/commands/COMMANDS.md",
    ".harness/commands/CONVERSATIONAL_MODE.md",
}


def _build_update_plan(
    root: Path,
    source_root: Path,
    current_manifest: dict,
    target_manifest: dict,
) -> tuple[dict[str, list[str]], bool]:
    inventory = _effective_current_inventory(current_manifest, target_manifest)
    exclusions = _manifest_exclusions(target_manifest)
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
    current_files = _tracked_candidate_files(root, exclusions)
    source_files = _tracked_candidate_files(source_root, exclusions)
    baseline_commit = str(current_manifest.get("sourceCommit", "")).strip()
    baseline_files = _baseline_candidate_files(source_root, baseline_commit, exclusions)
    baseline_available = baseline_files is not None
    executable_paths = set(manifest_posix_executable_paths(target_manifest))
    all_files = sorted(current_files | source_files | (baseline_files or set()))
    for relative_path in all_files:
        if relative_path == MANIFEST_PATH:
            categories["unchanged"].append(relative_path)
            continue
        ownership = _ownership_class(relative_path, inventory)
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
            elif ownership == "mixedGenerated":
                categories["project-owned-preserved"].append(relative_path)
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


def _tracked_candidate_files(root: Path, exclusions: list[str] | None = None) -> set[str]:
    exclusions = exclusions or []
    files: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in DRY_RUN_EXCLUDE_DIRS for part in relative_parts):
            continue
        relative_path = path.relative_to(root).as_posix()
        if _matches_any_entry(relative_path, exclusions):
            continue
        files.add(relative_path)
    return files


def _ownership_class(relative_path: str, inventory: dict) -> str:
    best_class = "projectOwned" if relative_path.startswith("scripts/") else "mixedGenerated"
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


def _baseline_candidate_files(
    source_root: Path,
    commit: str,
    exclusions: list[str] | None = None,
) -> set[str] | None:
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
    exclusions = exclusions or []
    files = set()
    for line in result.stdout.splitlines():
        relative_parts = Path(line).parts
        if any(part in DRY_RUN_EXCLUDE_DIRS for part in relative_parts):
            continue
        relative_path = line.strip()
        if _matches_any_entry(relative_path, exclusions):
            continue
        files.add(relative_path)
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


def _manifest_exclusions(manifest: dict) -> list[str]:
    exclusions = manifest.get("artifactInventoryExclusions", [])
    if not isinstance(exclusions, list):
        return []
    return [entry for entry in exclusions if isinstance(entry, str) and entry.strip()]


def _matches_any_entry(relative_path: str, entries: list[str]) -> bool:
    return any(_matches_inventory_entry(relative_path, entry) for entry in entries)


def _effective_current_inventory(current_manifest: dict, target_manifest: dict) -> dict:
    current = current_manifest.get("artifactInventory", {})
    target = target_manifest.get("artifactInventory", {})
    if not isinstance(current, dict):
        return {}
    if not isinstance(target, dict):
        return current
    migrated = copy.deepcopy(current)
    for ownership_class in ["harnessOwned", "projectOwned", "archival"]:
        target_entries = target.get(ownership_class, [])
        migrated_entries = migrated.setdefault(ownership_class, [])
        if not isinstance(target_entries, list) or not isinstance(migrated_entries, list):
            continue
        for entry in target_entries:
            if isinstance(entry, str) and entry not in migrated_entries:
                migrated_entries.append(entry)
    current_harness = current.get("harnessOwned", [])
    target_harness = target.get("harnessOwned", [])
    if not (
        isinstance(current_harness, list)
        and "scripts/" in current_harness
        and isinstance(target_harness, list)
        and "scripts/" not in target_harness
    ):
        return migrated

    migrated["harnessOwned"] = [entry for entry in migrated.get("harnessOwned", []) if entry != "scripts/"]
    # The first target-planner transition installs only the target's exact
    # harness surface. Preserve mixed/generated project files for this one
    # apply; after the target manifest is stamped, later updates can offer them
    # through the normal reviewed mixed-generated flow.
    migrated_project_owned = migrated.setdefault("projectOwned", [])
    migrated_mixed_generated = migrated.get("mixedGenerated", [])
    if isinstance(migrated_project_owned, list) and isinstance(migrated_mixed_generated, list):
        for entry in migrated_mixed_generated:
            if (
                isinstance(entry, str)
                and entry not in TRANSITION_GENERATED_COMMAND_DOCS
                and entry not in migrated_project_owned
            ):
                migrated_project_owned.append(entry)
        migrated["mixedGenerated"] = [
            entry for entry in migrated_mixed_generated if entry in TRANSITION_GENERATED_COMMAND_DOCS
        ]
    for ownership_class in ["harnessOwned", "projectOwned", "mixedGenerated", "archival"]:
        target_entries = target.get(ownership_class, [])
        migrated_entries = migrated.setdefault(ownership_class, [])
        if not isinstance(target_entries, list) or not isinstance(migrated_entries, list):
            continue
        for entry in target_entries:
            if isinstance(entry, str) and entry.startswith("scripts/") and entry not in migrated_entries:
                migrated_entries.append(entry)
    return migrated


def requires_target_planner_transition(current_manifest: dict, target_manifest: dict) -> bool:
    current = current_manifest.get("artifactInventory", {})
    target = target_manifest.get("artifactInventory", {})
    if not isinstance(current, dict) or not isinstance(target, dict):
        return False
    current_harness = current.get("harnessOwned", [])
    target_harness = target.get("harnessOwned", [])
    return (
        isinstance(current_harness, list)
        and "scripts/" in current_harness
        and isinstance(target_harness, list)
        and "scripts/" not in target_harness
    )
