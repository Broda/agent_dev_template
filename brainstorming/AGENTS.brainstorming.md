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

Focus Mode visibility rules:
- Show: direct user responses, required user questions/prompts, consequential failures.
- Hide: routine recording/commit/push success chatter and other inconsequential background status.

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
- Finalize in place with `./scripts/finalize-project`.
- If multiple ideas are active or inference is ambiguous, pass `--idea-id <idea-id>`.
- Do not clone another repository during finalize.

## Topic-Shift Continuity Nudges

To reduce idea loss during exploratory branching:

- Maintain session-scoped nudge state:
  - `last_milestone_ts`
  - `last_nudge_ts`
  - `current_thread_signature` (lightweight keyword/topic summary)
- Use heuristic topic-shift detection (no ML requirement):
  - Explicit shift phrases (e.g., "switching", "new topic", "another idea", "unrelated")
  - Abrupt keyword/domain drift from recent turns
  - Decision/risk intent markers (e.g., "we should", "let's do", "tradeoff", "risk")
- Only auto-nudge when confidence is `medium` or `high`.
- Cooldown: at most one auto-nudge every 10 minutes.
- Nudges are advisory, not mandatory.

When a nudge triggers, ask:
- "Before we switch, save the previous thread?"
- Quick actions:
  - `capture idea`
  - `record decision`
  - `log risk`
  - `save path note`
  - `skip`

Session boundary checkpoint:
- On a new session start in the same repo, ask once:
  - "Any key prior thread to persist before we continue?"
- Offer the same quick actions.

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
