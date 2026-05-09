from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from template_cli.io_helpers import ValidationResult, read_text, write_text
from template_cli.json_schema import validate_json_schema_file

MANIFEST_PATH = ".harness/commands/harness_manifest.json"
MANIFEST_SCHEMA_PATH = ".harness/commands/harness_manifest.schema.json"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_HARNESS_VERSION = "0.1.0"
EXPECTED_TEMPLATE_REPOSITORY = "https://github.com/Broda/agent_dev_template"
EXPECTED_COMPATIBILITY = {
    "wrapperRuntimeVersion": 1,
    "capabilityVersion": 1,
    "stateSchemaVersion": 2,
    "stateSchemaPath": "state/project-init.schema.v2.json",
}
EXPECTED_MODES = ["brainstorming", "development"]
EXPECTED_STABLE_WRAPPER_BACKENDS = {
    "scripts/lab": "lab-<command>",
    "scripts/finalize-project": "finalize-project",
    "scripts/validate-governance": "validate-governance",
    "scripts/project-harness": "project-harness-new | project-harness-update | project-harness-validate",
    "scripts/render-intent-docs": "render-intent-docs",
    "scripts/sync-plugin-skills": "sync-plugin-skills",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def load_harness_manifest(root: Path) -> dict[str, Any]:
    return json.loads(read_text(root / MANIFEST_PATH))


def stamp_harness_manifest(root: Path, source_root: Path) -> None:
    manifest_path = root / MANIFEST_PATH
    manifest = json.loads(read_text(manifest_path))
    source_commit = _source_commit(source_root)
    if source_commit:
        manifest["sourceCommit"] = source_commit
        manifest["sourceCommitType"] = "git"
        manifest["sourceWorktreeDirty"] = _source_worktree_dirty(source_root)
    else:
        manifest["sourceCommit"] = "unknown"
        manifest["sourceCommitType"] = "unknown"
        manifest["sourceWorktreeDirty"] = False
    write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")


def validate_harness_manifest(root: Path, result: ValidationResult) -> None:
    path = root / MANIFEST_PATH
    if not path.exists():
        result.add_failure(f"Missing harness manifest: {MANIFEST_PATH}")
        return

    try:
        manifest = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        result.add_failure(f"Invalid JSON in {MANIFEST_PATH}: {exc}")
        return

    if not isinstance(manifest, dict):
        result.add_failure("Harness manifest root must be an object.")
        return

    try:
        schema_errors = validate_json_schema_file(root, manifest, MANIFEST_SCHEMA_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        result.add_failure(f"Harness manifest schema could not be loaded: {exc}")
    else:
        for error in schema_errors:
            result.add_failure(f"Harness manifest schema validation failed: {error}")

    _validate_top_level(manifest, result)
    _validate_compatibility(manifest, result)
    _validate_wrappers(root, manifest, result)
    _validate_inventory(manifest, result)
    _validate_snapshot_policy(manifest, result)


def _validate_top_level(manifest: dict[str, Any], result: ValidationResult) -> None:
    required = {
        "schemaVersion",
        "harnessVersion",
        "templateRepository",
        "sourceCommit",
        "sourceCommitType",
        "sourceWorktreeDirty",
        "compatibility",
        "supportedModes",
        "stableWrappers",
        "artifactInventory",
        "artifactInventoryExclusions",
        "artifactInventorySnapshotPolicy",
    }
    missing = sorted(required - set(manifest.keys()))
    if missing:
        result.add_failure(f"Harness manifest missing required fields: {', '.join(missing)}")

    if manifest.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        result.add_failure("Harness manifest schemaVersion must be 1.")
    if manifest.get("harnessVersion") != EXPECTED_HARNESS_VERSION:
        result.add_failure("Harness manifest harnessVersion must be 0.1.0.")
    if manifest.get("templateRepository") != EXPECTED_TEMPLATE_REPOSITORY:
        result.add_failure(f"Harness manifest templateRepository must be {EXPECTED_TEMPLATE_REPOSITORY}.")
    if manifest.get("supportedModes") != EXPECTED_MODES:
        result.add_failure("Harness manifest supportedModes must be brainstorming, development.")
    _validate_source_commit(manifest, result)
    if not isinstance(manifest.get("sourceWorktreeDirty"), bool):
        result.add_failure("Harness manifest sourceWorktreeDirty must be true or false.")


def _validate_source_commit(manifest: dict[str, Any], result: ValidationResult) -> None:
    source_commit = str(manifest.get("sourceCommit", "")).strip()
    source_commit_type = str(manifest.get("sourceCommitType", "")).strip()
    if source_commit_type == "template":
        if source_commit != "template-source":
            result.add_failure("Template harness manifest sourceCommit must be template-source.")
    elif source_commit_type == "git":
        if not COMMIT_RE.fullmatch(source_commit):
            result.add_failure("Git-stamped harness manifest sourceCommit must be a 40-character SHA.")
    elif source_commit_type == "unknown":
        if source_commit != "unknown":
            result.add_failure("Unknown harness manifest sourceCommit must be unknown.")
    else:
        result.add_failure("Harness manifest sourceCommitType must be template, git, or unknown.")


def _validate_compatibility(manifest: dict[str, Any], result: ValidationResult) -> None:
    compatibility = manifest.get("compatibility")
    if not isinstance(compatibility, dict):
        result.add_failure("Harness manifest compatibility must be an object.")
        return
    for key, expected in EXPECTED_COMPATIBILITY.items():
        if compatibility.get(key) != expected:
            result.add_failure(f"Harness manifest compatibility.{key} must be {expected}.")


def _validate_wrappers(root: Path, manifest: dict[str, Any], result: ValidationResult) -> None:
    wrappers = manifest.get("stableWrappers")
    if not isinstance(wrappers, list) or not wrappers:
        result.add_failure("Harness manifest stableWrappers must be a non-empty array.")
        return
    seen_paths: set[str] = set()
    for index, wrapper in enumerate(wrappers, start=1):
        if not isinstance(wrapper, dict):
            result.add_failure(f"Harness manifest stableWrappers entry #{index} must be an object.")
            continue
        path = str(wrapper.get("path", "")).strip()
        backend = str(wrapper.get("backendCommand", "")).strip()
        if not path or not backend:
            result.add_failure(f"Harness manifest stableWrappers entry #{index} must include path and backendCommand.")
            continue
        if path in seen_paths:
            result.add_failure(f"Harness manifest contains duplicate stable wrapper path: {path}")
        seen_paths.add(path)
        if not (root / path).exists():
            result.add_failure(f"Harness manifest stable wrapper path is missing: {path}")
        expected_backend = EXPECTED_STABLE_WRAPPER_BACKENDS.get(path)
        if expected_backend and backend != expected_backend:
            result.add_failure(f"Harness manifest stable wrapper backendCommand for {path} must be {expected_backend}.")
    missing_expected_paths = sorted(set(EXPECTED_STABLE_WRAPPER_BACKENDS) - seen_paths)
    for path in missing_expected_paths:
        result.add_failure(f"Harness manifest missing stable wrapper entry: {path}")


def _validate_inventory(manifest: dict[str, Any], result: ValidationResult) -> None:
    inventory = manifest.get("artifactInventory")
    if not isinstance(inventory, dict):
        result.add_failure("Harness manifest artifactInventory must be an object.")
        return
    required_classes = ["harnessOwned", "projectOwned", "mixedGenerated", "archival"]
    for ownership_class in required_classes:
        paths = inventory.get(ownership_class)
        if not isinstance(paths, list) or not paths:
            result.add_failure(f"Harness manifest artifactInventory.{ownership_class} must be a non-empty array.")
            continue
        for entry in paths:
            if not isinstance(entry, str) or not entry.strip():
                result.add_failure(f"Harness manifest artifactInventory.{ownership_class} contains an empty path.")
    exclusions = manifest.get("artifactInventoryExclusions")
    if not isinstance(exclusions, list) or not exclusions:
        result.add_failure("Harness manifest artifactInventoryExclusions must be a non-empty array.")
        return
    for entry in exclusions:
        if not isinstance(entry, str) or not entry.strip():
            result.add_failure("Harness manifest artifactInventoryExclusions contains an empty path.")
    _validate_retained_artifact_coverage(inventory, exclusions, result)


def _validate_retained_artifact_coverage(
    inventory: dict[str, Any], exclusions: list[Any], result: ValidationResult
) -> None:
    from template_cli.validator_artifacts import BRAINSTORMING_CORE_ARTIFACTS

    inventory_entries = [
        entry
        for entries in inventory.values()
        if isinstance(entries, list)
        for entry in entries
        if isinstance(entry, str)
    ]
    excluded_entries = [entry for entry in exclusions if isinstance(entry, str)]
    for artifact in BRAINSTORMING_CORE_ARTIFACTS:
        if not _matches_manifest_entry(artifact, inventory_entries) and not _matches_manifest_entry(
            artifact, excluded_entries
        ):
            result.add_failure(f"Harness manifest artifact inventory does not classify retained artifact: {artifact}")


def _matches_manifest_entry(relative_path: str, entries: list[str]) -> bool:
    return any(_matches_inventory_entry(relative_path, entry) for entry in entries)


def _matches_inventory_entry(relative_path: str, entry: str) -> bool:
    entry = entry.strip()
    if not entry:
        return False
    if entry.endswith("/"):
        return relative_path.startswith(entry)
    return relative_path == entry


def _validate_snapshot_policy(manifest: dict[str, Any], result: ValidationResult) -> None:
    policy = manifest.get("artifactInventorySnapshotPolicy")
    if not isinstance(policy, dict):
        result.add_failure("Harness manifest artifactInventorySnapshotPolicy must be an object.")
        return
    if policy.get("decision") != "keep-broad-directory-entries":
        result.add_failure(
            "Harness manifest artifactInventorySnapshotPolicy.decision must be keep-broad-directory-entries."
        )
    if policy.get("snapshotGeneration") != "deferred":
        result.add_failure("Harness manifest artifactInventorySnapshotPolicy.snapshotGeneration must be deferred.")
    if not str(policy.get("rationale", "")).strip():
        result.add_failure("Harness manifest artifactInventorySnapshotPolicy.rationale must be non-empty.")
    broad_entries = policy.get("broadEntries")
    if not isinstance(broad_entries, list) or not broad_entries:
        result.add_failure("Harness manifest artifactInventorySnapshotPolicy.broadEntries must be a non-empty array.")
        return

    documented = {entry for entry in broad_entries if isinstance(entry, str)}
    inventory = manifest.get("artifactInventory", {})
    if not isinstance(inventory, dict):
        return
    for ownership_class, entries in inventory.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str) and entry.endswith("/") and entry not in documented:
                result.add_failure(
                    "Harness manifest broad artifactInventory entry must be documented in "
                    f"artifactInventorySnapshotPolicy.broadEntries: {ownership_class}.{entry}"
                )


def _source_commit(source_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    commit = result.stdout.strip()
    if COMMIT_RE.fullmatch(commit):
        return commit
    return ""


def _source_worktree_dirty(source_root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=source_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())
