from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from template_cli.validators import read_text, replace_literal, write_text


MILESTONE_NAME = "Milestone 0 — Foundation / Spine"
STATE_FILE = "state/project-init.json"


class RenderError(Exception):
    pass


def _trim(value: str | None) -> str:
    return (value or "").strip()


def _load_state(root: Path) -> dict:
    state_path = root / STATE_FILE
    try:
        return json.loads(read_text(state_path))
    except FileNotFoundError as exc:
        raise RenderError(f"Missing state file: {STATE_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise RenderError(f"Invalid JSON in {STATE_FILE}: {exc}") from exc


def _extract_value(state: dict, path: str) -> str:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise RenderError(f"Missing required value in {STATE_FILE}: {path}")
        cur = cur[part]
    if cur is None or not str(cur).strip():
        raise RenderError(f"Missing required value in {STATE_FILE}: {path}")
    return str(cur)


def _state_value(state: dict, path: str, default: str = "") -> str:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    if cur is None:
        return default
    value = str(cur).strip()
    return value or default


def _state_list(state: dict, path: str) -> list[str]:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return []
        cur = cur[part]
    if not isinstance(cur, list):
        return []
    values: list[str] = []
    seen: set[str] = set()
    for item in cur:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def _copy_base(root: Path, src: str, dst: str) -> None:
    src_path = root / src
    dst_path = root / dst
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_path, dst_path)


def _replace_file_literals(path: Path, replacements: list[tuple[str, str]]) -> None:
    content = read_text(path)
    for old, new in replacements:
        content = replace_literal(content, old, new)
    write_text(path, content)


def _append_unique_lines(path: Path, lines_to_add: list[str]) -> None:
    content = read_text(path)
    existing_lines = content.splitlines()
    additions = [line for line in lines_to_add if line not in existing_lines]
    if not additions:
        return
    if content and not content.endswith("\n"):
        content += "\n"
    if content and not content.endswith("\n\n"):
        content += "\n"
    content += "\n".join(additions) + "\n"
    write_text(path, content)


def _replace_readme_command_block(content: str, label: str, value: str) -> str:
    pattern = re.compile(rf"{re.escape(label)}:\r?\n\r?\n\s*<command>")
    return pattern.sub(f"{label}:\n\n    {value}", content)


def _extract_label_value(path: Path, label: str) -> str:
    prefix = f"- {label}:"
    if not path.exists():
        return ""
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return _trim(line[len(prefix) :])
    return ""


def _related_hydration_files(root: Path, idea_id: str) -> list[Path]:
    files: list[Path] = []
    for subdir in ["exports", "ideas", "sessions"]:
        base = root / subdir
        if not base.exists():
            continue
        for path in sorted(base.rglob(f"*{idea_id}*.md"), reverse=True):
            if path.is_file():
                files.append(path)
    return files


def _related_hydration_files_from_state(root: Path, state: dict, idea_id: str) -> list[Path]:
    files = _related_hydration_files(root, idea_id)
    for relative_path in _state_list(state, "artifacts.ideaFiles") + _state_list(state, "artifacts.sessionFiles"):
        path = root / relative_path
        if path.is_file() and path not in files:
            files.append(path)
    summary_export = _state_value(state, "artifacts.summaryExport")
    if summary_export:
        export_path = root / summary_export
        if export_path.is_file() and export_path not in files:
            files.append(export_path)
    return files


def _first_value_for_label(files: list[Path], labels: list[str]) -> str:
    for label in labels:
        for path in files:
            value = _extract_label_value(path, label)
            if value and value.lower() not in {"_none_", "_none yet_", "_n/a_"}:
                return value
    return ""


def _infer_domain_concepts(text: str) -> list[str]:
    lowered = text.lower()
    concepts: list[str] = []
    keyword_map = [
        ("profile", "Accounts and moderated player profiles"),
        ("egg", "Eggs, hatching, and species roll logic"),
        ("monster", "Monsters, stats, and progression"),
        ("rangler", "Ranglers, archetypes, and training specialization"),
        ("battle", "Turn-based battle flow and combat resolution"),
        ("energy", "Player and monster energy pacing"),
        ("crate", "Crates, items, and content rewards"),
        ("deploy", "Deployment-based passive earnings"),
        ("market", "Marketplace listings, trades, and ownership changes"),
        ("admin", "Admin-authored content and publish controls"),
        ("subscriber", "Subscriber status and bonus handling"),
    ]
    for token, label in keyword_map:
        if token in lowered:
            concepts.append(label)
    return concepts or ["Core domain entities and rules derived from the finalized product plan"]


