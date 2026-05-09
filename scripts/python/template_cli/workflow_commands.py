from __future__ import annotations

from pathlib import Path

from template_cli.workflow_data import (
    BUCKET_FILES,
    _append_idea_to_bucket,
    _build_idea_fields,
    _collect_session_links,
    _default_owner,
    _extract_catalog_row,
    _remove_idea_from_buckets,
    _sync,
    _title_from_idea_id,
    _today,
    _timestamp,
    _upsert_catalog_row,
)
from template_cli.workflow_sessions import _append_under_section, _ensure_session_file, _next_sequence_id
from template_cli.workflow_idea_commands import (
    run_lab_activate,
    run_lab_capture,
    run_lab_kill,
    run_lab_park,
)
from template_cli.workflow_export import run_lab_export
from template_cli.workflow_render import _render_idea_block


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
