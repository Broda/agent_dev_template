from __future__ import annotations

from pathlib import Path

from template_cli.finalize.helpers import (
    existing_state_value,
    first_value_for_label,
    is_placeholder_value,
    trim,
    unique_values,
)
from template_cli.workflow_data import FINALIZE_REQUIRED_FIELDS


def _required_value(value: str, field: str, missing: list[str]) -> str:
    value = trim(value)
    if not value:
        missing.append(field)
    return value


def _fail_noninteractive(missing: list[str], idea_id: str) -> None:
    unique_missing = unique_values(missing)
    lines = [
        "Cannot finalize non-interactively because required fields are missing.",
        f"Idea ID: {idea_id}",
        "Missing fields:",
    ]
    lines.extend(f"- {field}" for field in unique_missing)
    lines.append(
        "Next step: update state/project-init.json or the active idea/session, then rerun ./scripts/lab doctor."
    )
    lines.append("Use --interactive to fill missing values with prompts.")
    raise SystemExit("\n".join(lines))


def _pick_noninteractive_choice(value: str, field: str, missing: list[str]) -> str:
    return _required_value(value, field, missing)


def _collect_missing_noninteractive_fields(
    root: Path,
    hydrate_files: list[Path],
    session_paths: list[str],
    missing_fields: list[str],
) -> None:
    if not session_paths:
        missing_fields.append("session history")
    for display_name, state_keys, label in FINALIZE_REQUIRED_FIELDS:
        if display_name in {"build command", "run command", "test command"}:
            continue
        value = ""
        for state_key in state_keys:
            value = existing_state_value(root, state_key)
            if value and not is_placeholder_value(value):
                break
        if not value and label:
            value = first_value_for_label(hydrate_files, label)
        if not value or is_placeholder_value(value):
            missing_fields.append(display_name)
