from __future__ import annotations

import json
from pathlib import Path

from template_cli.finalize.context import load_finalize_context
from template_cli.finalize.helpers import (
    STATE_FILE,
    STATE_SCHEMA_VERSION,
    infer_project_type,
    is_placeholder_value,
    latest_session_path,
    summarize_decisions,
)
from template_cli.handoff_contract import REQUIRED_PATHS, SCALAR_LABELS
from template_cli.handoff_implementation import fill_implementation_contract
from template_cli.handoff_labels import first_label_value, handoff_source_files
from template_cli.handoff_state import fill, fill_list, load_state, value_at, with_defaults
from template_cli.handoff_summary import print_summary, write_handoff_session
from template_cli.io_helpers import IDEA_ROW_RE, ValidationResult, parse_markdown_table_rows, write_text
from template_cli.state_schema import validate_project_state_data
from template_cli.sync import run_lab_sync
from template_cli.workflow_readiness import resolved_finalize_target


def run_lab_handoff(root: Path, *, idea_id: str = "", check: bool = False, no_sync: bool = False) -> int:
    resolved_idea_id = _resolve_handoff_idea_id(root, idea_id)
    context = load_finalize_context(root, resolved_idea_id)
    source_files = handoff_source_files(root, context)
    original_state = load_state(root)
    state = with_defaults(original_state)
    filled: list[str] = []

    fill(state, "schemaVersion", STATE_SCHEMA_VERSION, filled)
    fill(state, "status", "draft", filled)
    fill(state, "ideaId", context.idea_id, filled)
    fill(state, "projectName", context.project_name, filled)
    fill(state, "owner", context.owner, filled)

    for dotted_path, labels in SCALAR_LABELS.items():
        fill(state, dotted_path, first_label_value(source_files, labels), filled)

    if not value_at(state, "projectType"):
        fill(state, "projectType", infer_project_type(context.project_name, value_at(state, "purpose")), filled)

    decision_summary = summarize_decisions(
        value_at(state, "projectType"),
        value_at(state, "persistence"),
        value_at(state, "authentication"),
        value_at(state, "determinism"),
        value_at(state, "packaging"),
    )
    fill(state, "governance.keyDecisions", decision_summary, filled)
    fill(state, "governance.latestReviewSession", latest_session_path(context.session_paths), filled)
    fill(
        state,
        "artifacts.noteReferences",
        context.notes_col if not is_placeholder_value(context.notes_col) else "None recorded",
        filled,
    )
    fill(state, "artifacts.summaryExport", context.existing_export_path, filled)
    fill_list(state, "artifacts.ideaFiles", context.idea_files, filled)
    fill_list(state, "artifacts.sessionFiles", context.session_paths, filled)
    fill_list(state, "artifacts.adrReferences", _existing_adr_references(root), filled)

    contract_sections = fill_implementation_contract(state, source_files, filled)
    missing = [path for path in REQUIRED_PATHS if not value_at(state, path)]

    print_summary(
        context.idea_id, context.idea_files, context.session_paths, filled, missing, contract_sections, check=check
    )
    if check:
        return 0

    session_path = write_handoff_session(
        root, context.idea_id, context.idea_files, context.session_paths, filled, missing, contract_sections
    )
    fill_list(state, "artifacts.sessionFiles", context.session_paths + [session_path], filled)
    schema_result = ValidationResult()
    validate_project_state_data(root, schema_result, state, variant="draft")
    if schema_result.failures:
        raise SystemExit("\n".join(schema_result.failures))
    write_text(root / STATE_FILE, json.dumps(state, indent=2) + "\n")
    sync_code = (
        run_lab_sync(
            root,
            message=f"handoff {context.idea_id}",
            quiet=True,
            no_warn_push_failure=True,
            files=[STATE_FILE, session_path],
        )
        if not no_sync
        else 0
    )
    if sync_code not in {0, 2}:
        raise SystemExit(sync_code)
    print(f"Handoff state updated: {STATE_FILE}")
    print(f"Handoff session log: {session_path}")
    return 0


def _resolve_handoff_idea_id(root: Path, idea_id: str) -> str:
    if idea_id:
        return idea_id
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    row, source = resolved_finalize_target(root, active)
    if row is not None:
        return row["idea_id"]
    if source == "ambiguous":
        raise SystemExit("Handoff target is ambiguous. Rerun with ./scripts/lab handoff --idea-id <idea-id>.")
    raise SystemExit("No handoff target found. Capture and activate an idea first.")


def _existing_adr_references(root: Path) -> list[str]:
    candidates = [
        "docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        ".harness/brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
    ]
    return [candidate for candidate in candidates if (root / candidate).exists()]
