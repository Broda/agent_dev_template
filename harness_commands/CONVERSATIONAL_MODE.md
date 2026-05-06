# Harness Command Conversational Mode

Agent-facing command intent model for chat-first human-agent development.

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

This table is generated from `harness_commands/intent_registry.json` via `./scripts/render-intent-docs`.
It is the agent-facing interface across harness modes: the user can speak naturally, and the agent maps intent into deterministic harness actions allowed for the current mode.

<!-- BEGIN GENERATED INTENT MAP -->
| Natural phrase family | Modes | Action | Files touched |
|---|---|---|---|
| "capture this idea", "save this idea", "log this idea" | `brainstorming` | add idea intake | `ideas/_inbox.md`, `IDEA_CATALOG.md` |
| "make this active", "promote this idea", "work on this now" | `brainstorming` | move to active | `ideas/_active.md`, `sessions/*`, `IDEA_CATALOG.md` |
| "decision: ... because ...", "we should do X", "record this decision" | `brainstorming` | record decision | `sessions/*` and optionally `brainstorming/docs/adr/*` |
| "risk: ...", "log this risk", "what could go wrong here?" | `brainstorming` | record risk | `sessions/*` |
| "save path note", "record this branch", "note why we deferred that" | `brainstorming` | append exploration note to current session file | `sessions/*` |
| "save that info in notes", "save a note on <topic>", "save that research" | `brainstorming`, `development` | create research note from prior gathered context or explicit topic | `notes/*`, `NOTES_CATALOG.md` |
| "review this idea", "gate this idea", "is this ready?" | `brainstorming` | record review/gate | `sessions/*`, `IDEA_CATALOG.md` |
| "save a summary snapshot", "export a summary", "make a handoff summary" | `brainstorming` | generate an optional archival project summary | `exports/*` |
| "finalize this repo", "switch to development mode", "finalize this idea" | `brainstorming` | persist canonical state, append finalization history, and switch this repo into development mode | `sessions/*`, `state/project-init.json`, `MODE.md`, `docs/*`, `IDEA_CATALOG.md` |
| "park this", "pause this idea", "put this on hold" | `brainstorming` | move idea to parked state | `ideas/_parked.md`, `IDEA_CATALOG.md` |
| "kill this", "drop this idea", "archive this as dead" | `brainstorming` | move idea to killed state | `ideas/_killed.md`, `IDEA_CATALOG.md` |
| "what's the current state?", "show me status", "where are we now?" | `brainstorming`, `development` | report current mode plus brainstorming or development context | no write |
| "why is finalize blocked?", "what exactly is missing before finalize?", "show me where finalize is getting values from" | `brainstorming` | explain finalize-readiness and source evidence | no write |
| "run audit", "validate the repo", "check governance" | `brainstorming`, `development` | validate integrity | `scripts/validate-governance` |
| "record this as evidence", "mark this task done", "save verification for this task" | `development` | mark a roadmap task complete and record verification evidence | `docs/ROADMAP.md` |
| "write an ADR", "record this architecture decision", "capture this decision as an ADR" | `development` | create the next sequential development ADR | `docs/adr/ADR-XXXX-*.md` |
| "generate the wiki", "update the wiki pages", "render wiki docs" | `development` | render friendly GitHub Wiki pages when wiki support is enabled | sibling wiki checkout |
| "check wiki sync", "verify the wiki is current", "check wiki drift" | `development` | verify user-facing changes are paired with wiki updates when enabled | sibling wiki checkout status |
| "commit this milestone", "make a commit", "commit these changes" | `brainstorming`, `development` | create an explicit git commit | git metadata and working tree |
| "push these changes", "push this branch", "publish the branch" | `brainstorming`, `development` | push the current branch to origin | git metadata and working tree |
| "sync the repo", "commit and push this", "sync these changes" | `brainstorming`, `development` | perform explicit commit plus push sync | git metadata and working tree |
<!-- END GENERATED INTENT MAP -->

## Notes

- Freeform conversation is valid; no write occurs until milestones happen.
- Open/continue-context cues such as "let's brainstorm `<idea-id>`" remain valid, but they are not command-backed registry intents.
- These phrases are intent families, not literal parser triggers. The agent/operator layer maps nearby wording onto the same backend action.
- Background recording/sync runs quietly by default to protect brainstorming flow.
- If a likely topic shift is detected, prompt once (respecting 10-minute cooldown): "Before we switch, save the previous thread?"
- Topic-shift quick actions: `capture idea`, `record decision`, `log risk`, `save path note`, `skip`.
- Note recall rule: for "save that info" requests, resolve from recent relevant research; if ambiguous, ask one clarifier.
- For small ideas, keep artifacts minimal: idea + session + canonical state.
- No extra push phrase is required; milestone commits are auto-pushed by default.
- If push fails, local commits are preserved for manual retry without interrupting flow.
