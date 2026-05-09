from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from template_cli.finalize_context import load_finalize_context
from template_cli.finalize_artifacts import (
    _backup_finalization_outputs,
    _ensure_finalization_dirs,
    _load_existing_state,
    _write_finalization_session_log,
)
from template_cli.finalize_helpers import (
    STATE_FILE,
    ask_non_empty,
    choose_from_list,
    choose_project_type,
    existing_state_value,
    first_value_for_label,
    infer_project_type,
    is_placeholder_value,
    latest_session_path,
    summarize_decisions,
)
from template_cli.finalize_state import (
    BackupManager,
    _update_catalog_transition,
    _write_mode_development,
    _write_summary_export,
    resolve_finalize_idea_id,
)
from template_cli.finalize_state_builder import _build_finalized_state
from template_cli.finalize_validation import (
    _collect_missing_noninteractive_fields,
    _fail_noninteractive,
    _pick_noninteractive_choice,
    _required_value,
)
from template_cli.io_helpers import (
    ValidationResult,
    write_text,
)
from template_cli.render import run_render_development_docs
from template_cli.state_schema import validate_project_state_data
from template_cli.validators import (
    run_validate_development,
)


def run_finalize_project(root: Path, idea_id: str, *, write_export: bool = False, interactive: bool = False) -> int:
    idea_id = resolve_finalize_idea_id(root, idea_id, interactive=interactive)
    context = load_finalize_context(root, idea_id)
    project_name = context.project_name
    owner = context.owner
    notes_col = context.notes_col
    idea_files = context.idea_files
    session_paths = context.session_paths
    hydrate_files = context.hydrate_files

    existing_project_name = existing_state_value(root, "projectName")
    existing_purpose = existing_state_value(root, "purpose")
    existing_project_type = existing_state_value(root, "projectType")
    existing_language = existing_state_value(root, "techStack.language")
    existing_runtime = existing_state_value(root, "techStack.runtime")
    existing_framework = existing_state_value(root, "techStack.framework")
    existing_package_tool = existing_state_value(root, "techStack.packageTool")
    existing_persistence = existing_state_value(root, "persistence")
    existing_authentication = existing_state_value(root, "authentication")
    existing_determinism = existing_state_value(root, "determinism")
    existing_packaging = existing_state_value(root, "packaging")
    existing_constraints = existing_state_value(root, "constraints")
    existing_build_command = existing_state_value(root, "commands.build")
    existing_run_command = existing_state_value(root, "commands.run")
    existing_test_command = existing_state_value(root, "commands.test")
    existing_problem_statement = existing_state_value(root, "product.problemStatement")
    existing_target_users = existing_state_value(root, "product.targetUsers")
    existing_why_now = existing_state_value(root, "product.whyNow")
    existing_expected_value = existing_state_value(root, "product.expectedValue")
    existing_solution_summary = existing_state_value(root, "product.solutionSummary")
    existing_mvp_scope = existing_state_value(root, "product.mvpScope")
    existing_out_of_scope = existing_state_value(root, "product.outOfScope")
    existing_assumptions = existing_state_value(root, "product.assumptions")
    existing_non_goals = existing_state_value(root, "product.nonGoals")
    existing_key_decisions = existing_state_value(root, "governance.keyDecisions")
    existing_top_risks = existing_state_value(root, "governance.topRisks")
    existing_mitigation_plans = existing_state_value(root, "governance.mitigationPlans")
    existing_contingencies = existing_state_value(root, "governance.contingencies")
    existing_remaining_risks = existing_state_value(root, "governance.remainingAcceptedRisks")
    existing_latest_review_outcome = existing_state_value(root, "governance.latestReviewOutcome")
    existing_latest_review_session = existing_state_value(root, "governance.latestReviewSession")

    if existing_project_name:
        project_name = existing_project_name

    objective = existing_purpose or ""
    if not objective:
        for label in [
            "One-sentence objective",
            "Problem statement",
            "Value hypothesis",
            "Summary rationale",
            "Situation summary",
        ]:
            objective = first_value_for_label(hydrate_files, label)
            if objective:
                break
    missing_fields: list[str] = []
    if interactive:
        objective = ask_non_empty("One-sentence objective", objective)
    else:
        objective = _required_value(objective, "purpose / one-sentence objective", missing_fields)

    problem_statement = existing_problem_statement or first_value_for_label(hydrate_files, "Problem statement")
    target_users = existing_target_users or first_value_for_label(hydrate_files, "Affected users/personas") or first_value_for_label(
        hydrate_files, "Target users"
    )
    why_now = existing_why_now or first_value_for_label(hydrate_files, "Why now")
    expected_value = existing_expected_value or first_value_for_label(hydrate_files, "Expected value") or first_value_for_label(
        hydrate_files, "Value hypothesis"
    )
    solution_summary = existing_solution_summary or first_value_for_label(hydrate_files, "Solution summary")
    mvp_scope = existing_mvp_scope or first_value_for_label(hydrate_files, "MVP scope")
    out_of_scope = existing_out_of_scope or first_value_for_label(hydrate_files, "Out of scope")
    assumptions = existing_assumptions or first_value_for_label(hydrate_files, "Assumptions")
    non_goals = existing_non_goals or first_value_for_label(hydrate_files, "Non-goals")
    top_risks = existing_top_risks or first_value_for_label(hydrate_files, "Top risks") or first_value_for_label(
        hydrate_files, "Top risks (link to risk entries)"
    )
    mitigation_plans = existing_mitigation_plans or first_value_for_label(hydrate_files, "Mitigation plans") or first_value_for_label(
        hydrate_files, "Preventive mitigation"
    )
    contingencies = existing_contingencies or first_value_for_label(hydrate_files, "Contingency plan")
    remaining_risks = existing_remaining_risks or first_value_for_label(hydrate_files, "Remaining accepted risks")
    latest_review_outcome = existing_latest_review_outcome or first_value_for_label(hydrate_files, "Latest review outcome") or first_value_for_label(
        hydrate_files, "Result"
    )
    latest_review_session = existing_latest_review_session or latest_session_path(session_paths)

    constraints_source = existing_constraints if not is_placeholder_value(existing_constraints) else ""
    if not constraints_source:
        constraints_source = first_value_for_label(hydrate_files, "Constraints")

    if interactive:
        project_type = choose_project_type(existing_project_type or infer_project_type(project_name, objective))
        language = ask_non_empty("Language", existing_language)
        runtime = ask_non_empty("Runtime", existing_runtime)
        framework = ask_non_empty("Framework (if any, else 'None')", existing_framework or "None")
        package_tool = ask_non_empty(
            "Package manager/build tool (if any, else 'None')", existing_package_tool or "None"
        )
        persistence = choose_from_list(
            "Persistence",
            existing_persistence,
            ["None", "File-based (JSON/YAML/etc.)", "SQLite", "Postgres/MySQL/Other RDBMS"],
        )
        authentication = choose_from_list(
            "Authentication", existing_authentication, ["None", "Local users", "External auth provider"]
        )
        determinism = choose_from_list(
            "Determinism/correctness sensitivity", existing_determinism, ["Normal", "High"]
        )
        packaging = choose_from_list(
            "Packaging/distribution planned",
            existing_packaging,
            ["None", "Yes (desktop installers / containers / artifacts)"],
        )
        constraints = ask_non_empty(
            "Constraints (comma-separated; use 'None' if none)", constraints_source or "None"
        )
        build_command = ask_non_empty("Build command", existing_build_command)
        run_command = ask_non_empty("Run command", existing_run_command)
        test_command = ask_non_empty("Test command", existing_test_command)
    else:
        project_type = _pick_noninteractive_choice(
            existing_project_type or infer_project_type(project_name, objective),
            "project type",
            missing_fields,
        )
        language = _required_value(existing_language, "language", missing_fields)
        runtime = _required_value(existing_runtime, "runtime", missing_fields)
        framework = _required_value(existing_framework or "None", "framework", missing_fields)
        package_tool = _required_value(existing_package_tool or "None", "package manager/build tool", missing_fields)
        persistence = _pick_noninteractive_choice(existing_persistence, "persistence", missing_fields)
        authentication = _pick_noninteractive_choice(existing_authentication, "authentication", missing_fields)
        determinism = _pick_noninteractive_choice(existing_determinism, "determinism/correctness sensitivity", missing_fields)
        packaging = _pick_noninteractive_choice(existing_packaging, "packaging/distribution planned", missing_fields)
        constraints = _required_value(constraints_source or "None", "constraints", missing_fields)
        build_command = _required_value(existing_build_command, "build command", missing_fields)
        run_command = _required_value(existing_run_command, "run command", missing_fields)
        test_command = _required_value(existing_test_command, "test command", missing_fields)

        _collect_missing_noninteractive_fields(root, hydrate_files, session_paths, missing_fields)
        if missing_fields:
            _fail_noninteractive(missing_fields, idea_id)
    key_decisions = existing_key_decisions or summarize_decisions(
        project_type, persistence, authentication, determinism, packaging
    )

    date_stamp = date.today().isoformat()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    session_path = f"sessions/{date_stamp}_FINALIZATION_SESSION_{idea_id}.md"

    _ensure_finalization_dirs(root, write_export=write_export)
    existing_state = _load_existing_state(root)

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
            idea_id=idea_id,
            project_name=project_name,
            owner=owner,
            objective=objective,
            project_type=project_type,
            language=language,
            runtime=runtime,
            framework=framework,
            package_tool=package_tool,
            persistence=persistence,
            authentication=authentication,
            determinism=determinism,
            packaging=packaging,
            constraints=constraints,
            build_command=build_command,
            run_command=run_command,
            test_command=test_command,
            problem_statement=problem_statement,
            target_users=target_users,
            why_now=why_now,
            expected_value=expected_value,
            solution_summary=solution_summary,
            mvp_scope=mvp_scope,
            out_of_scope=out_of_scope,
            assumptions=assumptions,
            non_goals=non_goals,
            key_decisions=key_decisions,
            top_risks=top_risks,
            mitigation_plans=mitigation_plans,
            contingencies=contingencies,
            remaining_risks=remaining_risks,
            latest_review_outcome=latest_review_outcome,
            latest_review_session=latest_review_session,
            idea_files=idea_files,
            session_paths=session_paths,
            session_path=session_path,
            notes_col=notes_col,
            export_path=export_path,
            write_export=write_export,
        )
        schema_result = ValidationResult()
        validate_project_state_data(root, schema_result, state, variant="finalized")
        if schema_result.failures:
            raise SystemExit("\n".join(schema_result.failures))
        write_text(root / STATE_FILE, json.dumps(state, indent=2) + "\n")
        if write_export:
            _write_summary_export(root, export_path, state)

        render_code = run_render_development_docs(root)
        if render_code != 0:
            raise SystemExit(render_code)

        _update_catalog_transition(root, idea_id, session_path, export_path if write_export else "")
        _write_mode_development(root)

        _write_finalization_session_log(
            root,
            session_path=session_path,
            date_stamp=date_stamp,
            owner=owner,
            idea_id=idea_id,
            export_path=export_path,
            write_export=write_export,
        )

        validation_code = run_validate_development(root)
        if validation_code != 0:
            raise SystemExit(validation_code)

        backups.commit()

    print(f"Canonical state saved: {STATE_FILE}")
    print(f"Finalization session log: {session_path}")
    if write_export:
        print(f"Optional project summary written: {export_path}")
    print("The repository has been successfully finalized into development mode.")
    return 0
