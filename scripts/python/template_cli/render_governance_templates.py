from __future__ import annotations

from template_cli.render_helpers import MILESTONE_NAME
from template_cli.render_contract import format_contract_sections


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
    implementation_contract: list[tuple[str, list[str]]],
) -> str:
    concept_lines = "\n".join(f"- {concept}" for concept in domain_concepts)
    contract_sections = format_contract_sections(implementation_contract, heading_level=2)
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

# 6. Concrete Implementation Boundaries

{contract_sections}

---

# 7. Layer Responsibilities

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

# 8. Public Contracts

Public contracts include:

- API endpoints
- DTO structures
- Surface boundaries
- CLI commands
- Library exports

Changes require ADR.

---

# 9. Evolution Strategy

Refactors must:

- Preserve public contracts
- Preserve agreed behavior
- Maintain test coverage
- Avoid cross-layer leaks
"""


def _render_decision_adr(
    project_name: str,
    purpose: str,
    key_decisions: str,
    top_risks: str,
    mitigation_plans: str,
    contingencies: str,
    latest_review_outcome: str,
    session_files: list[str],
    implementation_contract: list[tuple[str, list[str]]],
) -> str:
    session_lines = "\n".join(f"- `{session}`" for session in session_files) or "- See canonical state."
    contract_sections = format_contract_sections(implementation_contract, heading_level=3)
    return f"""# ADR-0001: Record Initial Architecture Decisions

## Status
Accepted

## Context

{project_name} is entering development mode with this finalized purpose:

{purpose}

The brainstorming record identified these risk pressures:

- {top_risks}

Latest review outcome: {latest_review_outcome}

Source sessions:

{session_lines}

## Decision

{key_decisions}

### Finalized Implementation Contract

{contract_sections}

## Consequences

- Development work must respect the finalized decisions above unless superseded by a later ADR.
- Implementation plans should preserve the product intent, constraints, and session evidence carried forward from brainstorming.
- Risk handling should follow this mitigation plan: {mitigation_plans}

## Contingencies

{contingencies}

## Alternatives Considered

- Re-decide the architecture during implementation.
- Keep decisions only in brainstorming notes.
- Treat generated development docs as advisory rather than authoritative.

Rejected because development mode needs traceable, version-controlled decisions that survive the mode switch.
"""


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
) -> str:
    domain_focus = "; ".join(domain_concepts[:4]) or "Core domain entities and rules"
    extra_domain = "\n".join(f"- [ ] Define rules for {concept.lower()}" for concept in domain_concepts[:4])
    contract_sections = format_contract_sections(implementation_contract, heading_level=3)
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

- Evidence: `{build_command}` (success), `{test_command}` (pass), `{run_command}` (smoke verified)

---

## Completion Criteria

- The first milestone flow works end to end.
- Core domain behavior is covered by tests.
- Surface boundaries are defined and respected.
- The architecture can grow without invalidating the spine.
"""
