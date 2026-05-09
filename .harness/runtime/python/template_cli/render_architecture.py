from __future__ import annotations

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
