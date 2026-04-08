from __future__ import annotations

from template_cli.render_helpers import MILESTONE_NAME


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

# Product Shape

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
    build_command: str,
    run_command: str,
    test_command: str,
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
- Build command: `{build_command}`
- Run command: `{run_command}`
- Test command: `{test_command}`

Refactors must be intentional and milestone-scoped.

---

# 6. Product Risks To Respect

- {top_risks}
- Preserve authority around validation, persistence, and security-sensitive behavior.
- Keep scope aligned to the active milestone and roadmap.
- Avoid reshaping the product model casually once development mode is active.

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
