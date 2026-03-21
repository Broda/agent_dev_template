# ADR-0001: Adopt Governance Structure for Idea Lab

- Status: Accepted
- Date: 2026-02-17
- Deciders: idea-lab-maintainer
- Technical Story: Evolve lightweight brainstorming repo into governance-structured project idea lab.
- Related Ideas: repo-governance-foundation
- Supersedes:
- Superseded by:

## Context and Problem Statement

The repository initially provided basic idea lifecycle files and templates, but lacked governance artifacts for policy enforcement, decision traceability, review rigor, and quality gating. As the lab scales, undocumented decision drift and inconsistent exports increase risk.

## Decision Drivers

- Need repeatable governance standards across all idea work.
- Need durable decision records using ADR format.
- Need quality gates before final exports.
- Need explicit command contract for governance-aware operations.

## Considered Options

1. Keep lightweight model and rely on ad hoc discipline
- Pros: minimal overhead
- Cons: weak traceability, inconsistent quality, hard to audit

2. Add governance and ADR layer while preserving existing content
- Pros: auditable decisions, quality controls, scalable process
- Cons: moderate documentation overhead

## Decision Outcome

Adopt a governance-structured idea lab with policy docs, ADR support, command standards, and cross-linked indexes while preserving all existing repository content.

## Consequences

### Positive

- Improved consistency and reviewability.
- Clear ownership and artifact locations.
- Better handoff quality to downstream build repositories.

### Negative

- Increased process/documentation effort per idea.

### Neutral

- Existing idea lifecycle files remain in place and become governed artifacts.

## Alternatives Considered But Rejected

- Using only session notes for strategic decisions.
- Why rejected: strategic changes require stronger permanence and supersedence tracking.

## Implementation Notes

- Required updates: governance docs, templates, command contract, indexes.
- Affected files: repository root docs, `templates/`, `docs/adr/`, `FILE_MAP.md`.
- Follow-up actions: create ADR-0002+ for future governance-changing decisions.
