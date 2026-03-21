# Development Mode Contract

This repository follows Structured Mode discipline after in-place finalization.

## Mandatory Pre-Work Read Phase

Before making any meaningful change:

1. Read `docs/GOVERNANCE_INDEX.md`.
2. Then read all governance documents listed in that index.
3. Also read the most recent ADRs in `docs/adr/`.
4. Read `CHANGELOG.md` if present.

If persistence exists, include `docs/MIGRATION_POLICY.md`.

## Active Milestone Alignment

Before implementing changes:

- Identify the active milestone in `docs/ROADMAP.md`.
- Confirm the change is in scope.
- Classify the change as feature, bug fix, refactor, migration, security fix, or docs-only.

## Definition Of Done

A task may only be checked off in `docs/ROADMAP.md` when all are true:

- Project builds successfully.
- Application runs successfully.
- Relevant tests exist and pass.
- No architectural boundary violations were introduced.
- Documentation is updated if required.
- Evidence commands are recorded under the completed task.

Evidence format example:

- Evidence: `<test command>` (pass), `<build command>` (success), `<run command>` (smoke verified)

## Public Contract Discipline

Do not change public contracts without an ADR and version alignment.

Public contracts include:

- API endpoints
- IPC channels
- DTO structures
- CLI commands
- Library exports
- Config file formats
- File formats

## Policy Discipline

- Follow `docs/VERSIONING_AND_RELEASE_POLICY.md`.
- Follow `docs/SECURITY_POLICY.md`.
- Follow `docs/MIGRATION_POLICY.md` when persistence exists.
- Update `CHANGELOG.md` for user-visible changes.

## Documentation Update Rules

When making meaningful changes:

- Update `docs/ROADMAP.md` if scope changes.
- Update `docs/ARCHITECTURE.md` if structure changes.
- Create or update ADRs for architectural decisions.
- Update `docs/GOVERNANCE_INDEX.md` if governance files change.

## Research Notes

Research note capture remains active in development mode.

- Use `./scripts/lab-note` to persist external research, investigation results, implementation notes, and follow-up context.
- Notes are stored under `notes/` and indexed in `NOTES_CATALOG.md`.
- Notes complement governance docs; they do not replace ADRs, roadmap entries, or architecture updates when those are required.
- If a note materially changes project direction or constraints, update the relevant governance docs as well.
- Do not load note contents into working context by default during normal development sessions.
- Only search `NOTES_CATALOG.md` or open note files when the user asks for prior research or explicitly references notes.

## Principle

Correctness over convenience.
Structure over speed.
Intentional evolution over drift.
