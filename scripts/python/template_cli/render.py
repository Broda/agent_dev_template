from __future__ import annotations

import shutil
from pathlib import Path

from template_cli.render_helpers import (
    MILESTONE_NAME,
    STATE_FILE,
    RenderError,
    _append_unique_lines,
    _copy_base,
    _extract_value,
    _first_value_for_label,
    _infer_domain_concepts,
    _load_state,
    _related_hydration_files_from_state,
    _replace_file_literals,
    _state_value,
)
from template_cli.render_templates import _render_project_context, _render_readme
from template_cli.io_helpers import read_text, write_text


def _render_architecture(
    project_name: str,
    project_type: str,
    language: str,
    runtime: str,
    framework: str,
    persistence: str,
    authentication: str,
    packaging: str,
    solution_summary: str,
    constraints: str,
    domain_concepts: list[str],
) -> str:
    concept_lines = "\n".join(f"- {concept}" for concept in domain_concepts)
    return f"""# ARCHITECTURE.md — Structured Mode v2

This document defines structure and boundaries.

---

# 1. Design Goals

- Deliver the first {project_name} implementation slice with clear boundaries.
- Keep infrastructure replaceable without rewriting domain logic.
- Preserve deterministic and testable business rules.
- Maintain stable public contracts.
- Support long-term maintainability and controlled expansion.

---

# 2. Planned System Shape

- Project type: {project_type}
- Primary implementation stack: {language} on {runtime}
- Interface stack: {framework}
- Persistence layer: {persistence}
- Authentication: {authentication}
- Packaging/distribution: {packaging}
- Product summary: {solution_summary}

---

# 3. Major Surfaces

- User-facing or operator-facing interfaces for the current milestone.
- Administrative or editor workflows for controlled mutation paths.
- Backend application services that keep business rules authoritative.
- Persistence and infrastructure services that support runtime state, history, and deployment needs.

Constraints to preserve:

- {constraints}

---

# 4. Layer Model

Interface
→ Application
→ Domain/Core
→ Persistence
→ Infrastructure

---

# 5. Domain Areas

{concept_lines}

---

# 6. Layer Responsibilities

## Interface Layer

- Web UI, admin UI, API handlers, and transport DTOs
- Basic input validation and presentation logic

Must NOT:
- Contain business rules
- Access storage directly

---

## Application Layer

- Orchestrates use cases, workflows, and transaction boundaries
- Coordinates domain services and repositories
- Defines transaction boundaries and workflow sequencing

---

## Domain Layer

- Pure business logic
- Deterministic calculations where possible
- Framework-agnostic rules derived from the finalized product plan
- Unit-testable behavior with no I/O

---

## Persistence Layer

- Repository interfaces and implementations
- Data mapping between runtime models and storage
- Schema and migration boundaries

---

## Infrastructure

- Database, network, files, secrets, deployment runtime, and external integrations

---

# 7. Public Contracts

Public contracts include:

- API endpoints
- DTO structures
- Surface boundaries
- CLI commands
- Library exports

Changes require ADR.

---

# 8. Evolution Strategy

Refactors must:

- Preserve public contracts
- Preserve agreed behavior
- Maintain test coverage
- Avoid cross-layer leaks
"""


