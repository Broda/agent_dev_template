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
