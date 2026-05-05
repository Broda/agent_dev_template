from __future__ import annotations

from pathlib import Path

from template_cli.finalize import run_finalize_project
from template_cli.finalize_helpers import (
    existing_state_value,
    files_containing,
    first_value_for_label,
)
from template_cli.sync import run_lab_commit, run_lab_push
from template_cli.io_helpers import (
    IDEA_ROW_RE,
    clean_backticks,
    parse_markdown_table_rows,
    path_exists,
    read_mode,
    read_text,
)
from template_cli.validators import (
    run_validate_governance,
)
from template_cli.workflow_commands import (
    run_lab_activate,
    run_lab_capture,
    run_lab_decide,
    run_lab_export,
    run_lab_kill,
    run_lab_park,
    run_lab_path_note,
    run_lab_review,
    run_lab_risk,
)
from template_cli.workflow_data import (
    FINALIZE_ADVISORY_FIELDS,
    FINALIZE_REQUIRED_FIELDS,
    _collect_session_links,
    _default_owner,
    _extract_catalog_row,
    _extract_label_from_text,
    _find_idea_block,
    _is_placeholderish_value,
    _sync,
    _title_from_idea_id,
)


def _status_counts(rows: list[list[str]]) -> dict[str, int]:
    counts = {name: 0 for name in ["inbox", "active", "parked", "killed", "finalized"]}
    for cells in rows:
        if len(cells) > 2:
            status = cells[2].strip()
            if status in counts:
                counts[status] += 1
    return counts


def _resolved_finalize_target(root: Path, active_rows: list[list[str]]) -> tuple[dict[str, str] | None, str]:
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


