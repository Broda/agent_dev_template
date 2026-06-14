from __future__ import annotations

import json
import sys
from pathlib import Path

from template_cli.external_idea import (
    ExternalIdeaImportResult,
    ExternalIdeaPayload,
    external_idea_error_code,
    external_idea_error_json,
    load_external_idea_payload,
)
from template_cli.workflow_catalog import _extract_catalog_row, _upsert_catalog_row
from template_cli.workflow_data import (
    BUCKET_FILES,
    _append_idea_to_bucket,
    _build_idea_fields,
    _collect_session_links,
    _default_owner,
    _remove_idea_from_buckets,
    _sync,
    _title_from_idea_id,
    normalize_idea_id,
)
from template_cli.workflow_render import _render_idea_block
from template_cli.workflow_sessions import _append_under_section, _ensure_session_file


def import_external_idea(
    root: Path,
    payload: ExternalIdeaPayload,
    *,
    activate: bool = True,
    create_session: bool = True,
    path_note: str = "",
    no_sync: bool = False,
) -> ExternalIdeaImportResult:
    idea_id = payload.normalized_idea_id
    owner = _default_owner(root)
    status = "active" if activate else "inbox"
    session_path = ""
    row = _extract_catalog_row(root, idea_id)
    sessions = _collect_session_links(root, idea_id, row)
    if create_session or activate or path_note:
        session_path = _ensure_session_file(root, idea_id, payload.title, owner, "")
        if session_path not in sessions:
            sessions.append(session_path)
    fields = _build_idea_fields(
        root,
        idea_id,
        title=payload.title,
        owner=owner,
        status=status,
        solution_summary=payload.summary,
        session_links=sessions,
    )
    if payload.source or payload.source_id:
        provenance = f"Imported from {payload.source}"
        if payload.source_id:
            provenance = f"{provenance} ({payload.source_id})"
        fields["open_questions"] = provenance
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
    if session_path:
        if path_note:
            lines = [f"### External import - {payload.title}", f"- Source: {payload.source}"]
            if payload.source_id:
                lines.append(f"- Source ID: {payload.source_id}")
            if payload.summary:
                lines.append(f"- Summary: {payload.summary}")
            lines.append(f"- Note: {path_note}")
            _append_under_section(root / session_path, "Exploration Path Notes", "\n".join(lines))
        changed.append(session_path)
    sync_code = _sync(root, message=f"import external idea {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    return ExternalIdeaImportResult(
        ok=True,
        idea_id=idea_id,
        title=payload.title,
        status=status,
        source=payload.source,
        source_id=payload.source_id,
        session_path=session_path,
        changed_files=changed,
        readiness="needs-input",
    )


def run_lab_import_idea(
    root: Path,
    *,
    idea_id: str = "",
    title: str = "",
    summary: str = "",
    source: str = "external",
    source_id: str = "",
    payload_file: str = "",
    activate: bool = False,
    create_session: bool = False,
    path_note: str = "",
    no_sync: bool = False,
    json_output: bool = False,
) -> int:
    try:
        if payload_file:
            payload = load_external_idea_payload(Path(payload_file).expanduser())
        else:
            payload = ExternalIdeaPayload(
                idea_id=idea_id,
                title=title,
                summary=summary,
                source=source,
                source_id=source_id,
            )
        result = import_external_idea(
            root,
            payload,
            activate=activate,
            create_session=create_session,
            path_note=path_note,
            no_sync=no_sync,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        code = external_idea_error_code(error)
        if json_output:
            print(json.dumps(external_idea_error_json(code, str(error)), sort_keys=True))
        else:
            print(f"External idea import failed [{code}]: {error}", file=sys.stderr)
        return 1
    if json_output:
        print(json.dumps(result.to_json_dict(), sort_keys=True))
    else:
        print(f"External idea imported: {result.idea_id}")
        if result.session_path:
            print(f"Session: {result.session_path}")
    return 0


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
    idea_id = normalize_idea_id(idea_id)
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
    idea_id = normalize_idea_id(idea_id)
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
    idea_id = normalize_idea_id(idea_id)
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
