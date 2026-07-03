from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from template_cli.bootstrap.update_plan import _build_update_plan
from template_cli.bootstrap.update_source import UpdateSource, source_worktree_state
from template_cli.io_helpers import read_mode
from template_cli.validator_manifest import stamp_harness_manifest


def _apply_update_source(root: Path, source: UpdateSource, *, yes: bool, include_mixed: bool) -> int:
    root = root.resolve()
    plan, _baseline_available = _build_update_plan(root, source.root, source.current_manifest, source.target_manifest)

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
    update_paths = list(plan["harness-owned"]) + list(plan["removed"])
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
        if relative_path in plan["removed"]:
            current_path.unlink()
        else:
            _copy_source_file(source.root / relative_path, current_path)

    hook_results: list[tuple[str, int]] = []
    if any(path.startswith(".agents/skills/") for path in update_paths):
        hook_results.append(("sync-plugin-skills", _run(_template_cli_command("sync-plugin-skills"), root)))
    if ".harness/commands/intent_registry.json" in update_paths:
        hook_results.append(("render-intent-docs", _run(_template_cli_command("render-intent-docs"), root)))
    failed_hooks = [(label, result) for label, result in hook_results if result != 0]
    if failed_hooks:
        _rollback_update(root, backup_dir, update_paths)
        print("Post-update hook failed. Rolled back copied files from backup:")
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
            _rollback_update(root, backup_dir, update_paths)
            print("Validation failed after update apply. Rolled back copied files from backup:")
            print(f"  {backup_dir}")
            return result

    stamp_harness_manifest(root, source.root)
    final_validation = _run(_template_cli_command("validate-governance"), root)
    validation_results.append(("validate-governance-after-provenance", final_validation))
    if final_validation != 0:
        _rollback_update(root, backup_dir, update_paths)
        print("Provenance validation failed after update apply. Rolled back copied files from backup:")
        print(f"  {backup_dir}")
        return final_validation

    print("Applied harness update.")
    print(f"Backup directory: {backup_dir}")
    print(f"Target source worktree: {source_worktree_state(source.root)}")
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


def _copy_source_file(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def _rollback_update(root: Path, backup_dir: Path, update_paths: list[str]) -> None:
    for relative_path in update_paths:
        current_path = root / relative_path
        backup_path = backup_dir / relative_path
        if backup_path.exists():
            current_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, current_path)
        elif current_path.exists():
            current_path.unlink()
    _run(_template_cli_command("sync-plugin-skills"), root)
    _run(_template_cli_command("render-intent-docs"), root)


def _timestamp_label() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _run(command: list[str], cwd: Path) -> int:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode


def _template_cli_command(command: str) -> list[str]:
    return [sys.executable, str(Path(".harness") / "runtime" / "python" / "cli.py"), command]
