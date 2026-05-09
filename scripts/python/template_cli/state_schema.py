from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from template_cli.io_helpers import ValidationResult, path_exists, read_text


STATE_FILE = "state/project-init.json"
STATE_SCHEMA_FILE = "state/project-init.schema.v2.json"
STATE_SCHEMA_VERSION = 2


def load_project_state(root: Path, result: ValidationResult) -> dict[str, Any]:
    state_path = root / STATE_FILE
    if not state_path.exists():
        result.add_failure(f"Missing required artifact: {STATE_FILE}")
        return {}
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError as exc:
        result.add_failure(f"Invalid JSON in {STATE_FILE}: {exc}")
        return {}
    if not isinstance(state, dict):
        result.add_failure("state/project-init.json root must be an object.")
        return {}
    return state


def validate_project_state_file(
    root: Path,
    result: ValidationResult,
    *,
    variant: str,
    check_artifact_references: bool = False,
) -> dict[str, Any]:
    state = load_project_state(root, result)
    if state:
        validate_project_state_data(
            root,
            result,
            state,
            variant=variant,
            check_artifact_references=check_artifact_references,
        )
    return state


def validate_project_state_data(
    root: Path,
    result: ValidationResult,
    state: dict[str, Any],
    *,
    variant: str,
    check_artifact_references: bool = False,
) -> None:
    schema = _load_schema(root, result)
    if not schema:
        return
    if variant not in schema.get("x-variantRequirements", {}):
        result.add_failure(f"Unsupported state/project-init.json validation variant: {variant}")
        return
    _validate_required_and_types(state, schema, result, "")
    _validate_schema_version(state, result)
    _validate_variant(root, state, schema, variant, check_artifact_references, result)


def _load_schema(root: Path, result: ValidationResult) -> dict[str, Any]:
    schema_path = root / STATE_SCHEMA_FILE
    if not schema_path.exists():
        result.add_failure(f"Missing required artifact: {STATE_SCHEMA_FILE}")
        return {}
    try:
        schema = json.loads(read_text(schema_path))
    except json.JSONDecodeError as exc:
        result.add_failure(f"Invalid JSON in {STATE_SCHEMA_FILE}: {exc}")
        return {}
    if not isinstance(schema, dict):
        result.add_failure("state/project-init.schema.v2.json root must be an object.")
        return {}
    return schema


def _validate_required_and_types(
    value: Any,
    schema: dict[str, Any],
    result: ValidationResult,
    prefix: str,
) -> None:
    expected_type = schema.get("type")
    if expected_type and not _matches_type(value, expected_type):
        if prefix:
            result.add_failure(f"state/project-init.json {prefix} must be a {_type_name(expected_type)}.")
        return

    if not isinstance(value, dict):
        return

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if key not in value:
                result.add_failure(f"state/project-init.json must include {_join_path(prefix, key)}.")

    if not isinstance(properties, dict):
        return

    for key, child_schema in properties.items():
        if key not in value or not isinstance(child_schema, dict):
            continue
        child_path = _join_path(prefix, key)
        child = value[key]
        _validate_array_items(child, child_schema, child_path, result)
        if child_schema.get("type") == "object":
            _validate_required_and_types(child, child_schema, result, child_path)
        elif child_schema.get("type") and not _matches_type(child, child_schema["type"]):
            result.add_failure(
                f"state/project-init.json {child_path} must be a {_type_name(child_schema['type'])}."
            )


def _validate_array_items(
    value: Any,
    schema: dict[str, Any],
    path: str,
    result: ValidationResult,
) -> None:
    if schema.get("type") != "array":
        return
    if not isinstance(value, list):
        result.add_failure(f"state/project-init.json {path} must be an array.")
        return
    item_schema = schema.get("items", {})
    if not isinstance(item_schema, dict) or item_schema.get("type") != "string":
        return
    for item in value:
        if not isinstance(item, str):
            result.add_failure(f"state/project-init.json {path} entries must be strings.")
            return


def _validate_schema_version(state: dict[str, Any], result: ValidationResult) -> None:
    if state.get("schemaVersion") != STATE_SCHEMA_VERSION:
        result.add_failure("state/project-init.json schemaVersion must be 2.")


def _validate_variant(
    root: Path,
    state: dict[str, Any],
    schema: dict[str, Any],
    variant: str,
    check_artifact_references: bool,
    result: ValidationResult,
) -> None:
    variant_schema = schema.get("x-variantRequirements", {}).get(variant, {})
    expected_status = variant_schema.get("status")
    if expected_status and state.get("status") != expected_status:
        result.add_failure(f"state/project-init.json must be marked {expected_status}.")

    for path in variant_schema.get("nonEmpty", []):
        if not _non_empty_value(_value_at(state, path)):
            result.add_failure(_non_empty_message(path))

    if check_artifact_references:
        _validate_artifact_references(root, state, result)


def _validate_artifact_references(root: Path, state: dict[str, Any], result: ValidationResult) -> None:
    artifacts = state.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return
    adr_references = artifacts.get("adrReferences", [])
    if isinstance(adr_references, list):
        for adr_reference in adr_references:
            if not isinstance(adr_reference, str) or not adr_reference.strip():
                result.add_failure("state/project-init.json contains an empty artifacts.adrReferences entry.")
                continue
            if not path_exists(root, adr_reference):
                result.add_failure(f"state/project-init.json references a missing ADR file: {adr_reference}")
    summary_export = str(artifacts.get("summaryExport", "")).strip()
    if summary_export and not path_exists(root, summary_export):
        result.add_failure(f"state/project-init.json references a missing summary export: {summary_export}")


def _non_empty_message(path: str) -> str:
    special = {
        "ideaId": "state/project-init.json must include a non-empty ideaId.",
        "projectType": "state/project-init.json must include a non-empty projectType.",
    }
    return special.get(path, f"state/project-init.json must include {path}.")


def _value_at(state: dict[str, Any], path: str) -> Any:
    cur: Any = state
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _non_empty_value(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    return bool(str(value or "").strip())


def _join_path(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def _type_name(expected: str) -> str:
    if expected == "array":
        return "array"
    if expected == "object":
        return "object"
    if expected == "integer":
        return "integer"
    if expected == "boolean":
        return "boolean"
    return expected
