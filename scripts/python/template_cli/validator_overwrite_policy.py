from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from template_cli.finalize_artifacts import FINALIZATION_BACKUP_PATHS
from template_cli.io_helpers import ValidationResult, read_text
from template_cli.render_helpers import RENDERED_ARTIFACTS


POLICY_PATH = "harness_commands/finalization_overwrite_policy.json"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_PATTERNS = [
    "sessions/*FINALIZATION_SESSION*.md",
    "exports/*PROJECT_SUMMARY*.md",
]
REQUIRED_ENTRY_FIELDS = {
    "category",
    "finalizationBehavior",
    "ownerAfterFinalization",
    "notes",
}


def validate_finalization_overwrite_policy(root: Path, result: ValidationResult) -> None:
    policy = _load_policy(root, result)
    if not isinstance(policy, dict):
        return

    if policy.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        result.add_failure("Finalization overwrite policy schemaVersion must be 1.")

    paths = policy.get("paths")
    patterns = policy.get("patterns")
    if not isinstance(paths, dict):
        result.add_failure("Finalization overwrite policy paths must be an object.")
        paths = {}
    if not isinstance(patterns, dict):
        result.add_failure("Finalization overwrite policy patterns must be an object.")
        patterns = {}

    for path in sorted(_required_paths()):
        if path not in paths:
            result.add_failure(f"Finalization overwrite policy missing path: {path}")
    for pattern in EXPECTED_PATTERNS:
        if pattern not in patterns:
            result.add_failure(f"Finalization overwrite policy missing pattern: {pattern}")

    _validate_entries(paths, "path", result)
    _validate_entries(patterns, "pattern", result)


def _load_policy(root: Path, result: ValidationResult) -> dict[str, Any] | None:
    path = root / POLICY_PATH
    if not path.exists():
        result.add_failure(f"Missing finalization overwrite policy: {POLICY_PATH}")
        return None
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        result.add_failure(f"Finalization overwrite policy contains invalid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        result.add_failure("Finalization overwrite policy root must be an object.")
        return None
    return data


def _required_paths() -> set[str]:
    return set(FINALIZATION_BACKUP_PATHS) | {artifact[0] for artifact in RENDERED_ARTIFACTS}


def _validate_entries(entries: dict[str, Any], entry_type: str, result: ValidationResult) -> None:
    for path, entry in entries.items():
        if not isinstance(entry, dict):
            result.add_failure(f"Finalization overwrite policy {entry_type} entry must be an object: {path}")
            continue
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        if missing:
            result.add_failure(
                f"Finalization overwrite policy {entry_type} entry {path} missing fields: {', '.join(missing)}"
            )
        for key in REQUIRED_ENTRY_FIELDS:
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                result.add_failure(
                    f"Finalization overwrite policy {entry_type} entry {path} field {key} must be non-empty."
                )