def _status_signal(
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


def _status_signal_details(
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


def _status_readiness(root: Path, row: dict[str, str]) -> tuple[str, list[str], list[str], list[str]]:
    idea_id = row["idea_id"]
    idea_lookup = _find_idea_block(root, idea_id)
    idea_block = idea_lookup[1] if idea_lookup else ""
    session_files = _collect_session_links(root, idea_id, row)
    hydration_files = [
        root / rel
        for rel in files_containing(root, "ideas", idea_id) + session_files
        if path_exists(root, rel)
    ]

    required_missing: list[str] = []
    advisory_missing: list[str] = []

    if not session_files:
        required_missing.append("session history")

    for display_name, state_keys, label in FINALIZE_REQUIRED_FIELDS:
        if not _status_signal(root, state_keys=state_keys, idea_block=idea_block, hydration_files=hydration_files, label=label):
            required_missing.append(display_name)

    for display_name, state_keys, label in FINALIZE_ADVISORY_FIELDS:
        if not _status_signal(root, state_keys=state_keys, idea_block=idea_block, hydration_files=hydration_files, label=label):
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


def run_lab_status(root: Path) -> int:
    mode = read_mode(root) or "unknown"
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    counts = _status_counts(rows)
    state_idea_id = existing_state_value(root, "ideaId")
    state_status = existing_state_value(root, "status")

    print(f"Mode: {mode}")
    print(
        "Ideas tracked: "
        f"{len(rows)} "
        f"(inbox {counts['inbox']}, active {counts['active']}, parked {counts['parked']}, "
        f"killed {counts['killed']}, finalized {counts['finalized']})"
    )
    if state_idea_id:
        if state_status:
            print(f"Canonical state: {state_status} for {state_idea_id}")
        else:
            print(f"Canonical state: {state_idea_id}")
    else:
        print("Canonical state: no bound idea yet")

    if active:
        print("Active ideas:")
        for cells in active:
            while len(cells) < 2:
                cells.append("")
            print(f"- {cells[0].strip()} ({cells[1].strip() or 'untitled'})")

    target_row, target_source = _resolved_finalize_target(root, active)
    if target_row is None:
        if target_source == "ambiguous":
            print("Finalize target: ambiguous")
            print("Finalize readiness: blocked")
            print("Missing before finalize: explicit --idea-id or a single active idea")
        else:
            print("Finalize target: none")
            print("Finalize readiness: blocked")
            print("Missing before finalize: capture and activate an idea")
        return 0

    sessions = _collect_session_links(root, target_row["idea_id"], target_row)
    print(f"Finalize target: {target_row['idea_id']} (from {target_source})")
    print(f"Target title: {target_row.get('title') or _title_from_idea_id(target_row['idea_id'])}")
    print(f"Target owner: {target_row.get('owner') or _default_owner(root)}")
    print(f"Related sessions: {len(sessions)}")
    summary_export = clean_backticks(target_row.get("summary_export", ""))
    if summary_export and summary_export != "_n/a_":
        print(f"Summary snapshot: {summary_export}")
    else:
        print("Summary snapshot: none")

    readiness, required_missing, advisory_missing, advisory_present = _status_readiness(root, target_row)
    print(f"Finalize readiness: {readiness}")
    if required_missing:
        print("Missing before low-friction finalize: " + ", ".join(required_missing))
    if advisory_missing:
        print("Advisories: capture " + ", ".join(advisory_missing))
    for note in advisory_present:
        print(f"Signals: {note}")
    return 0


def run_lab_doctor(root: Path, *, idea_id: str = "") -> int:
    mode = read_mode(root) or "unknown"
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]

    print("Finalize doctor")
    print(f"Mode: {mode}")
    print(f"Requested target: {idea_id or 'auto'}")

    if idea_id:
        target_row = _extract_catalog_row(root, idea_id)
        if not target_row:
            print("Finalize target: missing")
            print(f"Blocked on: idea '{idea_id}' not found in IDEA_CATALOG.md")
            print("Next step: pass a valid --idea-id or capture/activate the intended idea first")
            return 0
        target_source = "explicit --idea-id"
    else:
        target_row, target_source = _resolved_finalize_target(root, active)

    if target_row is None:
        if target_source == "ambiguous":
            print("Finalize target: ambiguous")
            print("Candidates:")
            for cells in active:
                title = cells[1].strip() if len(cells) > 1 else ""
                print(f"- {cells[0].strip()} ({title or 'untitled'})")
            print("Blocked on: explicit --idea-id or a single active idea")
            print("Next step: rerun ./scripts/lab doctor --idea-id <idea-id> or reduce active ideas to one")
        else:
            print("Finalize target: none")
            print("Blocked on: no active or state-bound idea")
            print("Next step: capture and activate an idea, then rerun ./scripts/lab doctor")
        return 0

    resolved_idea_id = target_row["idea_id"]
    idea_lookup = _find_idea_block(root, resolved_idea_id)
    session_files = _collect_session_links(root, resolved_idea_id, target_row)
    hydration_files = [
        root / rel
        for rel in files_containing(root, "ideas", resolved_idea_id) + session_files
        if path_exists(root, rel)
    ]
    readiness, required_missing, advisory_missing, advisory_present = _status_readiness(root, target_row)

    print(f"Finalize target: {resolved_idea_id} (from {target_source})")
    print(f"Target title: {target_row.get('title') or _title_from_idea_id(resolved_idea_id)}")
    print(f"Target owner: {target_row.get('owner') or _default_owner(root)}")
    print(f"Finalize readiness: {readiness}")
    print("Target evidence:")
    print("- catalog row: IDEA_CATALOG.md")
    if idea_lookup is not None:
        print(f"- idea record: {idea_lookup[0]}")
    else:
        print("- idea record: not found in idea buckets")
    if session_files:
        print("- sessions: " + ", ".join(session_files))
    else:
        print("- sessions: none")
    summary_export = clean_backticks(target_row.get("summary_export", ""))
    if summary_export and summary_export != "_n/a_":
        print(f"- summary snapshot: {summary_export}")
    else:
        print("- summary snapshot: none")

    print("Field checks:")
    if not session_files:
        print("- session history: MISSING")
    else:
        print(f"- session history: OK via {session_files[-1]}")

    for display_name, state_keys, label in FINALIZE_REQUIRED_FIELDS + FINALIZE_ADVISORY_FIELDS:
        value, source = _status_signal_details(
            root,
            state_keys=state_keys,
            idea_label=label,
            idea_lookup=idea_lookup,
            hydration_files=hydration_files,
        )
        if value:
            print(f"- {display_name}: OK via {source}")
        else:
            print(f"- {display_name}: MISSING")

    if advisory_present:
        print("Signals:")
        for note in advisory_present:
            print(f"- {note}")

    if required_missing:
        print("Blocked on:")
        for item in required_missing:
            print(f"- {item}")
        print("Next step: update the active idea/session or prefill state/project-init.json, then rerun ./scripts/lab doctor")
    elif advisory_missing:
        print("Advisories:")
        for item in advisory_missing:
            print(f"- capture {item} for a cleaner finalize record")
        print(f"Next step: finalize can run now with ./scripts/finalize-project --idea-id {resolved_idea_id}")
    else:
        print(f"Next step: finalize can run now with ./scripts/finalize-project --idea-id {resolved_idea_id}")
    return 0


def run_lab_audit(root: Path) -> int:
    return run_validate_governance(root)


def run_lab_finalize(root: Path, *, idea_id: str = "", write_export: bool = False) -> int:
    return run_finalize_project(root, idea_id, write_export=write_export)


def run_lab_commit_command(root: Path, *, message: str = "brainstorm: milestone update") -> int:
    return run_lab_commit(root, message=message)


def run_lab_push_command(root: Path) -> int:
    return run_lab_push(root)
