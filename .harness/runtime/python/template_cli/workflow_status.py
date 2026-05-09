from __future__ import annotations

from pathlib import Path

from template_cli.finalize_helpers import existing_state_value, files_containing
from template_cli.io_helpers import IDEA_ROW_RE, clean_backticks, parse_markdown_table_rows, path_exists, read_mode
from template_cli.workflow_data import (
    FINALIZE_ADVISORY_FIELDS,
    FINALIZE_REQUIRED_FIELDS,
    _collect_session_links,
    _default_owner,
    _extract_catalog_row,
    _find_idea_block,
    _title_from_idea_id,
)
from template_cli.workflow_development_status import run_development_status
from template_cli.workflow_readiness import (
    resolved_finalize_target,
    status_counts,
    status_readiness,
    status_signal_details,
)


def run_lab_status(root: Path) -> int:
    mode = read_mode(root) or "unknown"
    if mode == "development":
        return run_development_status(root)

    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    counts = status_counts(rows)
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

    target_row, target_source = resolved_finalize_target(root, active)
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

    readiness, required_missing, advisory_missing, advisory_present = status_readiness(root, target_row)
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
        target_row, target_source = resolved_finalize_target(root, active)

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
    readiness, required_missing, advisory_missing, advisory_present = status_readiness(root, target_row)

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
        value, source = status_signal_details(
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
        print(
            "Next step: run ./scripts/lab handoff "
            f"--idea-id {resolved_idea_id} --check to see what can be distilled from source material"
        )
        print("Then update the active idea/session or state/project-init.json for anything still missing.")
    elif advisory_missing:
        print("Advisories:")
        for item in advisory_missing:
            print(f"- capture {item} for a cleaner finalize record")
        print(f"Next step: finalize can run now with ./scripts/finalize-project --idea-id {resolved_idea_id}")
    else:
        print(f"Next step: finalize can run now with ./scripts/finalize-project --idea-id {resolved_idea_id}")
    return 0
