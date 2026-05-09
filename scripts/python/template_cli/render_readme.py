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
