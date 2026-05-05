# Development Mode Contract

This contract defines the development-mode operating rules for agents working in this harness.

## Canonical Workflow

Read `.agents/skills/development-governance/SKILL.md` before meaningful development work.

Core requirements:

- Read `docs/GOVERNANCE_INDEX.md`, every listed governance document, recent ADRs, and `CHANGELOG.md`.
- Identify the active milestone in `docs/ROADMAP.md`.
- Run the project validation commands from `docs/PROJECT_CONTEXT.md` and `state/project-init.json`.
- Record evidence under completed roadmap tasks.
- Keep code files at or under 500 lines.
- Treat public contract changes as ADR- and version-aligned work.

## Research Notes

Research note capture remains active in development mode:

- Use `./scripts/lab-note`.
- Notes live under `notes/` and are indexed in `NOTES_CATALOG.md`.
- Search `NOTES_CATALOG.md` before opening note files.
- Update governance docs when research changes direction or constraints.

## Harness Commands

Use shared harness commands with development semantics:

- `./scripts/lab status` for finalized project, active milestone, governance coverage, and roadmap task counts.
- `./scripts/lab audit` for governance validation.
- `./scripts/lab note` for durable research notes that may require follow-up ADR, roadmap, architecture, or policy updates.
- `./scripts/lab commit`, `./scripts/lab push`, and `./scripts/lab sync` only for explicit git operations after coherent development slices.

Brainstorming-only commands are intentionally blocked in development mode by `harness_commands/intent_registry.json`.

## Principle

Correctness over convenience.
Structure over speed.
Intentional evolution over drift.
