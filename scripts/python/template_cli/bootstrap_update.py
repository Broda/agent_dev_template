from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from template_cli.io_helpers import read_mode
from template_cli.validator_manifest import MANIFEST_PATH, load_harness_manifest, stamp_harness_manifest


DRY_RUN_EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}


def run_project_harness_update_dry_run(
    root: Path,
    *,
    source_path: str = "",
    source_commit: str = "",
    release_version: str = "",
) -> int:
    resolved = _resolve_update_source(root, source_path, source_commit, release_version, apply=False)
    if isinstance(resolved, int):
        return resolved
    source_root, current_manifest, target_manifest = resolved

    plan = _build_update_plan(root.resolve(), source_root, current_manifest, target_manifest)
    _print_update_plan(root.resolve(), source_root, current_manifest, target_manifest, plan)
    return 0


def run_project_harness_update_apply(
    root: Path,
    *,
    source_path: str = "",
    source_commit: str = "",
    release_version: str = "",
    yes: bool = False,
    include_mixed: bool = False,
) -> int:
    resolved = _resolve_update_source(root, source_path, source_commit, release_version, apply=True)
    if isinstance(resolved, int):
        return resolved
    source_root, current_manifest, target_manifest = resolved
    root = root.resolve()
    plan, _baseline_available = _build_update_plan(root, source_root, current_manifest, target_manifest)

    if plan["conflicted"]:
        print("Refusing to apply update while conflicts are present:")
        for path in plan["conflicted"]:
            print(f"  - {path}")
        return 1
    if plan["mixed-generated"] and not include_mixed:
        print("Refusing to apply mixed/generated updates without --include-mixed:")
        for path in plan["mixed-generated"]:
            print(f"  - {path}")
        return 1
    update_paths = list(plan["harness-owned"])
    if include_mixed:
        update_paths.extend(plan["mixed-generated"])
    update_paths = sorted(update_paths)
    if not update_paths:
        print("No clean harness-owned updates to apply.")
        return 0
    if not yes:
        print("Refusing to apply without --yes confirmation.")
        print("Re-run with --yes after reviewing project-harness update --dry-run output.")
        return 2

    backup_dir = root / ".harness-update-backups" / _timestamp_label()
    for relative_path in update_paths:
        current_path = root / relative_path
        if current_path.exists():
            backup_path = backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current_path, backup_path)
        _copy_source_file(source_root / relative_path, current_path)

    hook_results: list[tuple[str, int]] = []
    if any(path.startswith(".agents/skills/") for path in update_paths):
        hook_results.append(("sync-plugin-skills", _run(_template_cli_command("sync-plugin-skills"), root)))
    if "harness_commands/intent_registry.json" in update_paths:
        hook_results.append(("render-intent-docs", _run(_template_cli_command("render-intent-docs"), root)))
    failed_hooks = [(label, result) for label, result in hook_results if result != 0]
    if failed_hooks:
        print("Post-update hook failed. Restore from backup if needed:")
        print(f"  {backup_dir}")
        return failed_hooks[0][1]

    validation_commands = [("validate-governance", "validate-governance")]
    if read_mode(root) == "development":
        validation_commands.append(("validate-development", "validate-development"))
    validation_results: list[tuple[str, int]] = []
    for cli_command, label in validation_commands:
        result = _run(_template_cli_command(cli_command), root)
        validation_results.append((label, result))
        if result != 0:
            print("Validation failed after update apply. Restore from backup if needed:")
            print(f"  {backup_dir}")
            return result

    stamp_harness_manifest(root, source_root)
    final_validation = _run(_template_cli_command("validate-governance"), root)
    validation_results.append(("validate-governance-after-provenance", final_validation))
    if final_validation != 0:
        print("Provenance validation failed after update apply. Restore from backup if needed:")
        print(f"  {backup_dir}")
        return final_validation

    print("Applied harness update.")
    print(f"Backup directory: {backup_dir}")
    print("Changed paths:")
    for path in update_paths:
        print(f"  - {path}")
    if hook_results:
        print("Hooks:")
        for label, result in hook_results:
            print(f"  - {label}: {result}")
    print("Validation:")
    for label, result in validation_results:
        print(f"  - {label}: {result}")
    print("Review with: git diff")
    return 0


