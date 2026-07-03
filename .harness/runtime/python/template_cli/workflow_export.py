from __future__ import annotations

from pathlib import Path

from template_cli.finalize.helpers import (
    existing_state_value,
    files_containing,
    first_value_for_label,
    infer_project_type,
)
from template_cli.finalize.state import _write_summary_export
from template_cli.io_helpers import path_exists
from template_cli.workflow_catalog import _extract_catalog_row, _upsert_catalog_row
from template_cli.workflow_data import (
    BUCKET_FILES,
    _append_idea_to_bucket,
    _build_idea_fields,
    _collect_session_links,
    _default_adr_references,
    _default_owner,
    _extract_label_from_text,
    _find_idea_block,
    _remove_idea_from_buckets,
    _sync,
    _title_from_idea_id,
    _today,
)
from template_cli.workflow_render import _render_idea_block


def run_lab_export(root: Path, *, idea_id: str, no_sync: bool = False) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_lookup = _find_idea_block(root, idea_id)
    if idea_lookup is None:
        raise SystemExit(f"Idea '{idea_id}' not found in idea buckets.")
    idea_block = idea_lookup[1]
    session_files = _collect_session_links(root, idea_id, row)
    hydration_files = [
        root / rel for rel in files_containing(root, "ideas", idea_id) + session_files if path_exists(root, rel)
    ]
    date_stamp = _today()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    state = {
        "ideaId": idea_id,
        "projectName": _extract_label_from_text(idea_block, "Title")
        or row.get("title")
        or _title_from_idea_id(idea_id),
        "owner": _extract_label_from_text(idea_block, "Owner") or row.get("owner") or _default_owner(root),
        "finalizedAt": date_stamp,
        "purpose": first_value_for_label(hydration_files, "Problem statement")
        or first_value_for_label(hydration_files, "Value hypothesis")
        or "See related idea and session records.",
        "projectType": existing_state_value(root, "projectType")
        or infer_project_type(
            _extract_label_from_text(idea_block, "Title") or _title_from_idea_id(idea_id),
            first_value_for_label(hydration_files, "Problem statement"),
        )
        or "Unspecified",
        "techStack": {
            "language": existing_state_value(root, "techStack.language") or "Not captured yet",
            "runtime": existing_state_value(root, "techStack.runtime") or "Not captured yet",
            "framework": existing_state_value(root, "techStack.framework") or "None",
            "packageTool": existing_state_value(root, "techStack.packageTool") or "None",
        },
        "commands": {
            "build": existing_state_value(root, "commands.build") or "Not captured yet",
            "run": existing_state_value(root, "commands.run") or "Not captured yet",
            "test": existing_state_value(root, "commands.test") or "Not captured yet",
        },
        "product": {
            "problemStatement": _extract_label_from_text(idea_block, "Problem statement"),
            "targetUsers": _extract_label_from_text(idea_block, "Affected users/personas"),
            "whyNow": _extract_label_from_text(idea_block, "Why now"),
            "expectedValue": _extract_label_from_text(idea_block, "Value hypothesis"),
            "solutionSummary": _extract_label_from_text(idea_block, "Value hypothesis"),
            "mvpScope": _extract_label_from_text(idea_block, "MVP scope"),
            "outOfScope": _extract_label_from_text(idea_block, "Out of scope"),
            "assumptions": _extract_label_from_text(idea_block, "Assumptions"),
            "nonGoals": _extract_label_from_text(idea_block, "Non-goals"),
        },
        "governance": {
            "keyDecisions": _extract_label_from_text(idea_block, "Related decisions"),
            "topRisks": _extract_label_from_text(idea_block, "Top risks (link to risk entries)"),
            "mitigationPlans": first_value_for_label(hydration_files, "Preventive mitigation"),
            "contingencies": first_value_for_label(hydration_files, "Contingency plan"),
            "remainingAcceptedRisks": "See related sessions",
            "latestReviewOutcome": _extract_label_from_text(idea_block, "Latest review outcome"),
            "latestReviewSession": session_files[-1] if session_files else "",
        },
        "artifacts": {
            "ideaFiles": files_containing(root, "ideas", idea_id),
            "sessionFiles": session_files,
            "noteReferences": row.get("notes", "_none_"),
            "summaryExport": export_path,
            "finalizationSession": existing_state_value(root, "artifacts.finalizationSession"),
            "adrReferences": _default_adr_references(root),
        },
        "constraints": _extract_label_from_text(idea_block, "Constraints") or "None recorded",
        "persistence": existing_state_value(root, "persistence") or "None",
        "authentication": existing_state_value(root, "authentication") or "None",
        "determinism": existing_state_value(root, "determinism") or "Normal",
        "packaging": existing_state_value(root, "packaging") or "None",
    }
    (root / "exports").mkdir(parents=True, exist_ok=True)
    _write_summary_export(root, export_path, state)
    fields = _build_idea_fields(root, idea_id, summary_export=export_path, status=row.get("status") or "active")
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, fields["status"], _render_idea_block(fields))
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status=fields["status"],
        owner=fields["owner"],
        sessions=session_files,
        summary_export=export_path,
        notes=row.get("notes", "_none_"),
    )
    changed = ["exports/" + Path(export_path).name, BUCKET_FILES[fields["status"]], "IDEA_CATALOG.md"]
    sync_code = _sync(root, message=f"export {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Summary snapshot created: {export_path}")
    return 0
