---
name: brainstorming-lab
description: Use in this template repo when MODE.md says brainstorming, or when the user wants to capture, activate, park, kill, review, export, finalize, or discuss project ideas with milestone persistence.
---

# Brainstorming Lab

Use this skill after `MODE.md` confirms `brainstorming`.

## Operating Model

- Keep conversation natural; do not force slash commands during ordinary brainstorming.
- Persist only milestone events: new idea, state transition, major decision, risk, research note, export, or finalize.
- Use Focus Mode: report user-facing outcomes and consequential failures; keep routine sync chatter quiet.
- Do not load `notes/` by default. Search `NOTES_CATALOG.md` first only when prior research is requested or referenced.

## Milestone Commands

Use `./scripts/lab <command>` for durable brainstorming lifecycle writes:

- Capture: `./scripts/lab capture --idea-id <id> --title "<title>"`
- Activate: `./scripts/lab activate --idea-id <id>`
- Decision: `./scripts/lab decide --idea-id <id> --chosen-option "<choice>" --rationale "<why>"`
- Risk: `./scripts/lab risk --idea-id <id> --statement "<risk>"`
- Review: `./scripts/lab review --idea-id <id> --result <pass|conditional-pass|revise|fail>`
- Export: `./scripts/lab export --idea-id <id>`
- Status: `./scripts/lab status`
- Doctor: `./scripts/lab doctor [--idea-id <id>]`

`./scripts/lab` milestone writes auto-commit and best-effort push unless `--no-sync` is passed.

## Topic Continuity

For persistent multi-turn sessions, keep lightweight in-context nudge state:

- `last_milestone_ts`
- `last_nudge_ts`
- `current_thread_signature`

When a likely topic shift appears and the cooldown has passed, ask once:

`Before we switch, save the previous thread?`

Offer quick actions: `capture idea`, `record decision`, `log risk`, `save path note`, `skip`.

## Finalization

When the user wants to switch to development mode, use `$project-finalizer`.
