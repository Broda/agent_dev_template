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
    active_milestone: str = MILESTONE_NAME,
    public_contracts: list[str] | None = None,
    deferred_scope: list[str] | None = None,
) -> str:
    core_loop = solution_summary or purpose
    if mvp_scope:
        core_loop = f"{core_loop} MVP scope: {mvp_scope}"
    contract_lines = _render_lines(public_contracts or [], "- See docs/ARCHITECTURE.md")
    deferred_lines = _render_lines(deferred_scope or [], "- None recorded.")
    return f"""# {project_name}

{purpose}

---

# Status

- Phase: MVP
- Active Milestone: {active_milestone}

---

# Setup

Language: {language}
Runtime: {runtime}
Framework: {framework}
Tooling: {package_tool}

---

# Product Shape

{core_loop}

## Public Contracts

{contract_lines}

## Deferred Scope

{deferred_lines}

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
"""


def _render_lines(values: list[str], fallback: str) -> str:
    if not values:
        return fallback
    rendered: list[str] = []
    for value in values:
        if "<" in value and ">" in value:
            value = f"`{value}`"
        rendered.append(f"- {value}")
    return "\n".join(rendered)
