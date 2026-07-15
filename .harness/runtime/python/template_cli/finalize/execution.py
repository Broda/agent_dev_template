from __future__ import annotations

import json
from pathlib import Path

from template_cli.brainstorming_contract import semantic_contract_failure, semantic_contract_issues
from template_cli.finalize.artifacts import (
    _backup_finalization_outputs,
    _write_finalization_session_log,
)
from template_cli.finalize.context import FinalizeContext
from template_cli.finalize.helpers import STATE_FILE
from template_cli.finalize.history import archive_brainstorming_history
from template_cli.finalize.project_settings import FinalizeProjectSettings
from template_cli.finalize.state import (
    BackupManager,
    _update_catalog_transition,
    _write_mode_development,
    _write_summary_export,
)
from template_cli.finalize.state_builder import _build_finalized_state
from template_cli.finalize.value_collection import HydratedFinalizeValues
from template_cli.io_helpers import ValidationResult, write_text
from template_cli.render import run_render_development_docs
from template_cli.state_schema import validate_project_state_data
from template_cli.validators import run_validate_development


def _write_and_validate_finalized_project(
    root: Path,
    *,
    existing_state: dict,
    date_stamp: str,
    context: FinalizeContext,
    project_name: str,
    objective: str,
    hydrated: HydratedFinalizeValues,
    settings: FinalizeProjectSettings,
    session_path: str,
    export_path: str,
    write_export: bool,
    brainstorming_contract: dict,
) -> None:
    with BackupManager(root) as backups:
        _backup_finalization_outputs(
            backups,
            session_path=session_path,
            export_path=export_path,
            write_export=write_export,
        )

        state = _build_finalized_state(
            root,
            existing_state=existing_state,
            date_stamp=date_stamp,
            idea_id=context.idea_id,
            project_name=project_name,
            owner=context.owner,
            objective=objective,
            project_type=settings.project_type,
            language=settings.language,
            runtime=settings.runtime,
            framework=settings.framework,
            package_tool=settings.package_tool,
            persistence=settings.persistence,
            authentication=settings.authentication,
            determinism=settings.determinism,
            packaging=settings.packaging,
            constraints=settings.constraints,
            build_command=settings.build_command,
            run_command=settings.run_command,
            test_command=settings.test_command,
            problem_statement=hydrated.problem_statement,
            target_users=hydrated.target_users,
            why_now=hydrated.why_now,
            expected_value=hydrated.expected_value,
            solution_summary=hydrated.solution_summary,
            mvp_scope=hydrated.mvp_scope,
            out_of_scope=hydrated.out_of_scope,
            assumptions=hydrated.assumptions,
            non_goals=hydrated.non_goals,
            key_decisions=settings.key_decisions,
            top_risks=hydrated.top_risks,
            mitigation_plans=hydrated.mitigation_plans,
            contingencies=hydrated.contingencies,
            remaining_risks=hydrated.remaining_risks,
            latest_review_outcome=hydrated.latest_review_outcome,
            latest_review_session=hydrated.latest_review_session,
            idea_files=context.idea_files,
            session_paths=context.session_paths,
            hydration_files=context.hydrate_files,
            session_path=session_path,
            notes_col=context.notes_col,
            related_note_paths=context.related_note_paths,
            export_path=export_path,
            write_export=write_export,
            brainstorming_contract=brainstorming_contract,
        )
        contract_issues = semantic_contract_issues(state)
        if contract_issues:
            raise SystemExit(semantic_contract_failure(context.idea_id, contract_issues))
        schema_result = ValidationResult()
        validate_project_state_data(root, schema_result, state, variant="finalized")
        if schema_result.failures:
            raise SystemExit("\n".join(schema_result.failures))
        write_text(root / STATE_FILE, json.dumps(state, indent=2) + "\n")
        if write_export:
            _write_summary_export(root, export_path, state)

        _update_catalog_transition(root, context.idea_id, session_path, export_path if write_export else "")
        _write_finalization_session_log(
            root,
            session_path=session_path,
            date_stamp=date_stamp,
            owner=context.owner,
            idea_id=context.idea_id,
            export_path=export_path,
            write_export=write_export,
        )

        archived_state = archive_brainstorming_history(root, state)
        schema_result = ValidationResult()
        validate_project_state_data(root, schema_result, archived_state, variant="finalized")
        if schema_result.failures:
            raise SystemExit("\n".join(schema_result.failures))
        write_text(root / STATE_FILE, json.dumps(archived_state, indent=2) + "\n")

        render_code = run_render_development_docs(root)
        if render_code != 0:
            raise SystemExit(render_code)

        _write_mode_development(root)

        validation_code = run_validate_development(root)
        if validation_code != 0:
            raise SystemExit(validation_code)

        backups.commit()
