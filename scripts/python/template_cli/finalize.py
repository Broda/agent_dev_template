from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from template_cli.finalize_context import load_finalize_context
from template_cli.finalize_helpers import (
    STATE_FILE,
    STATE_SCHEMA_VERSION,
    ask_non_empty,
    choose_from_list,
    choose_project_type,
    existing_state_value,
    first_value_for_label,
    infer_project_type,
    is_placeholder_value,
    join_lines,
    latest_session_path,
    summarize_decisions,
    trim,
    unique_values,
)
from template_cli.workflow_data import FINALIZE_REQUIRED_FIELDS
from template_cli.finalize_state import (
    BackupManager,
    _update_catalog_transition,
    _write_mode_development,
    _write_summary_export,
    resolve_finalize_idea_id,
)
from template_cli.io_helpers import (
    ValidationResult,
    read_text,
    write_text,
)
from template_cli.render import run_render_development_docs
from template_cli.state_schema import validate_project_state_data
from template_cli.validators import (
    run_validate_development,
)
from template_cli.wiki import default_wiki_config


def _required_value(value: str, field: str, missing: list[str]) -> str:
    value = trim(value)
    if not value:
        missing.append(field)
    return value


def _fail_noninteractive(missing: list[str], idea_id: str) -> None:
    unique_missing = unique_values(missing)
    lines = [
        "Cannot finalize non-interactively because required fields are missing.",
        f"Idea ID: {idea_id}",
        "Missing fields:",
    ]
    lines.extend(f"- {field}" for field in unique_missing)
    lines.append("Next step: update state/project-init.json or the active idea/session, then rerun ./scripts/lab doctor.")
    lines.append("Use --interactive to fill missing values with prompts.")
    raise SystemExit("\n".join(lines))


