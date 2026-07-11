from __future__ import annotations

from template_cli.render_capabilities import ProjectProfile
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
    profile: ProjectProfile | None = None,
    deferred_scope: list[str] | None = None,
) -> str:
    concept_lines = "\n".join(f"- {concept}" for concept in domain_concepts)
    contract_sections = format_contract_sections(implementation_contract, heading_level=2)
    profile = profile or ProjectProfile(project_type, True, True, True, True, True, False, False)
    major_surfaces = _major_surfaces(profile)
    layer_model = _layer_model(profile)
    interface_responsibilities = _interface_responsibilities(profile)
    public_contracts = _public_contracts(profile)
    deferred = _deferred_scope(deferred_scope or [])
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

{major_surfaces}

Constraints to preserve:

- {constraints}

---

# 4. Layer Model

{layer_model}

---

# 5. Domain Areas

{concept_lines}

---

# 6. Concrete Implementation Boundaries

{contract_sections}

---

# 7. Layer Responsibilities

## Interface Layer

{interface_responsibilities}

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

{public_contracts}

Changes require ADR.

Deferred scope:

{deferred}

---

# 9. Evolution Strategy

Refactors must:

- Preserve public contracts
- Preserve agreed behavior
- Maintain test coverage
- Avoid cross-layer leaks
"""


def _major_surfaces(profile: ProjectProfile) -> str:
    if profile.is_cli and profile.is_data_pipeline:
        return "\n".join(
            [
                "- Operator-facing CLI commands for report execution and inspection.",
                "- Data ingestion and derivation services that keep business rules authoritative.",
                "- Persistence and filesystem services for local runtime state, history, and generated artifacts.",
            ]
        )
    if profile.is_cli:
        return "\n".join(
            [
                "- Operator-facing CLI commands for the current milestone.",
                "- Application services that keep business rules authoritative.",
                "- Persistence and infrastructure services that support runtime state and generated artifacts.",
            ]
        )
    lines = [
        "- User-facing or operator-facing interfaces for the current milestone.",
    ]
    if profile.has_admin:
        lines.append("- Administrative or editor workflows for controlled mutation paths.")
    lines.extend(
        [
            "- Backend application services that keep business rules authoritative.",
            "- Persistence and infrastructure services that support runtime state, history, and deployment needs.",
        ]
    )
    return "\n".join(lines)


def _layer_model(profile: ProjectProfile) -> str:
    if profile.is_cli:
        return "CLI Boundary\n-> Application\n-> Domain/Core\n-> Persistence\n-> Infrastructure"
    return "Interface\n-> Application\n-> Domain/Core\n-> Persistence\n-> Infrastructure"


def _interface_responsibilities(profile: ProjectProfile) -> str:
    if profile.is_cli:
        return "- CLI commands, file inputs, configuration parsing, and rendered output boundaries\n- Basic input validation and operator feedback"
    if profile.has_api:
        return "- Web UI, privileged UI where scoped, API handlers, and transport schemas\n- Basic input validation and presentation logic"
    return "- User interface handlers and presentation boundaries\n- Basic input validation and presentation logic"


def _public_contracts(profile: ProjectProfile) -> str:
    contracts = ["- Surface boundaries"]
    if profile.has_api:
        contracts.append("- HTTP routes and transport schemas")
    if profile.is_cli:
        contracts.append("- CLI commands")
    else:
        contracts.append("- User-facing routes or screens")
    contracts.append("- Library exports")
    contracts.append("- Stored data formats")
    return "\n".join(contracts)


def _deferred_scope(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None recorded."
