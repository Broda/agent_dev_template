# Conversational Mode

Lightweight mode for chat-first brainstorming with milestone-based recording.

## Defaults

- Auto-journaling: on
- Write cadence: milestone-based
- Auto-commit: on
- Auto-push: on
- Push policy: clean tree only
- Focus Mode: on (default)
- Background sync visibility: hidden unless consequential
- Push-failure warnings in default brainstorming flow: suppressed
- Slash commands: optional
- Topic-shift continuity nudges: on
- Nudge cooldown: 10 minutes

## Milestones That Trigger Recording

- new idea captured
- state transition
- major decision or risk
- research note captured
- export/finalize

## Intent Map

| Natural phrase | Action | Files touched |
|---|---|---|
| "let's brainstorm `<idea-id>`" | open/continue context | `sessions/*` (as needed) |
| "capture this idea" | add idea intake | `ideas/_inbox.md`, `IDEA_CATALOG.md` |
| "make this active" | move to active | `ideas/_active.md`, `sessions/*`, `IDEA_CATALOG.md` |
| "decision: ... because ..." | record decision | `sessions/*` and optionally `brainstorming/docs/adr/*` |
| "risk: ..." | record risk | `sessions/*` |
| "save path note" | append exploration note to current session file | `sessions/*` |
| "save that info in notes" | create research note from prior gathered context | `notes/*`, `NOTES_CATALOG.md` |
| "save a note on `<topic>`" | create research note scoped to topic | `notes/*`, `NOTES_CATALOG.md` |
| "save that research" | create research note from prior gathered context | `notes/*`, `NOTES_CATALOG.md` |
| "review this idea" | record review/gate | `sessions/*`, `IDEA_CATALOG.md` |
| "finalize/export plan" | create export, persist canonical state, and switch this repo into development mode | `exports/*`, `state/project-init.json`, `MODE.md`, `docs/*`, `IDEA_CATALOG.md` |
| "run audit" | validate integrity | `scripts/validate-governance` |

## Notes

- Freeform conversation is valid; no write occurs until milestones happen.
- Background recording/sync runs quietly by default to protect brainstorming flow.
- If a likely topic shift is detected, prompt once (respecting 10-minute cooldown): "Before we switch, save the previous thread?"
- Topic-shift quick actions: `capture idea`, `record decision`, `log risk`, `save path note`, `skip`.
- Note recall rule: for "save that info" requests, resolve from recent relevant research; if ambiguous, ask one clarifier.
- For small ideas, keep artifacts minimal: idea + session + export.
- No extra push phrase is required; milestone commits are auto-pushed by default.
- If push fails, local commits are preserved for manual retry without interrupting flow.
