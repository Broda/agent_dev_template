---
name: brainstorming-lab
description: Use in this project harness template when MODE.md says brainstorming, or when the user wants to capture, activate, park, kill, review, export, finalize, or discuss project ideas with milestone persistence.
---

# Brainstorming Lab

Use this skill after `MODE.md` confirms `brainstorming`.

## Operating Model

- Keep conversation natural; do not force slash commands during ordinary brainstorming.
- Treat user phrasing as the primary interface. Map milestone intent through `.harness/commands/intent_registry.json` and `.harness/commands/COMMANDS.md`, then run deterministic `./scripts/lab ...` commands as the backend.
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
- Handoff: `./scripts/lab handoff [--idea-id <id>] [--check]`
- Status: `./scripts/lab status`
- Doctor: `./scripts/lab doctor [--idea-id <id>]`

`./scripts/lab` milestone writes auto-commit and best-effort push unless `--no-sync` is passed. When a user wants several related writes to land as one commit, run the earlier writes with `--no-sync` and run the final write normally; skipped file-scoped writes are folded into the final sync commit.

Use `./scripts/lab-note` for durable research notes. When saving a discussion, include the important details directly with `--summary` or `--detail`, durable constraints with `--fact`, unresolved items with `--question`, and references with `--link`. For longer captures, use the matching `--details-file`, `--facts-file`, `--questions-file`, or `--links-file` options; pass `-` to read one section from stdin.

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
When the user is worried about losing detail, or the idea has rich implementation/session context, run `./scripts/lab handoff --check` first and then `./scripts/lab handoff` to distill source material into `state/project-init.json` before finalizing.
