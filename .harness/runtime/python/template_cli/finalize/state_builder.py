from __future__ import annotations

from pathlib import Path

from template_cli.finalized_contract import build_finalized_contract
from template_cli.finalize.helpers import STATE_SCHEMA_VERSION, is_placeholder_value, summarize_decisions, unique_values
from template_cli.wiki import default_wiki_config


def _build_finalized_state(
    root: Path,
    *,
    existing_state: dict,
    date_stamp: str,
    idea_id: str,
    project_name: str,
    owner: str,
    objective: str,
    project_type: str,
    language: str,
    runtime: str,
    framework: str,
    package_tool: str,
    persistence: str,
    authentication: str,
    determinism: str,
    packaging: str,
    constraints: str,
    build_command: str,
    run_command: str,
    test_command: str,
    problem_statement: str,
    target_users: str,
    why_now: str,
    expected_value: str,
    solution_summary: str,
    mvp_scope: str,
    out_of_scope: str,
    assumptions: str,
    non_goals: str,
    key_decisions: str,
    top_risks: str,
    mitigation_plans: str,
    contingencies: str,
    remaining_risks: str,
    latest_review_outcome: str,
    latest_review_session: str,
    idea_files: list[str],
    session_paths: list[str],
    hydration_files: list[Path],
    session_path: str,
    notes_col: str,
    export_path: str,
    write_export: bool,
) -> dict:
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
    documentation.setdefault(
        "ciPolicy",
        "Generated GitHub Actions CI is included as a baseline guardrail; local build, "
        "test, and manual verification remain authoritative.",
    )

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
    state["finalizedContract"] = build_finalized_contract(existing_state, state, hydration_files)
    return state
