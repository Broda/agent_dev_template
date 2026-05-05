from __future__ import annotations

from pathlib import Path

from template_cli.finalize_helpers import (
    existing_state_value,
    files_containing,
    first_value_for_label,
    infer_project_type,
)
from template_cli.finalize_state import _write_summary_export
from template_cli.workflow_data import (
    BUCKET_FILES,
    _append_idea_to_bucket,
    _append_under_section,
    _build_idea_fields,
    _collect_session_links,
    _default_adr_references,
    _default_owner,
    _ensure_session_file,
    _extract_catalog_row,
    _extract_label_from_text,
    _find_idea_block,
    _next_sequence_id,
    _remove_idea_from_buckets,
    _render_idea_block,
    _sync,
    _title_from_idea_id,
    _today,
    _timestamp,
    _upsert_catalog_row,
)
from template_cli.io_helpers import path_exists


def run_lab_capture(
    root: Path,
    *,
    idea_id: str,
    title: str = "",
    owner: str = "",
    problem: str = "",
    summary: str = "",
    scope: str = "",
    constraints: str = "",
    no_sync: bool = False,
) -> int:
    fields = _build_idea_fields(
        root,
        idea_id,
        title=title,
        owner=owner,
        status="inbox",
        problem_statement=problem,
        solution_summary=summary,
        mvp_scope=scope,
        constraints=constraints,
    )
    block = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, "inbox", block)
    row = _extract_catalog_row(root, idea_id)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status="inbox",
        owner=fields["owner"],
        sessions=_collect_session_links(root, idea_id, row),
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES["inbox"], "IDEA_CATALOG.md"]
    sync_code = _sync(root, message=f"capture {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Idea captured: {idea_id}")
    return 0


def run_lab_activate(
    root: Path,
    *,
    idea_id: str,
    title: str = "",
    owner: str = "",
    session: str = "",
    no_sync: bool = False,
) -> int:
    current_owner = owner or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, title or _title_from_idea_id(idea_id), current_owner, session)
    row = _extract_catalog_row(root, idea_id)
    sessions = _collect_session_links(root, idea_id, row)
    if session_path not in sessions:
        sessions.append(session_path)
    fields = _build_idea_fields(
        root,
        idea_id,
        title=title,
        owner=current_owner,
        status="active",
        session_links=sessions,
    )
    block = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, "active", block)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status="active",
        owner=fields["owner"],
        sessions=sessions,
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES["active"], "IDEA_CATALOG.md", session_path]
    sync_code = _sync(root, message=f"activate {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Idea activated: {idea_id}")
    print(f"Session: {session_path}")
    return 0


def _transition_idea_state(
    root: Path,
    *,
    idea_id: str,
    status: str,
    owner: str = "",
    note: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    sessions = _collect_session_links(root, idea_id, row)
    fields = _build_idea_fields(
        root,
        idea_id,
        owner=owner or row.get("owner") or _default_owner(root),
        status=status,
        session_links=sessions,
    )
    if note:
        fields["open_questions"] = note
    block = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, status, block)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status=status,
        owner=fields["owner"],
        sessions=sessions,
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES[status], "IDEA_CATALOG.md"]
    sync_code = _sync(root, message=f"{status} {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Idea marked {status}: {idea_id}")
    return 0


def run_lab_park(root: Path, *, idea_id: str, owner: str = "", reason: str = "", no_sync: bool = False) -> int:
    return _transition_idea_state(root, idea_id=idea_id, status="parked", owner=owner, note=reason, no_sync=no_sync)


def run_lab_kill(root: Path, *, idea_id: str, owner: str = "", reason: str = "", no_sync: bool = False) -> int:
    return _transition_idea_state(root, idea_id=idea_id, status="killed", owner=owner, note=reason, no_sync=no_sync)


