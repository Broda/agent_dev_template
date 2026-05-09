from __future__ import annotations

from datetime import date
from pathlib import Path

from template_cli.finalize_context import load_finalize_context
from template_cli.finalize_artifacts import (
    _ensure_finalization_dirs,
    _load_existing_state,
)
from template_cli.finalize_helpers import (
    ask_non_empty,
)
from template_cli.finalize_existing import _load_existing_finalize_values
from template_cli.finalize_execution import _write_and_validate_finalized_project
from template_cli.finalize_project_settings import _collect_finalize_project_settings
from template_cli.finalize_state import (
    resolve_finalize_idea_id,
)
from template_cli.finalize_output import _print_finalization_result
from template_cli.finalize_validation import (
    _collect_missing_noninteractive_fields,
    _fail_noninteractive,
    _required_value,
)
from template_cli.finalize_value_collection import _hydrate_finalize_values


def run_finalize_project(root: Path, idea_id: str, *, write_export: bool = False, interactive: bool = False) -> int:
    idea_id = resolve_finalize_idea_id(root, idea_id, interactive=interactive)
    context = load_finalize_context(root, idea_id)
    project_name = context.project_name
    session_paths = context.session_paths
    hydrate_files = context.hydrate_files

    existing = _load_existing_finalize_values(root)

    if existing.project_name:
        project_name = existing.project_name

    hydrated = _hydrate_finalize_values(existing, hydrate_files, session_paths)
    objective = hydrated.objective
    missing_fields: list[str] = []
    if interactive:
        objective = ask_non_empty("One-sentence objective", objective)
    else:
        objective = _required_value(objective, "purpose / one-sentence objective", missing_fields)

    settings = _collect_finalize_project_settings(
        existing,
        project_name=project_name,
        objective=objective,
        constraints_source=hydrated.constraints_source,
        interactive=interactive,
        missing_fields=missing_fields,
    )
    if not interactive:
        _collect_missing_noninteractive_fields(root, hydrate_files, session_paths, missing_fields)
        if missing_fields:
            _fail_noninteractive(missing_fields, idea_id)

    date_stamp = date.today().isoformat()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    session_path = f"sessions/{date_stamp}_FINALIZATION_SESSION_{idea_id}.md"

    _ensure_finalization_dirs(root, write_export=write_export)
    existing_state = _load_existing_state(root)

    _write_and_validate_finalized_project(
        root,
        existing_state=existing_state,
        date_stamp=date_stamp,
        context=context,
        project_name=project_name,
        objective=objective,
        hydrated=hydrated,
        settings=settings,
        session_path=session_path,
        export_path=export_path,
        write_export=write_export,
    )

    _print_finalization_result(session_path, export_path, write_export=write_export)
    return 0
