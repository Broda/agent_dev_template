# FILE_MAP.md — Structured Mode v2

This file helps developers and AI agents target changes correctly.

Always consult this before editing code.

---

## interface/

UI, CLI, or API surface.
No business logic here.

---

## application/

Use-case orchestration.
Coordinates domain and repositories.

---

## domain/

Pure business logic.
No infrastructure imports allowed.

---

## persistence/

Repository implementations.
Data mapping only.

---

## infrastructure/

Filesystem, networking, runtime environment.

---

## docs/

Architecture, roadmap, ADRs.

---

# AI Prompt Targeting

When prompting an AI agent, specify the layer:

Examples:

- "Domain only — no interface changes."
- "Refactor persistence layer only."
- "Update docs only."
- "No public contract changes."

Layer targeting prevents architectural drift.

---

# Agent Operating Rules

Before editing any file:

1. Identify the correct layer from the map above.
2. Confirm the change is isolated to that layer (or that cross-layer changes are explicitly in scope).
3. If the change touches a public contract (interface layer, API surface, CLI commands, config formats), an ADR is required before proceeding — see `docs/ARCHITECTURE.md`.

Do not introduce logic from one layer into another. If the scope is unclear, ask before editing.