def _render_roadmap(
    project_name: str,
    build_command: str,
    run_command: str,
    test_command: str,
    solution_summary: str,
    top_risks: str,
    domain_concepts: list[str],
) -> str:
    domain_focus = "; ".join(domain_concepts[:4]) or "Core domain entities and rules"
    extra_domain = "\n".join(f"- [ ] Define rules for {concept.lower()}" for concept in domain_concepts[:4])
    return f"""# ROADMAP.md — Structured Mode v2

This roadmap defines execution.

Rules:

- Organized by milestone.
- Each milestone has a clear goal.
- Tasks grouped by architectural layer.
- Completion criteria required.
- Evidence required before marking tasks complete.
- No flat TODO lists.

---

# {MILESTONE_NAME}

## Goal

Establish the first implementation slice for {project_name} and validate the project baseline.

## Architecture Impact

- Lock the initial service and UI boundaries around the product shape.
- Keep core business logic authoritative and testable.
- Preserve room for later milestones without rewriting the spine.

Product focus:

- {solution_summary}

Primary risk pressure:

- {top_risks}

---

## Domain/Core

- [ ] Model the core domain entities and relationships
{extra_domain}
- [ ] Add deterministic unit tests for the core domain logic

Focus areas:

- {domain_focus}

---

## Application

- [ ] Create the first use-case orchestration needed for the milestone
- [ ] Separate lower-risk and higher-risk application workflows where the product shape requires it
- [ ] Define transaction boundaries and error handling for the first slice

---

## Persistence

- [ ] Define repository interfaces for milestone data and runtime state
- [ ] Design the initial persistence schema and migration strategy
- [ ] Ensure persisted state can be reconstructed and verified

---

## Interface

- [ ] Build the first user-facing or operator-facing flow needed for the milestone
- [ ] Build the first privileged or editor-facing flow needed to manage core data
- [ ] Provide clear validation and failure feedback at the boundaries

---

## Infrastructure

- [ ] Stand up the local runtime needed for app, storage, and supporting services
- [ ] Configure auth, secrets, and environment boundaries
- [ ] Make the local dev flow reproducible for build, run, and test commands

---

## Testing & Verification

- [ ] Build succeeds
- [ ] Tests pass
- [ ] Manual smoke test completes for the first milestone flow

Evidence target:

- Evidence: {build_command} (success), {test_command} (pass), {run_command} (smoke verified)

---

## Completion Criteria

- The first milestone flow works end to end.
- Core domain behavior is covered by tests.
- Surface boundaries are defined and respected.
- The architecture can grow without invalidating the spine.
"""


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
    problem_statement = _state_value(state, "product.problemStatement") or _first_value_for_label(
        hydration_files, ["Problem statement"]
    ) or purpose
    target_users = _state_value(state, "product.targetUsers") or _first_value_for_label(
        hydration_files, ["Target users", "Affected users/personas"]
    ) or "Users validated during brainstorming"
    solution_summary = _state_value(state, "product.solutionSummary") or _first_value_for_label(
        hydration_files, ["Solution summary"]
    ) or purpose
    mvp_scope = _state_value(state, "product.mvpScope") or _first_value_for_label(
        hydration_files, ["MVP scope"]
    ) or "Capture milestone scope in ROADMAP.md."
    out_of_scope = _state_value(state, "product.outOfScope") or _first_value_for_label(
        hydration_files, ["Out of scope"]
    ) or "Track non-goals explicitly."
    top_risks = _state_value(state, "governance.topRisks") or _first_value_for_label(
        hydration_files, ["Top risks", "Top risks (link to risk entries)"]
    ) or "Capture implementation risks during the first milestone."
    domain_concepts = _infer_domain_concepts(
        " ".join([purpose, problem_statement, solution_summary, mvp_scope, out_of_scope])
    )

    _copy_base(root, "development/templates/docs/README.base.md", "README.md")
    _copy_base(root, "development/templates/docs/PROJECT_CONTEXT.base.md", "docs/PROJECT_CONTEXT.md")
    _copy_base(root, "development/templates/docs/ROADMAP.base.md", "docs/ROADMAP.md")
    _copy_base(root, "development/templates/docs/ARCHITECTURE.base.md", "docs/ARCHITECTURE.md")
    _copy_base(root, "development/templates/docs/FILE_MAP.base.md", "docs/FILE_MAP.md")
    _copy_base(root, "development/templates/docs/GOVERNANCE_INDEX.base.md", "docs/GOVERNANCE_INDEX.md")
    _copy_base(
        root,
        "development/templates/docs/VERSIONING_AND_RELEASE_POLICY.base.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
    )
    _copy_base(root, "development/templates/docs/SECURITY_POLICY.base.md", "docs/SECURITY_POLICY.md")
    _copy_base(
        root,
        "development/templates/docs/RUNTIME_VERIFICATION_REPORT.base.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
    )
    _copy_base(
        root,
        "development/templates/docs/adr/ADR-0001-record-architecture-decisions.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
    )
    _copy_base(root, "development/templates/docs/adr/ADR-TEMPLATE.md", "docs/adr/ADR-TEMPLATE.md")
    _copy_base(root, "development/templates/docs/CHANGELOG.base.md", "CHANGELOG.md")

    migration_policy_path = root / "docs/MIGRATION_POLICY.md"
    if persistence and persistence != "None":
        _copy_base(root, "development/templates/docs/MIGRATION_POLICY.base.md", "docs/MIGRATION_POLICY.md")
    elif migration_policy_path.exists():
        migration_policy_path.unlink()

    lc_lang = language.lower()
    if "python" in lc_lang:
        shutil.copyfile(root / "development/templates/gitignore/python.gitignore", root / ".gitignore")
    elif any(token in lc_lang for token in ("node", "javascript", "typescript")):
        shutil.copyfile(root / "development/templates/gitignore/node.gitignore", root / ".gitignore")
    elif any(token in lc_lang for token in ("c#", "dotnet", ".net")):
        shutil.copyfile(root / "development/templates/gitignore/dotnet.gitignore", root / ".gitignore")
    else:
        shutil.copyfile(root / "development/templates/gitignore/generic.gitignore", root / ".gitignore")

    if persistence and persistence != "None":
        _append_unique_lines(root / ".gitignore", ["*.db", "*.sqlite", "*.sqlite3"])

    shared_replacements = [
        ("<Project Name>", project_name),
        ("<Milestone Name>", MILESTONE_NAME),
        ("<Build command>", build_command),
        ("<Run command>", run_command),
        ("<Test command>", test_command),
    ]

    for relative_path in [
        "README.md",
        "docs/PROJECT_CONTEXT.md",
        "docs/ROADMAP.md",
        "docs/ARCHITECTURE.md",
        "docs/FILE_MAP.md",
        "docs/GOVERNANCE_INDEX.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
        "docs/SECURITY_POLICY.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        "docs/adr/ADR-TEMPLATE.md",
    ]:
        _replace_file_literals(root / relative_path, shared_replacements)

    readme_path = root / "README.md"
    write_text(
        readme_path,
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
        ),
    )
    write_text(
        root / "docs/PROJECT_CONTEXT.md",
        _render_project_context(
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
            top_risks,
            build_command,
            run_command,
            test_command,
        ),
    )
    write_text(
        root / "docs/ARCHITECTURE.md",
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
        ),
    )
    write_text(
        root / "docs/ROADMAP.md",
        _render_roadmap(
            project_name,
            build_command,
            run_command,
            test_command,
            solution_summary,
            top_risks,
            domain_concepts,
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
    if marker in changelog_content:
        changelog_content = changelog_content.replace(
            marker,
            marker
            + "\n\n### Added\n- Initialized Structured Mode governance baseline from brainstorming finalization.",
            1,
        )
    write_text(changelog_path, changelog_content)

    return 0