def _render_readme(
    project_name: str,
    purpose: str,
    language: str,
    runtime: str,
    framework: str,
    package_tool: str,
    build_command: str,
    run_command: str,
    test_command: str,
    solution_summary: str,
    mvp_scope: str,
) -> str:
    core_loop = solution_summary or purpose
    if mvp_scope:
        core_loop = f"{core_loop} MVP scope: {mvp_scope}"
    return f"""# {project_name}

{purpose}

---

# Status

- Phase: MVP
- Active Milestone: {MILESTONE_NAME}

---

# Setup

Language: {language}
Runtime: {runtime}
Framework: {framework}
Tooling: {package_tool}

---

# Core Loop

{core_loop}

---

# Development Workflow

1. Build project
2. Run project
3. Run tests
4. Verify manually

---

# Verification Commands

Build:

    {build_command}

Run:

    {run_command}

Test:

    {test_command}

---

# Architecture

See:

- docs/PROJECT_CONTEXT.md
- docs/ARCHITECTURE.md
- docs/ROADMAP.md
- docs/FILE_MAP.md
- docs/adr/

---

# Research Notes

Capture implementation research and investigation context with:

    ./scripts/lab-note --topic "runtime-verification" --summary "Captured smoke-test notes"

Notes are stored under `notes/` and indexed in `NOTES_CATALOG.md`.

---

# Philosophy

Correctness over convenience.  
Structure over speed.  
Intentional evolution over drift.
"""


def _render_project_context(
    purpose: str,
    project_type: str,
    language: str,
    runtime: str,
    framework: str,
    package_tool: str,
    persistence: str,
    authentication: str,
    packaging: str,
    problem_statement: str,
    target_users: str,
    solution_summary: str,
    mvp_scope: str,
    out_of_scope: str,
    constraints: str,
    top_risks: str,
) -> str:
    return f"""# PROJECT_CONTEXT.md — Structured Mode v2

This document defines how this project evolves.

It exists to keep architecture, roadmap, documentation, and AI-assisted development aligned with long-term intent.

This is a structured, milestone-driven project.

---

# 1. Project Purpose

{purpose}

Primary goals:

- Correctness
- Maintainability
- Deterministic behavior (if applicable)
- Clean architecture
- Long-term extensibility
- Explicit architectural boundaries

This project is not a scratchpad.
It is intended to evolve intentionally.

---

# 2. Product Summary

- Project type: {project_type}
- Problem: {problem_statement}
- Target users: {target_users}
- Product shape: {solution_summary}
- MVP scope: {mvp_scope}
- Out of scope: {out_of_scope}

---

# 3. Technical Baseline

- Language: {language}
- Runtime: {runtime}
- Framework: {framework}
- Tooling: {package_tool}
- Persistence: {persistence}
- Authentication: {authentication}
- Packaging/distribution: {packaging}
- Delivery constraints: {constraints}

---

# 4. Core Architectural Principles

The system follows strict layer separation:

Interface Layer  
→ Application Layer  
→ Domain/Core Logic  
→ Persistence Layer  
→ Infrastructure/Storage

## 4.1 Boundary Rules

- Domain must contain no UI, framework, or infrastructure logic.
- Interface must not contain business rules.
- Persistence must be abstracted behind repository interfaces.
- Infrastructure must not leak into Domain.
- Public interfaces must not change silently.
- Deterministic logic must not rely on uncontrolled runtime behavior.

If unsure, prefer placing logic deeper (Domain/App) rather than higher (Interface).

---

# 5. Development Model

- Local-first development.
- Manual verification required.
- Tests required for core logic.
- No CI/CD required at this stage.
- Milestone-driven execution.

Refactors must be intentional and milestone-scoped.

---

# 6. Product Risks To Respect

- {top_risks}
- Preserve server authority around gameplay and progression.
- Keep content expansion data-driven where possible.
- Avoid scope expansion before the first playable loop is stable.

---

# 7. Documentation Discipline

When a meaningful decision is made:

1. Create or update an ADR in docs/adr/
2. Update ARCHITECTURE.md if structural changes occur.
3. Update ROADMAP.md if milestone scope changes.
4. Update PROJECT_CONTEXT.md if architectural philosophy shifts.

Do not silently introduce structural changes.

---

# 8. Definition of Done (Mandatory)

A task may be marked complete only when:

- Project builds successfully.
- Application runs successfully.
- Relevant tests exist and pass.
- Documentation updated if required.
- No architectural boundary violations introduced.
- Evidence commands are recorded under the completed task in ROADMAP.md.

Example evidence:

- Evidence: `npm test` (pass), `npm run build` (success), manual smoke verified.

No exceptions.

---

# 9. Milestone Discipline

- Only one active milestone at a time.
- All work must align with the active milestone.
- Future features must not be implemented early.
- Refactors must preserve public contracts unless explicitly scoped.

ROADMAP.md is the execution map.
It is not a scratchpad.
"""


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

