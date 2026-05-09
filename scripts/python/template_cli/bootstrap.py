from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from template_cli.io_helpers import read_mode, write_text
from template_cli.validator_manifest import load_harness_manifest, stamp_harness_manifest


COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
)
DRY_RUN_EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}


def run_project_harness_new(
    root: Path,
    target: str,
    *,
    origin: str = "",
    no_git: bool = False,
) -> int:
    target_path = Path(target).expanduser()
    if not target_path.is_absolute():
        target_path = (Path.cwd() / target_path).resolve()
    else:
        target_path = target_path.resolve()

    root = root.resolve()
    if target_path == root or root in target_path.parents:
        print("Refusing to create a harness inside the template repository.")
        return 1
    if target_path.exists():
        print(f"Target already exists: {target_path}")
        return 1

    shutil.copytree(root, target_path, ignore=COPY_IGNORE)
    _write_brainstorming_mode(target_path)
    stamp_harness_manifest(target_path, root)

    if origin and no_git:
        print("--origin cannot be used with --no-git.")
        return 1

    if not no_git:
        init_result = _run(["git", "init", "-b", "main"], target_path)
        if init_result != 0:
            return init_result
        identity_result = _ensure_initial_commit_identity(target_path)
        if identity_result != 0:
            return identity_result
        add_result = _run(["git", "add", "-A"], target_path)
        if add_result != 0:
            return add_result
        commit_result = _run(["git", "commit", "-m", "Initialize project harness"], target_path)
        if commit_result != 0:
            return commit_result
    if origin:
        origin_result = _run(["git", "remote", "add", "origin", origin], target_path)
        if origin_result != 0:
            return origin_result

    validation_result = _run(_template_cli_command("validate-governance"), target_path)
    if validation_result != 0:
        return validation_result

    print(f"Created project harness: {target_path}")
    if origin:
        print(f"Configured origin: {origin}")
    elif no_git:
        print("Git was not initialized because --no-git was supplied.")
    else:
        print("Initialized independent Git repository with no remote.")
    return 0


def run_project_harness_validate(root: Path) -> int:
    commands = [("validate-governance", "./scripts/validate-governance")]
    if read_mode(root) == "development":
        commands.append(("validate-development", "./scripts/validate-development"))

    for cli_command, display_command in commands:
        print(f"Running: {display_command}")
        result = _run(_template_cli_command(cli_command), root)
        print(f"Exit code: {result}")
        if result != 0:
            return result
    return 0


def run_project_harness_update_dry_run(
    root: Path,
    *,
    source_path: str = "",
    source_commit: str = "",
    release_version: str = "",
) -> int:
    selected_sources = [
        label
        for label, value in [
            ("--source-path", source_path),
            ("--source-commit", source_commit),
            ("--release-version", release_version),
        ]
        if value
    ]
    if len(selected_sources) != 1:
        print(
            "project-harness update --dry-run requires exactly one explicit update source: "
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
        print(f"Cannot load harness manifest for update dry run: {exc}")
        return 1

    plan = _build_update_plan(root, source_root, current_manifest, target_manifest)
    _print_update_plan(root, source_root, current_manifest, target_manifest, plan)
    return 0


def _write_brainstorming_mode(root: Path) -> None:
    write_text(
        root / "MODE.md",
        "\n".join(
            [
                "# Repository Mode",
                "",
                "Current mode: brainstorming",
                "",
                "Allowed values:",
                "",
                "- brainstorming",
                "- development",
                "",
                "Switch modes with `./scripts/finalize-project`.",
                "",
            ]
        ),
    )


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


def _ensure_initial_commit_identity(root: Path) -> int:
    if not _git_config_value(root, "user.name"):
        name_result = _run(["git", "config", "user.name", "Project Harness"], root)
        if name_result != 0:
            return name_result
    if not _git_config_value(root, "user.email"):
        email_result = _run(["git", "config", "user.email", "project-harness@example.invalid"], root)
        if email_result != 0:
            return email_result
    return 0


def _git_config_value(root: Path, key: str) -> str:
    result = subprocess.run(
        ["git", "config", "--get", key],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
