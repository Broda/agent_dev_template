from __future__ import annotations

from pathlib import Path

from template_cli.finalize_helpers import existing_state_value, files_containing, first_value_for_label
from template_cli.io_helpers import clean_backticks, path_exists, read_text
from template_cli.workflow_data import (
    FINALIZE_ADVISORY_FIELDS,
    FINALIZE_REQUIRED_FIELDS,
    _collect_session_links,
    _extract_catalog_row,
    _extract_label_from_text,
    _find_idea_block,
    _is_placeholderish_value,
)


def status_counts(rows: list[list[str]]) -> dict[str, int]:
    counts = {name: 0 for name in ["inbox", "active", "parked", "killed", "finalized"]}
    for cells in rows:
        if len(cells) > 2:
            status = cells[2].strip()
            if status in counts:
                counts[status] += 1
    return counts


def resolved_finalize_target(root: Path, active_rows: list[list[str]]) -> tuple[dict[str, str] | None, str]:
    state_idea_id = existing_state_value(root, "ideaId")
    if state_idea_id:
        row = _extract_catalog_row(root, state_idea_id)
        if row.get("idea_id"):
            return row, "canonical state"

    if len(active_rows) == 1:
        idea_id = active_rows[0][0].strip()
        row = _extract_catalog_row(root, idea_id)
        if row.get("idea_id"):
            return row, "single active idea"

    if len(active_rows) > 1:
        return None, "ambiguous"
    return None, "none"


def status_signal(
    root: Path,
    *,
    state_keys: list[str],
    idea_block: str,
    hydration_files: list[Path],
    label: str = "",
) -> str:
    for state_key in state_keys:
        value = existing_state_value(root, state_key)
        if value and not _is_placeholderish_value(value):
            return value
    if label:
        direct_value = _extract_label_from_text(idea_block, label)
        if direct_value and not _is_placeholderish_value(direct_value):
            return direct_value
        hydrated_value = first_value_for_label(hydration_files, label)
        if hydrated_value and not _is_placeholderish_value(hydrated_value):
            return hydrated_value
    return ""


def status_signal_details(
    root: Path,
    *,
    state_keys: list[str],
    idea_label: str,
    idea_lookup: tuple[str, str] | None,
    hydration_files: list[Path],
) -> tuple[str, str]:
    for state_key in state_keys:
        value = existing_state_value(root, state_key)
        if value and not _is_placeholderish_value(value):
            return value, f"state.{state_key}"
    if idea_label and idea_lookup is not None:
        value = _extract_label_from_text(idea_lookup[1], idea_label)
        if value and not _is_placeholderish_value(value):
            return value, f"{idea_lookup[0]}:{idea_label}"
    if idea_label:
        idea_relpath = idea_lookup[0] if idea_lookup is not None else ""
        for path in hydration_files:
            relpath = path.relative_to(root).as_posix()
            if relpath == idea_relpath:
                continue
            value = _extract_label_from_text(read_text(path), idea_label)
            if value and not _is_placeholderish_value(value):
                return value, f"{relpath}:{idea_label}"
    return "", ""


def status_readiness(root: Path, row: dict[str, str]) -> tuple[str, list[str], list[str], list[str]]:
    idea_id = row["idea_id"]
    idea_lookup = _find_idea_block(root, idea_id)
    idea_block = idea_lookup[1] if idea_lookup else ""
    session_files = _collect_session_links(root, idea_id, row)
    hydration_files = [
        root / rel for rel in files_containing(root, "ideas", idea_id) + session_files if path_exists(root, rel)
    ]

    required_missing: list[str] = []
    advisory_missing: list[str] = []

    if not session_files:
        required_missing.append("session history")

    for display_name, state_keys, label in FINALIZE_REQUIRED_FIELDS:
        if not status_signal(
            root, state_keys=state_keys, idea_block=idea_block, hydration_files=hydration_files, label=label
        ):
            required_missing.append(display_name)

    for display_name, state_keys, label in FINALIZE_ADVISORY_FIELDS:
        if not status_signal(
            root, state_keys=state_keys, idea_block=idea_block, hydration_files=hydration_files, label=label
        ):
            advisory_missing.append(display_name)

    summary_export = clean_backticks(row.get("summary_export", ""))
    if summary_export and summary_export != "_n/a_":
        advisory_present = [f"summary snapshot: {summary_export}"]
    else:
        advisory_present = []

    if required_missing:
        return "needs-input", required_missing, advisory_missing, advisory_present
    if advisory_missing:
        return "ready-with-advisories", required_missing, advisory_missing, advisory_present
    return "ready", required_missing, advisory_missing, advisory_present
