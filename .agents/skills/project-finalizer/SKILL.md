---
name: project-finalizer
description: Use in this template repo when preparing or running brainstorming-to-development finalization, checking finalize readiness, hydrating state/project-init.json, rendering development docs, or diagnosing blocked finalization.
---

# Project Finalizer

Use this skill when finalizing an idea into development mode or diagnosing why finalization is blocked.

## Readiness Flow

1. Confirm `MODE.md` says `brainstorming`.
2. Run `./scripts/lab status` for the inferred target and readiness summary.
3. Run `./scripts/lab doctor [--idea-id <id>]` when fields, sessions, or source artifacts are unclear.
4. If multiple ideas are active, require an explicit `--idea-id`.

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

Use `--write-export` only when the user wants an archival summary under `exports/`.

## After Finalization

- Confirm `MODE.md` changed to `development`.
- Run `./scripts/validate-governance`.
- Run `./scripts/validate-development`.
- Future implementation work uses `$development-governance`.
