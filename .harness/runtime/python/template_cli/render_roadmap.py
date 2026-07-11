from __future__ import annotations

from typing import Any

from template_cli.render_capabilities import ProjectProfile
from template_cli.render_contract import format_contract_sections
from template_cli.render_helpers import MILESTONE_NAME


def _render_roadmap(
    project_name: str,
    build_command: str,
    run_command: str,
    test_command: str,
    solution_summary: str,
    mvp_scope: str,
    top_risks: str,
    domain_concepts: list[str],
    implementation_contract: list[tuple[str, list[str]]],
    profile: ProjectProfile | None = None,
    milestones: list[dict[str, Any]] | None = None,
    deferred_scope: list[str] | None = None,
) -> str:
    if milestones:
        return _render_explicit_roadmap(
            project_name,
            build_command,
            run_command,
            test_command,
            solution_summary,
            top_risks,
            implementation_contract,
            milestones,
            deferred_scope or [],
        )
    profile = profile or ProjectProfile("", True, True, True, True, True, False, False)
    domain_focus = "; ".join(domain_concepts[:4]) or "Core domain entities and rules"
    extra_domain = "\n".join(f"- [ ] Define rules for {concept.lower()}" for concept in domain_concepts[:4])
    contract_sections = format_contract_sections(implementation_contract, heading_level=3)
    interface_tasks = _generic_interface_tasks(profile)
    infra_tasks = _generic_infrastructure_tasks(profile)
    architecture_impact = _architecture_impact(profile)
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

- {architecture_impact}
- Keep core business logic authoritative and testable.
- Preserve room for later milestones without rewriting the spine.

Product focus:

- {solution_summary}

Primary risk pressure:

- {top_risks}

---

## Milestone 1 MVP Contract

{mvp_scope}

{contract_sections}

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

{interface_tasks}

---

## Infrastructure

- [ ] Stand up the local runtime needed for app, storage, and supporting services
{infra_tasks}
- [ ] Make the local dev flow reproducible for build, run, and test commands

---

## Testing & Verification

- [ ] Build succeeds
- [ ] Tests pass
- [ ] Manual smoke test completes for the first milestone flow

Evidence target:

- Evidence: `{build_command}` (success), `{test_command}` (pass), `{run_command}` (smoke verified)

---

## Completion Criteria

- The first milestone flow works end to end.
- Core domain behavior is covered by tests.
- Surface boundaries are defined and respected.
- The architecture can grow without invalidating the spine.
"""


def _architecture_impact(profile: ProjectProfile) -> str:
    if profile.is_cli and profile.is_data_pipeline:
        return "Lock the initial CLI, data pipeline, and storage boundaries around the product shape."
    if profile.is_cli:
        return "Lock the initial CLI command and storage boundaries around the product shape."
    if profile.has_web_ui:
        return "Lock the initial service and UI boundaries around the product shape."
    return "Lock the initial operator interface and service boundaries around the product shape."


def _generic_interface_tasks(profile: ProjectProfile) -> str:
    if profile.is_cli:
        tasks = [
            "- [ ] Build the first operator-facing CLI flow needed for the milestone",
            "- [ ] Validate command inputs, file paths, and output formats at the boundary",
            "- [ ] Provide clear terminal feedback for success, invalid input, and recoverable failures",
        ]
    else:
        tasks = ["- [ ] Build the first user-facing or operator-facing flow needed for the milestone"]
        if profile.has_admin:
            tasks.append("- [ ] Build the first privileged or editor-facing flow needed to manage core data")
        tasks.append("- [ ] Provide clear validation and failure feedback at the boundaries")
    return "\n".join(tasks)


def _generic_infrastructure_tasks(profile: ProjectProfile) -> str:
    if profile.has_authentication:
        return "- [ ] Configure authentication, secrets, and environment boundaries"
    return "- [ ] Configure runtime settings, filesystem paths, and environment boundaries"


def _render_explicit_roadmap(
    project_name: str,
    build_command: str,
    run_command: str,
    test_command: str,
    solution_summary: str,
    top_risks: str,
    implementation_contract: list[tuple[str, list[str]]],
    milestones: list[dict[str, Any]],
    deferred_scope: list[str],
) -> str:
    contract_sections = format_contract_sections(implementation_contract, heading_level=3)
    milestone_sections = "\n\n".join(_render_milestone(milestone) for milestone in milestones)
    deferred = "\n".join(f"- {item}" for item in deferred_scope) or "- None recorded."
    return f"""# ROADMAP.md — Structured Mode v2

This roadmap defines execution.

Rules:

- Organized by milestone.
- Each milestone has a clear goal.
- Explicit finalized milestones must stay in order.
- Completion gates are required before marking tasks complete.
- Deferred scope must not be promoted into active tasks without a later ADR.

---

# Finalized Product Focus

- Project: {project_name}
- Product focus: {solution_summary}
- Primary risk pressure: {top_risks}

---

# Finalized Implementation Contract

{contract_sections}

---

# Ordered Milestones

{milestone_sections}

---

# Deferred Scope

{deferred}

---

# Verification Baseline

- Evidence: `{build_command}` (success), `{test_command}` (pass), `{run_command}` (smoke verified)
"""


def _render_milestone(milestone: dict[str, Any]) -> str:
    goal = milestone.get("goal", "") or "Complete the finalized milestone slice."
    tasks = _render_task_groups(milestone.get("tasks", []))
    gates = _render_gates(milestone.get("gates", []))
    return f"""## {milestone["id"]} - {milestone["name"]}

Goal: {goal}

### Tasks

{tasks}

### Gates

{gates}"""


def _render_task_groups(tasks: list[dict[str, str]]) -> str:
    if not tasks:
        return "- [ ] Capture milestone tasks before execution."
    if not any(task.get("area") for task in tasks):
        return "\n".join(f"- [ ] {task['text']}" for task in tasks)
    lines: list[str] = []
    current_area = ""
    for task in tasks:
        area = task.get("area", "")
        if area and area != current_area:
            if lines:
                lines.append("")
            lines.append(f"#### {area}")
            lines.append("")
            current_area = area
        lines.append(f"- [ ] {task['text']}")
    return "\n".join(lines)


def _render_gates(gates: list[dict[str, str]]) -> str:
    if not gates:
        return "- [ ] Evidence recorded."
    rendered: list[str] = []
    for gate in gates:
        name = gate.get("name", "")
        evidence = gate.get("evidence", "")
        suffix = f" Evidence: {evidence}" if evidence else ""
        rendered.append(f"- [ ] {name}{suffix}")
    return "\n".join(rendered)
