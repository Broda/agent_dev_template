---
name: project-finalizer
description: Use in this project harness template when preparing or running brainstorming-to-development finalization, checking finalize readiness, hydrating state/project-init.json, rendering development docs, or diagnosing blocked finalization.
---

# Project Finalizer

Use this skill when finalizing an idea into development mode or diagnosing why finalization is blocked.

## Readiness Flow

1. Confirm `MODE.md` says `brainstorming`.
2. Treat phrases like "finalize this repo" and "switch to development mode" as first-class agent intents that map to `./scripts/lab finalize`.
3. Run `./scripts/lab status` for the inferred target and readiness summary.
4. Run `./scripts/lab doctor [--idea-id <id>]` when fields, sessions, or source artifacts are unclear.
5. Run `./scripts/lab handoff [--idea-id <id>] --check` when rich brainstormed details should be carried forward or finalization fields are incomplete.
6. Run `./scripts/lab handoff [--idea-id <id>]` before finalizing when the check shows useful fields can be distilled into `state/project-init.json`.
7. Treat native decision/risk completeness failures as blockers: complete the cited source records, then rerun handoff check. Related notes are discovered by `Related Idea ID` even when the idea catalog Notes cell is empty.
8. If multiple ideas are active, require an explicit `--idea-id`.
9. Treat non-interactive finalization as the default; use `--interactive` only when the user explicitly wants prompt-fill mode.

## Required Sources

Finalization needs:

- An idea record in `ideas/_*.md` and `IDEA_CATALOG.md`.
- At least one related session in `sessions/`.
- Canonical handoff state in `state/project-init.json`.

Populate known values in `state/project-init.json` before finalization when possible. Do not clone another repo.

## Execute

Run one of:

- `./scripts/finalize-project --idea-id <id>`
- `./scripts/finalize-project --idea-id <id> --write-export`

Use `--write-export` only when the user wants an archival summary under `exports/`; finalization then moves root brainstorming history into `.harness/history/`.
Use `--interactive` to opt into prompts for missing or editable finalization fields. Without `--interactive`, missing required fields should fail with guidance instead of prompting.
Use `./scripts/lab handoff` before these commands when the source sessions contain detailed implementation requirements that should become canonical state. Finalization also compiles native records directly and fails closed if their semantic contract is materially incomplete.

## After Finalization

- Confirm `MODE.md` changed to `development`.
- Confirm brainstorming history moved under `.harness/history/`.
- Run `./scripts/validate-governance`.
- Run `./scripts/validate-development`.
- Future implementation work uses `$development-governance`.