def run_lab_path_note(
    root: Path,
    *,
    idea_id: str,
    title: str,
    summaries: list[str] | None = None,
    deferred: str = "",
    session: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner = row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner, session)
    lines = [f"### {_timestamp()} - {title}"]
    for summary in summaries or []:
        lines.append(f"- {summary}")
    if deferred:
        lines.append(f"- Deferred/Parked rationale: {deferred}")
    _append_under_section(root / session_path, "Exploration Path Notes", "\n".join(lines))
    sync_code = _sync(root, message=f"path-note {idea_id}", files=[session_path], no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Path note saved: {session_path}")
    return 0


def run_lab_decide(
    root: Path,
    *,
    idea_id: str,
    decision_id: str = "",
    owner: str = "",
    session: str = "",
    decision_level: str = "L2",
    situation: str = "",
    chosen_option: str = "",
    rationale: str = "",
    constraints: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner_value = owner or row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner_value, session)
    decision_id = decision_id or _next_sequence_id(root, "decision")
    block = "\n".join(
        [
            f"### Decision: {decision_id}",
            "",
            f"- Decision ID: {decision_id}",
            f"- Decision level: {decision_level}",
            f"- Related Idea ID: {idea_id}",
            f"- Date: {_today()}",
            f"- Owner: {owner_value}",
            f"- Session Link: `{session_path}`",
            "- ADR Link (required for L3): ",
            f"- Situation summary: {situation}",
            f"- Constraints: {constraints}",
            f"- Chosen option: {chosen_option}",
            f"- Rationale: {rationale}",
        ]
    )
    _append_under_section(root / session_path, "Decisions", block)
    sync_code = _sync(root, message=f"decide {idea_id}", files=[session_path], no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Decision recorded: {decision_id}")
    return 0


def run_lab_risk(
    root: Path,
    *,
    idea_id: str,
    risk_id: str = "",
    owner: str = "",
    session: str = "",
    statement: str = "",
    mitigation: str = "",
    contingency: str = "",
    probability: str = "medium",
    impact: str = "medium",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner_value = owner or row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner_value, session)
    risk_id = risk_id or _next_sequence_id(root, "risk")
    block = "\n".join(
        [
            f"### Risk: {risk_id}",
            "",
            f"- Risk ID: {risk_id}",
            f"- Related Idea ID: {idea_id}",
            f"- Date: {_today()}",
            f"- Owner: {owner_value}",
            f"- Session Link: `{session_path}`",
            f"- Risk statement: {statement}",
            f"- Probability: {probability}",
            f"- Impact: {impact}",
            f"- Preventive mitigation: {mitigation}",
            f"- Contingency plan: {contingency}",
        ]
    )
    _append_under_section(root / session_path, "Risks", block)
    sync_code = _sync(root, message=f"risk {idea_id}", files=[session_path], no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Risk recorded: {risk_id}")
    return 0


def run_lab_review(
    root: Path,
    *,
    idea_id: str,
    result: str,
    owner: str = "",
    session: str = "",
    summary: str = "",
    outcome: str = "revise",
    next_action: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner_value = owner or row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner_value, session)
    block = "\n".join(
        [
            f"### Review Gate - {_today()}",
            "",
            f"- Date: {_today()}",
            f"- Owner: {owner_value}",
            f"- Idea ID: {idea_id}",
            f"- Session: `{session_path}`",
            f"- Result: {result}",
            f"- Summary rationale: {summary}",
            f"- Outcome: {outcome}",
            f"- Next action: {next_action}",
        ]
    )
    _append_under_section(root / session_path, "Review Gates", block)
    fields = _build_idea_fields(root, idea_id, owner=owner_value, status=row.get("status") or "active")
    fields["latest_review_outcome"] = result
    block_text = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, fields["status"], block_text)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status=fields["status"],
        owner=owner_value,
        sessions=_collect_session_links(root, idea_id, row) or [session_path],
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES[fields["status"]], "IDEA_CATALOG.md", session_path]
    sync_code = _sync(root, message=f"review {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Review recorded for: {idea_id}")
    return 0


def run_lab_export(root: Path, *, idea_id: str, no_sync: bool = False) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_lookup = _find_idea_block(root, idea_id)
    if idea_lookup is None:
        raise SystemExit(f"Idea '{idea_id}' not found in idea buckets.")
    idea_block = idea_lookup[1]
    session_files = _collect_session_links(root, idea_id, row)
    hydration_files = [root / rel for rel in files_containing(root, "ideas", idea_id) + session_files if path_exists(root, rel)]
    date_stamp = _today()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    state = {
        "ideaId": idea_id,
        "projectName": _extract_label_from_text(idea_block, "Title") or row.get("title") or _title_from_idea_id(idea_id),
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
