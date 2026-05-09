from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from template_cli.validator_manifest import load_harness_manifest


@dataclass(frozen=True)
class UpdateSource:
    root: Path
    current_manifest: dict
    target_manifest: dict
    cleanup_dir: Path | None = None


def resolve_update_source(
    root: Path,
    source_path: str,
    source_commit: str,
    release_version: str,
    *,
    apply: bool,
) -> UpdateSource | int:
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
    if release_version:
        return _resolve_release_version_update_source(root, release_version)
    if source_commit:
        return _resolve_source_commit_update_source(root, source_commit)
    return _resolve_source_path_update_source(root, source_path)


def cleanup_update_source(source: UpdateSource) -> None:
    if source.cleanup_dir is not None:
        shutil.rmtree(source.cleanup_dir, ignore_errors=True)


def source_worktree_state(source_root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=source_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return "unavailable"
    return "dirty" if result.stdout.strip() else "clean"


def _resolve_source_path_update_source(root: Path, source_path: str) -> UpdateSource | int:
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
    return UpdateSource(source_root, current_manifest, target_manifest)


def _resolve_source_commit_update_source(root: Path, source_commit: str) -> UpdateSource | int:
    source_commit = source_commit.strip()
    if not _looks_like_commit(source_commit):
        print("--source-commit must be a 40-character lowercase Git SHA.")
        return 2
    try:
        current_manifest = load_harness_manifest(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Cannot load current harness manifest for update: {exc}")
        return 1

    template_repository = str(current_manifest.get("templateRepository", "")).strip()
    if not template_repository:
        print("Cannot resolve --source-commit: current harness manifest has no templateRepository.")
        return 1

    checkout_dir = Path(tempfile.mkdtemp(prefix="project-harness-source-"))
    clone_result = _run_quiet(
        ["git", "clone", "--quiet", "--no-checkout", template_repository, str(checkout_dir)], root
    )
    if clone_result != 0:
        shutil.rmtree(checkout_dir, ignore_errors=True)
        print(f"Cannot clone templateRepository for --source-commit: {template_repository}")
        return clone_result
    checkout_result = _run_quiet(["git", "checkout", "--quiet", source_commit], checkout_dir)
    if checkout_result != 0:
        shutil.rmtree(checkout_dir, ignore_errors=True)
        print(f"Cannot check out source commit: {source_commit}")
        return checkout_result

    try:
        target_manifest = load_harness_manifest(checkout_dir)
    except (FileNotFoundError, OSError, ValueError) as exc:
        shutil.rmtree(checkout_dir, ignore_errors=True)
        print(f"Cannot load harness manifest for update source commit: {exc}")
        return 1
    target_manifest["sourceCommit"] = source_commit
    target_manifest["sourceCommitType"] = "git"
    target_manifest["sourceWorktreeDirty"] = False
    return UpdateSource(checkout_dir, current_manifest, target_manifest, cleanup_dir=checkout_dir)


def _resolve_release_version_update_source(root: Path, release_version: str) -> UpdateSource | int:
    release_version = release_version.strip()
    if not release_version:
        print("--release-version requires a non-empty version.")
        return 2
    try:
        current_manifest = load_harness_manifest(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Cannot load current harness manifest for update: {exc}")
        return 1

    template_repository = str(current_manifest.get("templateRepository", "")).strip()
    if not template_repository:
        print("Cannot resolve --release-version: current harness manifest has no templateRepository.")
        return 1

    checkout_dir = Path(tempfile.mkdtemp(prefix="project-harness-release-"))
    clone_result = _run_quiet(
        ["git", "clone", "--quiet", "--no-checkout", template_repository, str(checkout_dir)], root
    )
    if clone_result != 0:
        shutil.rmtree(checkout_dir, ignore_errors=True)
        print(f"Cannot clone templateRepository for --release-version: {template_repository}")
        return clone_result

    release_refs = [release_version]
    if not release_version.startswith("v"):
        release_refs.insert(0, f"v{release_version}")
    checked_out_ref = ""
    for release_ref in release_refs:
        if _run_quiet(["git", "checkout", "--quiet", release_ref], checkout_dir) == 0:
            checked_out_ref = release_ref
            break
    if not checked_out_ref:
        shutil.rmtree(checkout_dir, ignore_errors=True)
        print(f"Cannot check out release version: {release_version}")
        print("Tried refs: " + ", ".join(release_refs))
        return 1

    try:
        target_manifest = load_harness_manifest(checkout_dir)
    except (FileNotFoundError, OSError, ValueError) as exc:
        shutil.rmtree(checkout_dir, ignore_errors=True)
        print(f"Cannot load harness manifest for update release version: {exc}")
        return 1
    target_commit = _git_rev_parse(checkout_dir)
    if target_commit:
        target_manifest["sourceCommit"] = target_commit
        target_manifest["sourceCommitType"] = "git"
        target_manifest["sourceWorktreeDirty"] = False
    return UpdateSource(checkout_dir, current_manifest, target_manifest, cleanup_dir=checkout_dir)


def _looks_like_commit(value: str) -> bool:
    return len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def _git_rev_parse(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    commit = result.stdout.strip()
    return commit if _looks_like_commit(commit) else ""


def _run_quiet(command: list[str], cwd: Path) -> int:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return result.returncode