def _pick_noninteractive_choice(value: str, field: str, missing: list[str]) -> str:
    return _required_value(value, field, missing)


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

        if not session_paths:
            missing_fields.append("session history")
        for display_name, state_keys, label in FINALIZE_REQUIRED_FIELDS:
            if display_name in {"build command", "run command", "test command"}:
                continue
            value = ""
            for state_key in state_keys:
                value = existing_state_value(root, state_key)
                if value and not is_placeholder_value(value):
                    break
            if not value and label:
                value = first_value_for_label(hydrate_files, label)
            if not value or is_placeholder_value(value):
                missing_fields.append(display_name)
        if missing_fields:
            _fail_noninteractive(missing_fields, idea_id)
    key_decisions = existing_key_decisions or summarize_decisions(
        project_type, persistence, authentication, determinism, packaging
    )

    date_stamp = date.today().isoformat()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    session_path = f"sessions/{date_stamp}_FINALIZATION_SESSION_{idea_id}.md"

    (root / "sessions").mkdir(parents=True, exist_ok=True)
    if write_export:
        (root / "exports").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "docs/adr").mkdir(parents=True, exist_ok=True)

    existing_state: dict = {}
    state_path = root / STATE_FILE
    if state_path.exists():
        try:
            existing_state = json.loads(read_text(state_path))
        except json.JSONDecodeError:
            existing_state = {}

    with BackupManager(root) as backups:
        for relative_path in [
            STATE_FILE,
            "README.md",
            "CHANGELOG.md",
            ".gitignore",
            "docs/PROJECT_CONTEXT.md",
            "docs/ROADMAP.md",
            "docs/ARCHITECTURE.md",
            "docs/FILE_MAP.md",
            "docs/GOVERNANCE_INDEX.md",
            "docs/VERSIONING_AND_RELEASE_POLICY.md",
            "docs/SECURITY_POLICY.md",
            "docs/RUNTIME_VERIFICATION_REPORT.md",
            "docs/MIGRATION_POLICY.md",
            "docs/adr/ADR-0001-record-architecture-decisions.md",
            "docs/adr/ADR-TEMPLATE.md",
            ".github/workflows/ci.yml",
            "IDEA_CATALOG.md",
            "MODE.md",
            session_path,
        ]:
            backups.backup_path(relative_path)
        if write_export:
            backups.backup_path(export_path)

        existing_artifacts = existing_state.get("artifacts", {}) if isinstance(existing_state, dict) else {}
        preserved_note_references = str(existing_artifacts.get("noteReferences", "") or "").strip()
        preserved_summary_export = str(existing_artifacts.get("summaryExport", "") or "").strip()
        preserved_adr_references = existing_artifacts.get("adrReferences", [])
        if not isinstance(preserved_adr_references, list):
            preserved_adr_references = []
        preserved_documentation = existing_state.get("documentation", {}) if isinstance(existing_state, dict) else {}
        if not isinstance(preserved_documentation, dict):
            preserved_documentation = {}
        documentation = dict(preserved_documentation)
        wiki_config = default_wiki_config(root)
        existing_wiki_config = documentation.get("wiki", {})
        if isinstance(existing_wiki_config, dict):
            wiki_config.update(existing_wiki_config)
        documentation["wiki"] = wiki_config

        adr_references = unique_values(
            list(preserved_adr_references) + ["docs/adr/ADR-0001-record-architecture-decisions.md"]
        )

        effective_note_references = notes_col
        if is_placeholder_value(effective_note_references) or effective_note_references.lower() in {
            "none recorded",
            "_none_",
            "_n/a_",
            "_none yet_",
        }:
            effective_note_references = preserved_note_references

        state = {
            "schemaVersion": STATE_SCHEMA_VERSION,
            "status": "finalized",
            "finalizedAt": date_stamp,
            "ideaId": idea_id,
            "projectName": project_name,
            "owner": owner,
            "purpose": objective,
            "projectType": project_type,
            "techStack": {
                "language": language,
                "runtime": runtime,
                "framework": framework,
                "packageTool": package_tool,
            },
            "persistence": persistence,
            "authentication": authentication,
            "determinism": determinism,
            "packaging": packaging,
            "constraints": constraints,
            "commands": {
                "build": build_command,
                "run": run_command,
                "test": test_command,
            },
            "documentation": documentation,
            "product": {
                "problemStatement": problem_statement or objective,
                "targetUsers": target_users or "See related sessions",
                "whyNow": why_now or "See related sessions",
                "expectedValue": expected_value or objective,
                "solutionSummary": solution_summary or f"Deliver the first implementation slice for {project_name}.",
                "mvpScope": mvp_scope or "Milestone 0 implementation slice with working build, run, and test commands.",
                "outOfScope": out_of_scope or "See roadmap and follow-up sessions.",
                "assumptions": assumptions,
                "nonGoals": non_goals,
            },
            "governance": {
                "keyDecisions": key_decisions
                or summarize_decisions(project_type, persistence, authentication, determinism, packaging),
                "topRisks": top_risks or "Capture implementation risks during Milestone 0 execution.",
                "mitigationPlans": mitigation_plans
                or "Keep scope narrow, validate early, and update governance on change.",
                "contingencies": contingencies or "Reduce scope and re-baseline roadmap if assumptions fail.",
                "remainingAcceptedRisks": remaining_risks or "None recorded at finalization time.",
                "latestReviewOutcome": latest_review_outcome or "conditional-pass",
                "latestReviewSession": latest_review_session,
            },
            "artifacts": {
                "ideaFiles": unique_values(idea_files),
                "sessionFiles": unique_values(session_paths + [session_path]),
                "noteReferences": effective_note_references or "None recorded",
                "summaryExport": export_path if write_export else preserved_summary_export,
                "finalizationSession": session_path,
                "adrReferences": adr_references,
            },
        }
        for detail_key in ["implementation", "mvpContract"]:
            existing_detail = existing_state.get(detail_key) if isinstance(existing_state, dict) else None
            if isinstance(existing_detail, dict) and existing_detail:
                state[detail_key] = existing_detail
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

        session_lines = [
            "# Finalization Session",
            "",
            f"- Date: {date_stamp}",
            f"- Owner: {owner}",
            f"- Idea ID: {idea_id}",
            f"- Session: {session_path}",
            f"- Canonical state: `{STATE_FILE}`",
        ]
        if write_export:
            session_lines.append(f"- Summary export: `{export_path}`")
        session_content = join_lines(session_lines) + "\n\n"
        session_content += (
            "- Result: in-place mode switch completed\n\n"
            "The repository has been successfully finalized into development mode.\n"
        )
        write_text(root / session_path, session_content)

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
