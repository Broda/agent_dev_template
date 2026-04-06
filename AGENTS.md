# Agent Dispatcher

This repository is a two-phase project template. It starts in **brainstorming mode** and finalizes in place into **development mode**.

## Step 1: Check the current mode

Read `MODE.md`. It will say either `brainstorming` or `development`.

Do not mix the two rule sets in one task.

## Step 2: Follow the mode contract

| Mode | Full contract | Purpose |
|---|---|---|
| `brainstorming` | `brainstorming/AGENTS.brainstorming.md` | Capture ideas, decisions, risks; finalize into a project definition |
| `development` | `development/AGENTS.development.md` | Execute delivery work against the finalized governance docs in `docs/` |

## Agent-specific guidance

- **Claude Code**: Also read `CLAUDE.md` before acting. It covers tool usage, auto-sync behavior, topic-shift nudging, and the finalize flow.
- **Other agents**: The mode contracts above are self-contained. Start with the contract for the current mode.

## Key scripts (Python 3 required)

```sh
./scripts/lab status                 # current mode, idea counts, finalize readiness
./scripts/lab doctor                 # detailed finalize-readiness report
./scripts/lab capture --idea-id <id> --title "Title"
./scripts/lab activate --idea-id <id>
./scripts/finalize-project --idea-id <id>   # switches mode to development
./scripts/validate-governance        # governance audit (run after any structural change)
```

## Brainstorming mode summary

- Primary UX: freeform conversation. Artifacts are written at milestones, not per-turn.
- Milestones: new idea captured, state transition, major decision/risk, note saved, export/finalize.
- Each `./scripts/lab` command auto-commits and auto-pushes on success (push failures are non-blocking).
- Idea lifecycle: inbox → active → (parked | killed | finalized).
- Finalization writes `state/project-init.json`, renders `docs/`, and switches `MODE.md` to `development`.

## Development mode summary

- Before any meaningful change: read `docs/GOVERNANCE_INDEX.md` and all documents it lists.
- Identify the active milestone in `docs/ROADMAP.md`; confirm the change is in scope.
- Definition of Done requires: build passes, tests pass, docs updated, evidence recorded in `ROADMAP.md`.
- Public contracts (API, CLI, config formats) require an ADR before changing.
- Research notes: use `./scripts/lab-note`; stored in `notes/`, indexed in `NOTES_CATALOG.md`.
