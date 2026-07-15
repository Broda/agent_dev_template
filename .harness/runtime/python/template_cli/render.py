from __future__ import annotations

import shutil
from pathlib import Path

from template_cli.io_helpers import read_text, write_text
from template_cli.render_capabilities import (
    active_milestone_name,
    contract_list,
    contract_milestones,
    effective_deferred_scope,
    milestone_summary_lines,
    project_profile,
    structured_domain_concepts,
)
from template_cli.render_ci import render_development_ci
from template_cli.render_contract import collect_implementation_contract
from template_cli.render_governance_templates import _render_architecture, _render_decision_adr, _render_roadmap
from template_cli.render_helpers import (
    DEFAULT_CI_POLICY,
    MILESTONE_NAME,
    _append_unique_lines,
    _copy_base_if_missing,
    _extract_value,
    _first_value_for_label,
    _infer_domain_concepts,
    _load_state,
    _related_hydration_files_from_state,
    _render_artifact_source_table,
    _replace_file_literals,
    _state_value,
    _write_rendered_text,
)
from template_cli.render_policy_docs import apply_capability_policy_docs
from template_cli.render_templates import _render_project_context, _render_readme


def run_render_development_docs(root: Path) -> int:
    state = _load_state(root)

    project_name = _extract_value(state, "projectName")
    purpose = _extract_value(state, "purpose")
    project_type = _extract_value(state, "projectType")
    idea_id = _extract_value(state, "ideaId")
    language = _extract_value(state, "techStack.language")
    runtime = _extract_value(state, "techStack.runtime")
    framework = str(state.get("techStack", {}).get("framework", "") or "None")
    package_tool = str(state.get("techStack", {}).get("packageTool", "") or "None")
    persistence = str(state.get("persistence", "") or "")
    authentication = str(state.get("authentication", "") or "")
    packaging = str(state.get("packaging", "") or "")
    constraints = str(state.get("constraints", "") or "")
    build_command = _extract_value(state, "commands.build")
    run_command = _extract_value(state, "commands.run")
    test_command = _extract_value(state, "commands.test")
    hydration_files = _related_hydration_files_from_state(root, state, idea_id)
    problem_statement = (
        _state_value(state, "product.problemStatement")
        or _first_value_for_label(hydration_files, ["Problem statement"])
        or purpose
    )
    target_users = (
        _state_value(state, "product.targetUsers")
        or _first_value_for_label(hydration_files, ["Target users", "Affected users/personas"])
        or "Users validated during brainstorming"
    )
    solution_summary = (
        _state_value(state, "product.solutionSummary")
        or _first_value_for_label(hydration_files, ["Solution summary"])
        or purpose
    )
    mvp_scope = (
        _state_value(state, "product.mvpScope")
        or _first_value_for_label(hydration_files, ["MVP scope"])
        or "Capture milestone scope in ROADMAP.md."
    )
    out_of_scope = (
        _state_value(state, "product.outOfScope")
        or _first_value_for_label(hydration_files, ["Out of scope"])
        or "Track non-goals explicitly."
    )
    key_decisions = _state_value(state, "governance.keyDecisions") or "See canonical state and related sessions."
    top_risks = (
        _state_value(state, "governance.topRisks")
        or _first_value_for_label(hydration_files, ["Top risks", "Top risks (link to risk entries)"])
        or "Capture implementation risks during the first milestone."
    )
    mitigation_plans = (
        _state_value(state, "governance.mitigationPlans") or "Validate early and keep milestone scope narrow."
    )
    contingencies = (
        _state_value(state, "governance.contingencies") or "Reduce scope and re-baseline roadmap if assumptions fail."
    )
    latest_review_outcome = _state_value(state, "governance.latestReviewOutcome") or "conditional-pass"
    ci_policy = _state_value(state, "documentation.ciPolicy") or DEFAULT_CI_POLICY
    session_files = [str(item) for item in state.get("artifacts", {}).get("sessionFiles", []) if str(item).strip()]
    profile = project_profile(state)
    inferred_concepts = _infer_domain_concepts(" ".join([purpose, problem_statement, solution_summary, mvp_scope]))
    domain_concepts = structured_domain_concepts(state) or inferred_concepts
    implementation_contract = collect_implementation_contract(state, hydration_files)
    milestones = contract_milestones(state)
    deferred_scope = effective_deferred_scope(state)
    public_contracts = contract_list(state, "publicContracts")
    invariants = contract_list(state, "invariants")
    active_milestone = active_milestone_name(state)

    _copy_base_if_missing(root, ".harness/development/templates/docs/FILE_MAP.base.md", "docs/FILE_MAP.md")
    _copy_base_if_missing(
        root, ".harness/development/templates/docs/GOVERNANCE_INDEX.base.md", "docs/GOVERNANCE_INDEX.md"
    )
    _copy_base_if_missing(
        root,
        ".harness/development/templates/docs/VERSIONING_AND_RELEASE_POLICY.base.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
    )
    _copy_base_if_missing(
        root, ".harness/development/templates/docs/SECURITY_POLICY.base.md", "docs/SECURITY_POLICY.md"
    )
    _copy_base_if_missing(
        root,
        ".harness/development/templates/docs/RUNTIME_VERIFICATION_REPORT.base.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
    )
    _copy_base_if_missing(root, ".harness/development/templates/docs/adr/ADR-TEMPLATE.md", "docs/adr/ADR-TEMPLATE.md")
    _copy_base_if_missing(root, ".harness/development/templates/docs/CHANGELOG.base.md", "CHANGELOG.md")

    migration_policy_path = root / "docs/MIGRATION_POLICY.md"
    if persistence and persistence != "None":
        _copy_base_if_missing(
            root, ".harness/development/templates/docs/MIGRATION_POLICY.base.md", "docs/MIGRATION_POLICY.md"
        )
    elif migration_policy_path.exists():
        migration_policy_path.unlink()

    lc_lang = language.lower()
    if "python" in lc_lang:
        shutil.copyfile(root / ".harness/development/templates/gitignore/python.gitignore", root / ".gitignore")
    elif any(token in lc_lang for token in ("node", "javascript", "typescript")):
        shutil.copyfile(root / ".harness/development/templates/gitignore/node.gitignore", root / ".gitignore")
    elif any(token in lc_lang for token in ("c#", "dotnet", ".net")):
        shutil.copyfile(root / ".harness/development/templates/gitignore/dotnet.gitignore", root / ".gitignore")
    else:
        shutil.copyfile(root / ".harness/development/templates/gitignore/generic.gitignore", root / ".gitignore")

    if persistence and persistence != "None":
        _append_unique_lines(root / ".gitignore", ["*.db", "*.sqlite", "*.sqlite3"])

    _write_rendered_text(
        root,
        ".github/workflows/ci.yml",
        render_development_ci(language, runtime, package_tool, build_command, test_command),
    )

    shared_replacements = [
        ("<Project Name>", project_name),
        ("<Milestone Name>", MILESTONE_NAME),
        ("<Build command>", build_command),
        ("<Run command>", run_command),
        ("<Test command>", test_command),
        (
            "<Rendered artifact source table>",
            _render_artifact_source_table(bool(persistence and persistence != "None")),
        ),
    ]

    for relative_path in [
        "docs/FILE_MAP.md",
        "docs/GOVERNANCE_INDEX.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
        "docs/SECURITY_POLICY.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
        "docs/adr/ADR-TEMPLATE.md",
    ]:
        _replace_file_literals(root / relative_path, shared_replacements)
    apply_capability_policy_docs(root, profile)

    _write_rendered_text(
        root,
        "README.md",
        _render_readme(
            project_name,
            purpose,
            language,
            runtime,
            framework,
            package_tool,
            build_command,
            run_command,
            test_command,
            solution_summary,
            mvp_scope,
            active_milestone,
            public_contracts,
            deferred_scope,
        ),
    )
    _write_rendered_text(
        root,
        "docs/PROJECT_CONTEXT.md",
        _render_project_context(
            project_name,
            purpose,
            project_type,
            language,
            runtime,
            framework,
            package_tool,
            persistence or "None",
            authentication or "None",
            packaging or "None",
            problem_statement,
            target_users,
            solution_summary,
            mvp_scope,
            out_of_scope,
            constraints or "None recorded",
            key_decisions,
            top_risks,
            mitigation_plans,
            contingencies,
            latest_review_outcome,
            ci_policy,
            build_command,
            run_command,
            test_command,
            active_milestone,
            invariants,
            milestone_summary_lines(state),
            deferred_scope,
        ),
    )
    _write_rendered_text(
        root,
        "docs/ARCHITECTURE.md",
        _render_architecture(
            project_name,
            project_type,
            language,
            runtime,
            framework,
            persistence or "None",
            authentication or "None",
            packaging or "None",
            solution_summary,
            constraints or "None recorded",
            domain_concepts,
            implementation_contract,
            profile,
            deferred_scope,
        ),
    )
    _write_rendered_text(
        root,
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        _render_decision_adr(
            project_name,
            purpose,
            key_decisions,
            top_risks,
            mitigation_plans,
            contingencies,
            latest_review_outcome,
            session_files,
            implementation_contract,
        ),
    )
    _write_rendered_text(
        root,
        "docs/ROADMAP.md",
        _render_roadmap(
            project_name,
            build_command,
            run_command,
            test_command,
            solution_summary,
            mvp_scope,
            top_risks,
            domain_concepts,
            implementation_contract,
            profile,
            milestones,
            deferred_scope,
        ),
    )
    _replace_file_literals(
        root / "docs/RUNTIME_VERIFICATION_REPORT.md",
        [
            ("<build command>", build_command),
            ("<test command>", test_command),
            ("<run command>", run_command),
        ],
    )

    changelog_path = root / "CHANGELOG.md"
    changelog_content = read_text(changelog_path)
    marker = "## [Unreleased]"
    initial_entry = "- Initialized Structured Mode governance baseline from brainstorming finalization."
    if marker in changelog_content and initial_entry not in changelog_content:
        changelog_content = changelog_content.replace(
            marker,
            marker + f"\n\n### Added\n{initial_entry}",
            1,
        )
    write_text(changelog_path, changelog_content)

    return 0