- Deliver the core {project_name} gameplay loop with clear boundaries.
- Keep infrastructure replaceable without rewriting domain logic.
- Preserve deterministic and testable gameplay calculations.
- Maintain stable public contracts.
- Support long-term maintainability and content extensibility.

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

- Public player surface for gameplay, progression, and market interactions.
- Private admin surface for content authoring, balance controls, and release/publish actions.
- Backend application services that keep game rules authoritative.
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
- Contain gameplay rules
- Access storage directly

---

## Application Layer

- Orchestrates onboarding, progression, battle, and admin use cases
- Coordinates domain services and repositories
- Defines transaction boundaries and workflow sequencing

---

## Domain Layer

- Pure gameplay and business logic
- Deterministic calculations where possible
- Framework-agnostic rules for progression, economy, and ownership
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
- Admin/public surface boundaries
- CLI commands
- Library exports

Changes require ADR.

---

# 8. Evolution Strategy

Refactors must:

- Preserve public contracts
- Preserve gameplay behavior
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
    domain_focus = "; ".join(domain_concepts[:4]) or "Core entities and game rules"
    extra_domain = "\n".join(f"- [ ] Define rules for {concept.lower()}" for concept in domain_concepts[:5])
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

Establish the first playable {project_name} vertical slice and validate the project baseline.

## Architecture Impact

- Lock the initial service and UI boundaries around the product shape.
- Keep gameplay logic authoritative and testable.
- Preserve room for content expansion without rewriting the spine.

Product focus:

- {solution_summary}

Primary risk pressure:

- {top_risks}

---

## Domain/Core

- [ ] Model the core game entities and relationships
- [ ] Define rules for onboarding, progression, and ownership state
{extra_domain}
- [ ] Add deterministic unit tests for the core gameplay calculations

Focus areas:

- {domain_focus}

---

## Application

- [ ] Create use-case orchestration for player onboarding and profile setup
- [ ] Create orchestration for starter progression, training, and battle flows
- [ ] Separate public-player and private-admin workflows

---

## Persistence

- [ ] Define repository interfaces for player state, content, and runtime history
- [ ] Design the initial persistence schema and migration strategy
- [ ] Ensure progression and economy state can be reconstructed and verified

---

## Interface

- [ ] Build the first player-facing flow needed for the playable loop
- [ ] Build the first admin flow needed to manage core content
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
- [ ] Manual smoke test completes for the first playable loop

Evidence target:

- Evidence: {build_command} (success), {test_command} (pass), {run_command} (smoke verified)

---

## Completion Criteria

- The first playable loop works end to end.
- Core domain behavior is covered by tests.
- Public/admin boundaries are defined and respected.
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

    setup_steps = (
        f"Language: {language}\n"
        f"Runtime: {runtime}\n"
        f"Framework: {framework or 'None'}\n"
        f"Tooling: {package_tool or 'None'}"
    )

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
