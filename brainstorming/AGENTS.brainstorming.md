# Brainstorming Mode Contract

This compatibility contract is kept for agents that do not load repo-scoped skills automatically.

## Canonical Workflow

Read `.agents/skills/brainstorming-lab/SKILL.md` for brainstorming-mode behavior:

- Natural conversation first.
- Persist only milestone events.
- Use `./scripts/lab` for durable idea lifecycle writes.
- Keep research notes archival unless explicitly requested.
- Use topic-shift nudges only in persistent multi-turn sessions.

## Finalization

For transition into development mode, read `.agents/skills/project-finalizer/SKILL.md`.

Important invariants:

- `state/project-init.json` and `sessions/` are the finalization source of truth.
- Finalize in place with `./scripts/finalize-project --idea-id <idea-id>`.
- Use `--write-export` only for an archival summary snapshot in `exports/`.
- Do not clone another repository during finalize.

## References

- `harness_commands/CONVERSATIONAL_MODE.md`
- `harness_commands/COMMANDS.md`
- `scripts/validate-governance`
