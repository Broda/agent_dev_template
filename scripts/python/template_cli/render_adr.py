from __future__ import annotations

from template_cli.render_contract import format_contract_sections


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
