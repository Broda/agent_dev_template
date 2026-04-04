# Commands

Backend contract for conversational operations in the Project Idea Lab.

Python 3 is required for the `scripts/` command implementations referenced in this document.

## Usage Style

- Primary UX: conversational intent (plain language).
- `/lab` command syntax remains optional and supported.
- The backend contract is executable through `./scripts/lab <command> ...`.
- Milestone writes implicitly run commit + push synchronization.
- Default brainstorming runtime uses Focus Mode (quiet background ops).
- Autosync push is best-effort; push failures are silent by default while local commits are retained.

## Conventions

- Idea ID format: `idea-<kebab-case>`
- Decision ID format: `decision-<nnn>`
- Risk ID format: `risk-<nnn>`
- Note ID format: `note-<nnnn>`
- ADR ID format: `ADR-XXXX`
- Dates: `YYYY-MM-DD`

## Conversational Intent Mapping

| Conversational phrase | Backend intent |
|---|---|
| "capture this idea" | `/lab capture <idea-id>` |
| "make this active" | `/lab activate <idea-id>` |
| "decision: ... because ..." | `/lab decide <decision-slug>` |
| "risk: ..." | `/lab risk <idea-id>` |
| "save path note" | `/lab path-note <idea-id>` |
| "save that info in notes" | `/lab note <topic-or-ref>` |
| "save a note on <topic>" | `/lab note <topic-or-ref>` |
| "save that research" | `/lab note <topic-or-ref>` |
| "review this idea" | `/lab review <idea-id>` |
| "save a summary snapshot" | `/lab export <idea-id>` |
| "finalize this repo" | `/lab finalize [<idea-id>]` |
| "park this" | `/lab park <idea-id>` |
| "kill this" | `/lab kill <idea-id>` |
| "run audit" | `/lab audit` |

## Commands (Backend Contract)

### `/lab capture <idea-id>`
- Add/update idea in `ideas/_inbox.md` using `brainstorming/templates/idea_template.md`.
- Add/update row in `IDEA_CATALOG.md`.
- Update `brainstorming/FILE_MAP.md` when file inventory changes.

### `/lab activate <idea-id>`
- Move/update idea in `ideas/_active.md`.
- Create/update session file in `sessions/`.
- Update `IDEA_CATALOG.md`.

### `/lab decide <decision-slug>`
- Record decision in session using `brainstorming/templates/decision_template.md`.
- For major strategic changes, create ADR from `brainstorming/docs/adr/template.md`.
- Update `IDEA_CATALOG.md` references.

### `/lab risk <idea-id>`
- Record risk in session using `brainstorming/templates/risk_template.md`.

### `/lab path-note <idea-id>`
- Append note to the current session file under `## Exploration Path Notes`.
- Create section if missing.
- Entry format:
  - Timestamp (`YYYY-MM-DD HH:mm`)
  - Thread title (short)
  - 1-3 summary bullets
  - Optional deferred/parked rationale

### `/lab note <topic-or-ref>`
- Resolve source context from recent relevant assistant research.
- Matching heuristic:
  - explicit topic reference > topic keyword overlap > most recent research block
- If multiple plausible source contexts exist, ask one clarifier with top candidates.
- If no candidate exists, ask user to restate target topic/cue.
- Create note file in `notes/` using sequential ID naming:
  - `notes/YYYY-MM-DD_note-<NNNN>-<kebab-topic>.md`
- Append row to `NOTES_CATALOG.md`:
  - `Note ID | Title | Date | Related Idea | Source Context | Path | Tags`
- Treat note saves as milestone writes and persist immediately.
- Update `brainstorming/FILE_MAP.md` when file inventory changes.

### `/lab review <idea-id>`
- Record review notes and optional gate using `brainstorming/templates/review_gate_template.md`.
- Update `IDEA_CATALOG.md`.

### `/lab export <idea-id>`
- Optionally create `exports/YYYY-MM-DD_PROJECT_SUMMARY_<idea-id>.md` using `brainstorming/templates/project_plan_packet_template.md`.
- Update summary export link in `IDEA_CATALOG.md` when a snapshot exists.

### `/lab finalize [<idea-id>]`
- Capture canonical decisions in `state/project-init.json`.
- Append a finalization session entry under `sessions/`.
- Finalize in place with `./scripts/finalize-project`.
- Use `--write-export` only when an archival summary snapshot is desired.
- Default target is the current idea from canonical state or the single active idea.
- If multiple ideas are active or inference is ambiguous, prompt with a numbered choice list.
- `--idea-id <idea-id>` remains available as an explicit override.
- Switch `MODE.md` to development after successful rendering and validation.

### `/lab park <idea-id>`
- Move/update idea in `ideas/_parked.md`.
- Update `IDEA_CATALOG.md`.

### `/lab kill <idea-id>`
- Move/update idea in `ideas/_killed.md`.
- Update `IDEA_CATALOG.md`.

### `/lab audit`
- Run `scripts/validate-governance`.

### `/lab commit [message]`
- Commit staged changes manually.
- Message format preferred: `brainstorm: <milestone-type> <idea-id-or-context>`.

### `/lab push`
- Push current branch to `origin/<current-branch>`.
- Requires clean working tree.

### `/lab sync [message]`
- Manual commit+push wrapper using `scripts/lab-sync`.
- Keeps local commit if push fails.
- Supports `--quiet` to suppress routine success output.
- Supports `--no-warn-push-failure` for silent best-effort push behavior.
- Default autosync profile: `scripts/lab-sync --quiet --no-warn-push-failure`.

## Topic-Shift Nudge Policy (Runtime Contract)

- Runtime tracks:
  - `last_milestone_ts`
  - `last_nudge_ts`
  - `current_thread_signature`
- Topic-shift confidence is heuristic (`low|medium|high`) using:
  - explicit shift phrases
  - domain/keyword drift
  - decision/risk markers
- Nudge only on `medium/high` and when `now - last_nudge_ts >= 10 minutes`.
- Nudge prompt:
  - "Before we switch, save the previous thread?"
  - Quick actions: `capture idea`, `record decision`, `log risk`, `save path note`, `skip`
- New session continuity checkpoint:
  - "Any key prior thread to persist before we continue?"
  - Offer same quick actions.

## Minimum Required Artifacts per Finalized Idea

- Idea record (`ideas/_*.md` + `IDEA_CATALOG.md`)
- At least one related session (`sessions/*`)
- Canonical state (`state/project-init.json`)
- Optional archival summary (`exports/*`)

## Auto-Commit Message Strategy

- Preferred: `brainstorm: <milestone-type> <idea-id-or-context>`
- Examples:
  - `brainstorm: capture idea-agentic-briefing-lab`
  - `brainstorm: decide idea-agentic-briefing-lab`
  - `brainstorm: export idea-agentic-briefing-lab`
- Fallback:
  - `brainstorm: milestone update`