def _resolve_update_source(
    root: Path,
    source_path: str,
    source_commit: str,
    release_version: str,
    *,
    apply: bool,
) -> tuple[Path, dict, dict] | int:
    selected_sources = [
        label
        for label, value in [
            ("--source-path", source_path),
            ("--source-commit", source_commit),
            ("--release-version", release_version),
        ]
        if value
    ]
    command = "project-harness update --apply" if apply else "project-harness update --dry-run"
    if len(selected_sources) != 1:
        print(
            f"{command} requires exactly one explicit update source: "
            "--source-path, --source-commit, or --release-version."
        )
        return 2
    if source_commit or release_version:
        selected = source_commit or release_version
        print(f"Update source is explicit but unavailable locally: {selected}")
        print("Use --source-path <template-checkout> for dry-run comparison in this local helper.")
        return 1

    source_root = Path(source_path).expanduser()
    if not source_root.is_absolute():
        source_root = (root / source_root).resolve()
    else:
        source_root = source_root.resolve()
    root = root.resolve()
    if source_root == root:
        print("Refusing update dry run: --source-path must point to a different template checkout.")
        return 2
    if not source_root.exists() or not source_root.is_dir():
        print(f"Update source path does not exist: {source_root}")
        return 1

    try:
        current_manifest = load_harness_manifest(root)
        target_manifest = load_harness_manifest(source_root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Cannot load harness manifest for update: {exc}")
        return 1
    return source_root, current_manifest, target_manifest


def _build_update_plan(
    root: Path,
    source_root: Path,
    current_manifest: dict,
    target_manifest: dict,
) -> tuple[dict[str, list[str]], bool]:
    inventory = current_manifest.get("artifactInventory", {})
    categories = {
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
                categories["removed"].append(relative_path)
            else:
                categories["added"].append(relative_path)
            continue
        if not current_exists or not source_exists:
            continue
        if _same_file(current_path, source_path):
            categories["unchanged"].append(relative_path)
            continue

        if baseline_available:
            current_content = _file_content(current_path)
            baseline_content = _baseline_file_content(source_root, baseline_commit, relative_path)
            if current_content == baseline_content:
                _add_update_category(categories, ownership, relative_path)
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


def _print_update_plan(
    root: Path,
    source_root: Path,
    current_manifest: dict,
    target_manifest: dict,
    plan_with_baseline: tuple[dict[str, list[str]], bool],
) -> None:
    plan, baseline_available = plan_with_baseline
    print("Project harness update dry run")
    print(f"Current project: {root}")
    print(f"Target source: {source_root}")
    print(
        "Current harness: "
        f"{current_manifest.get('harnessVersion', 'unknown')} "
        f"({current_manifest.get('sourceCommit', 'unknown')})"
    )
    print(
        "Target harness: "
        f"{target_manifest.get('harnessVersion', 'unknown')} "
        f"({target_manifest.get('sourceCommit', 'unknown')})"
    )
    if baseline_available:
        print("Recorded source baseline: resolved")
    else:
        print("Recorded source baseline: unavailable")
    print("Writes: none")
    for label in [
        "harness-owned",
        "mixed-generated",
        "conflicted",
        "missing",
        "removed",
        "added",
        "project-owned-preserved",
        "unchanged",
    ]:
        paths = plan[label]
        print(f"{label}: {len(paths)}")
        for path in paths:
            print(f"  - {path}")
    print("Next commands:")
    print("  apply updates: not implemented yet; Milestone 4 will add project-harness update --apply")
    print("  skip groups: rerun dry-run after adjusting the source or local files")


def _add_update_category(categories: dict[str, list[str]], ownership: str, relative_path: str) -> None:
    if ownership == "harnessOwned":
        categories["harness-owned"].append(relative_path)
    elif ownership == "mixedGenerated":
        categories["mixed-generated"].append(relative_path)
    else:
        categories["mixed-generated"].append(relative_path)


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


def _matches_inventory_entry(relative_path: str, entry: str) -> bool:
    entry = entry.strip()
    if not entry:
        return False
    if entry.endswith("/"):
        return relative_path.startswith(entry)
    return relative_path == entry


def _same_file(left: Path, right: Path) -> bool:
    try:
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False


def _file_content(path: Path) -> bytes | None:
    if not path.exists():
        return None
    try:
        return path.read_bytes()
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
    return result.stdout


def _looks_like_commit(value: str) -> bool:
    return len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def _copy_source_file(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def _timestamp_label() -> str:
    result = subprocess.run(
        ["date", "-u", "+%Y%m%dT%H%M%SZ"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "update-backup"


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


def _run(command: list[str], cwd: Path) -> int:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode


def _template_cli_command(command: str) -> list[str]:
    return [sys.executable, str(Path("scripts") / "python" / "cli.py"), command]
