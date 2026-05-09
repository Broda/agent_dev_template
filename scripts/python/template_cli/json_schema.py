from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from template_cli.io_helpers import read_text


def validate_json_schema_file(root: Path, data: Any, schema_path: str) -> list[str]:
    schema = json.loads(read_text(root / schema_path))
    if not isinstance(schema, dict):
        return [f"{schema_path} root must be an object."]
    return validate_json_schema_data(data, schema)


def validate_json_schema_data(data: Any, schema: dict[str, Any]) -> list[str]:
    return list(_validate(data, schema, "$", schema))


def _validate(data: Any, schema: dict[str, Any], path: str, root_schema: dict[str, Any]) -> list[str]:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = _resolve_ref(ref, root_schema)
        if resolved is None:
            return [f"{path}: unsupported schema reference {ref}"]
        return _validate(data, resolved, path, root_schema)

    errors: list[str] = []
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _matches_type(data, expected_type):
        return [f"{path}: expected {_type_name(expected_type)}"]

    if "const" in schema and data != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")

    enum = schema.get("enum")
    if isinstance(enum, list) and data not in enum:
        allowed = ", ".join(repr(value) for value in enum)
        errors.append(f"{path}: expected one of {allowed}")

    if isinstance(data, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(data) < min_length:
            errors.append(f"{path}: expected string length at least {min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, data) is None:
            errors.append(f"{path}: expected string matching {pattern}")

    if isinstance(data, int) and not isinstance(data, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, int | float) and data < minimum:
            errors.append(f"{path}: expected number at least {minimum}")

    if isinstance(data, dict):
        errors.extend(_validate_object(data, schema, path, root_schema))

    if isinstance(data, list):
        errors.extend(_validate_array(data, schema, path, root_schema))

    return errors


def _validate_object(
    data: dict[Any, Any],
    schema: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in data:
                errors.append(f"{path}: missing required field {key!r}")

    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for key, child_schema in properties.items():
            if key in data and isinstance(child_schema, dict):
                errors.extend(_validate(data[key], child_schema, _child_path(path, key), root_schema))

    additional = schema.get("additionalProperties", True)
    known = set(properties) if isinstance(properties, dict) else set()
    for key, value in data.items():
        if key in known:
            continue
        key_path = _child_path(path, str(key))
        if additional is False:
            errors.append(f"{path}: unknown field {key!r}")
        elif isinstance(additional, dict):
            errors.extend(_validate(value, additional, key_path, root_schema))

    return errors


def _validate_array(
    data: list[Any],
    schema: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(data) < min_items:
        errors.append(f"{path}: expected at least {min_items} item(s)")

    if schema.get("uniqueItems") is True:
        seen: set[str] = set()
        for item in data:
            marker = json.dumps(item, sort_keys=True)
            if marker in seen:
                errors.append(f"{path}: expected unique items")
                break
            seen.add(marker)

    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, item in enumerate(data):
            errors.extend(_validate(item, item_schema, f"{path}[{index}]", root_schema))

    return errors


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any] | None:
    if not ref.startswith("#/$defs/"):
        return None
    current: Any = root_schema
    for part in ref.removeprefix("#/").split("/"):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current if isinstance(current, dict) else None


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _type_name(expected_type: str) -> str:
    return {
        "object": "object",
        "array": "array",
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
        "null": "null",
    }.get(expected_type, expected_type)


def _child_path(path: str, key: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return f"{path}.{key}"
    return f"{path}[{key!r}]"
