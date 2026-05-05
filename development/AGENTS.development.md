# Development Mode Contract

This compatibility contract is kept for agents that do not load repo-scoped skills automatically.

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

## Principle

Correctness over convenience.
Structure over speed.
Intentional evolution over drift.
