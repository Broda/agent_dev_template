---
name: development-governance
description: Use in this project harness template when MODE.md says development, or when implementing, reviewing, validating, or documenting work after project finalization.
---

# Development Governance

Use this skill after `MODE.md` confirms `development`.

## Pre-Work Read

Before meaningful changes:

1. Read `docs/GOVERNANCE_INDEX.md`.
2. Read every governance document listed there.
3. Read recent ADRs in `docs/adr/`.
4. Read `CHANGELOG.md` when present.
5. If persistence exists, include `docs/MIGRATION_POLICY.md`.

## Scope And Done

- Identify the active milestone in `docs/ROADMAP.md`.
- Classify work as feature, bug fix, refactor, migration, security fix, or docs-only.
- Keep code files at or under 500 lines, splitting by cohesive responsibility.
- Public contract changes require ADR and version alignment.

A task is done only when relevant tests pass, the project builds/runs as applicable, docs are updated when needed, and evidence is recorded under the completed roadmap task.

## Validation

Use commands from `docs/PROJECT_CONTEXT.md` and `state/project-init.json`.

After meaningful changes run:

- The project test command.
- The project build command when one exists.
- `./scripts/validate-governance`.
- `./scripts/validate-development`.

Record evidence in `docs/ROADMAP.md`.

## Harness Commands

Natural language remains the primary user interface in development mode. Map user intent through `harness_commands/intent_registry.json` and run the deterministic backend only when a durable workflow action is needed.

Shared commands keep development-specific meaning:

- `./scripts/lab status` reports finalized project context, active milestone, governance-doc coverage, and roadmap task counts.
- `./scripts/lab audit` runs harness governance validation.
- `./scripts/lab evidence` marks a matching roadmap checkbox task complete and records verification evidence beneath it.
- `./scripts/lab note` captures durable research notes; if the note changes direction, update ADRs, roadmap, architecture, or policy in the same slice.
- `./scripts/lab commit`, `./scripts/lab push`, and `./scripts/lab sync` are explicit git operations after a coherent development slice.

Brainstorming-only commands remain unavailable after finalization. Do not use `capture`, `activate`, `decide`, `risk`, `review`, `export`, `finalize`, `park`, `kill`, or `doctor` in development mode unless the registry explicitly changes.

## Research Notes

Use `./scripts/lab-note` for durable research notes. Notes complement governance docs; update ADRs, roadmap, architecture, or policy when research changes direction.
