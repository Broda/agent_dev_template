# Brainstorming Mode Contract

Keep brainstorming natural while recording milestone artifacts for later finalization.

## Interaction Mode

- Primary UX: freeform conversational brainstorming.
- Persistence style: auto-journaling at milestones.
- Do not force slash commands during normal chat.
- Focus Mode: on by default.

## Git Sync Behavior

- Auto-commit on each milestone write.
- Auto-push after each auto-commit.
- Push target: current branch to `origin/<current-branch>`.
- Push safety: push only if working tree is clean after commit.
- Autosync runs in quiet mode by default.
- Push failures are silent and non-blocking in default brainstorming flow.

## Milestone Capture Rule

Persist updates only when one of these occurs:

- New idea captured
- State transition
- Major decision or risk
- Research note captured
- Export/finalize action

Avoid per-turn file churn for exploratory discussion.

## Finalization Rule

- Always create the exported project plan packet first.
- Persist canonical answers in `state/project-init.json`.
- Finalize in place with `./scripts/finalize-project --idea-id <idea-id>`.
- Do not clone another repository during finalize.

## Research Note Retrieval

- `notes/` and `NOTES_CATALOG.md` are a durable research archive.
- Do not load note contents into working context by default at session start.
- Do not search or read notes unless the user asks for them or clearly references prior research.
- When the user asks, search `NOTES_CATALOG.md` first, then open only the relevant note files.
- Treat notes as supporting context, not as always-on governance.

## Required Artifacts For Finalization

- Idea record in `ideas/_*.md` and `IDEA_CATALOG.md`
- At least one session file in `sessions/`
- Export file in `exports/`
- Canonical handoff state in `state/project-init.json` after finalization

## References

- `brainstorming/CONVERSATIONAL_MODE.md`
- `brainstorming/COMMANDS.md`
- `scripts/validate-governance`
