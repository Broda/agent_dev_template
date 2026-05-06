# Harness Commands

Backend contract for conversational operations in the project harness.

Python 3 is required for the `scripts/` command implementations referenced in this document.

## Usage Style

- Primary UX: conversational intent (plain language).
- `/lab` command syntax remains optional and supported.
- The backend contract is executable through `./scripts/lab <command> ...`.
- Milestone writes in brainstorming mode implicitly run commit + push synchronization.
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

This table is generated from `harness_commands/intent_registry.json` via `./scripts/render-intent-docs`.
It is for agent dispatch: humans can speak the phrase family naturally, and agents translate it to the backend intent before running deterministic harness commands.

<!-- BEGIN GENERATED CONVERSATIONAL INTENT MAPPING -->
| Conversational phrase family | Modes | Backend intent |
|---|---|---|
| "capture this idea", "save this idea", "log this idea" | `brainstorming` | `/lab capture <idea-id>` |
| "make this active", "promote this idea", "work on this now" | `brainstorming` | `/lab activate <idea-id>` |
| "decision: ... because ...", "we should do X", "record this decision" | `brainstorming` | `/lab decide <decision-slug>` |
| "risk: ...", "log this risk", "what could go wrong here?" | `brainstorming` | `/lab risk <idea-id>` |
| "save path note", "record this branch", "note why we deferred that" | `brainstorming` | `/lab path-note <idea-id>` |
| "save that info in notes", "save a note on <topic>", "save that research" | `brainstorming`, `development` | `/lab note <topic-or-ref>` |
| "review this idea", "gate this idea", "is this ready?" | `brainstorming` | `/lab review <idea-id>` |
| "save a summary snapshot", "export a summary", "make a handoff summary" | `brainstorming` | `/lab export <idea-id>` |
| "finalize this repo", "switch to development mode", "finalize this idea" | `brainstorming` | `/lab finalize [<idea-id>]` |
| "park this", "pause this idea", "put this on hold" | `brainstorming` | `/lab park <idea-id>` |
| "kill this", "drop this idea", "archive this as dead" | `brainstorming` | `/lab kill <idea-id>` |
| "what's the current state?", "show me status", "where are we now?" | `brainstorming`, `development` | `/lab status` |
| "why is finalize blocked?", "what exactly is missing before finalize?", "show me where finalize is getting values from" | `brainstorming` | `/lab doctor [<idea-id>]` |
| "run audit", "validate the repo", "check governance" | `brainstorming`, `development` | `/lab audit` |
| "record this as evidence", "mark this task done", "save verification for this task" | `development` | `/lab evidence <task>` |
| "write an ADR", "record this architecture decision", "capture this decision as an ADR" | `development` | `/lab adr <title>` |
| "generate the wiki", "update the wiki pages", "render wiki docs" | `development` | `/lab wiki-render` |
| "check wiki sync", "verify the wiki is current", "check wiki drift" | `development` | `/lab wiki-check` |
| "commit this milestone", "make a commit", "commit these changes" | `brainstorming`, `development` | `/lab commit [message]` |
| "push these changes", "push this branch", "publish the branch" | `brainstorming`, `development` | `/lab push` |
| "sync the repo", "commit and push this", "sync these changes" | `brainstorming`, `development` | `/lab sync [message]` |
<!-- END GENERATED CONVERSATIONAL INTENT MAPPING -->

## Commands (Backend Contract)

### `/lab capture <idea-id>`
- Add/update idea in `ideas/_inbox.md` using `brainstorming/templates/idea_template.md`.
- Add/update row in `IDEA_CATALOG.md`.
- Update `brainstorming/FILE_MAP.md` when file inventory changes.
- Example:
  - `./scripts/lab capture --idea-id idea-template-hardening --title "Template Hardening"`

### `/lab activate <idea-id>`
- Move/update idea in `ideas/_active.md`.
- Create/update session file in `sessions/`.
- Update `IDEA_CATALOG.md`.
- Example:
  - `./scripts/lab activate --idea-id idea-template-hardening`

### `/lab decide <decision-slug>`
- Record decision in session using `brainstorming/templates/decision_template.md`.
- For major strategic changes, create ADR from `brainstorming/docs/adr/template.md`.
- Update `IDEA_CATALOG.md` references.
- Example:
  - `./scripts/lab decide --idea-id idea-template-hardening --chosen-option "State-first finalize" --rationale "Preserve continuity"`

### `/lab risk <idea-id>`
- Record risk in session using `brainstorming/templates/risk_template.md`.
- Example:
  - `./scripts/lab risk --idea-id idea-template-hardening --statement "Docs/runtime drift"`

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
- Example:
  - `./scripts/lab review --idea-id idea-template-hardening --result conditional-pass --summary "Ready after validator parity"`

### `/lab export <idea-id>`
- Optionally create `exports/YYYY-MM-DD_PROJECT_SUMMARY_<idea-id>.md` using `brainstorming/templates/project_plan_packet_template.md`.
- Update summary export link in `IDEA_CATALOG.md` when a snapshot exists.
- Example:
  - `./scripts/lab export --idea-id idea-template-hardening`

### `/lab finalize [<idea-id>]`
- Capture canonical decisions in `state/project-init.json`.
- Append a finalization session entry under `sessions/`.
- Finalize in place with `./scripts/finalize-project`.
- Use `--write-export` only when an archival summary snapshot is desired.
- Default target is the current idea from canonical state or the single active idea.
- Finalization is non-interactive by default: complete state finalizes directly, missing fields fail with fix-up guidance.
- If multiple ideas are active or inference is ambiguous, fail and require `--idea-id`.
- `--idea-id <idea-id>` remains available as an explicit override.
- Use `--interactive` to opt into the older prompt-fill flow.
- Switch `MODE.md` to development after successful rendering and validation.
- Example:
  - `./scripts/lab finalize --idea-id idea-template-hardening --write-export`

### `/lab park <idea-id>`
- Move/update idea in `ideas/_parked.md`.
- Update `IDEA_CATALOG.md`.

### `/lab kill <idea-id>`
- Move/update idea in `ideas/_killed.md`.
- Update `IDEA_CATALOG.md`.

### `/lab audit`
- Run `scripts/validate-governance`.

### `/lab evidence <task>`
- Development-mode command.
- Find exactly one matching checkbox task in `docs/ROADMAP.md`.
- Mark the task complete unless `--no-complete` is supplied.
- Insert verification evidence directly beneath the matched task.
- Required fields:
  - `--task "<roadmap task text>"`
  - `--command "<command run>"`
  - `--result "<observed result>"`
- Optional repeated note:
  - `--note "<extra context>"`
- Example:
  - `./scripts/lab evidence --task "Tests pass" --command "python3 -m unittest discover -s tests -v" --result "60 tests passed"`

### `/lab adr <title>`
- Development-mode command.
- Create the next sequential ADR file in `docs/adr/`.
- Preserve the human-readable title in the ADR while normalizing the filename slug.
- Required fields:
  - `--title "<short decision title>"`
  - `--decision "<chosen approach>"`
- Optional repeated fields:
  - `--context "<context bullet>"`
  - `--consequence "<consequence bullet>"`
  - `--alternative "<alternative considered>"`
- Optional metadata:
  - `--status "<status>"`
  - `--deciders "<names>"`
  - `--supersedes "ADR-####"`
  - `--date "YYYY-MM-DD"`
- Example:
  - `./scripts/lab adr --title "Adopt deterministic ADR capture" --decision "Use ./scripts/lab adr for development decisions"`

### `/lab wiki-render`
- Development-mode command.
- No-op unless `state/project-init.json` has `documentation.wiki.enabled` set to `true`.
- Resolve the wiki checkout from `PROJECT_HARNESS_WIKI_DIR`, then `documentation.wiki.defaultCheckout`.
- Clone the wiki remote automatically when enabled and the checkout is missing.
- Render friendly GitHub Wiki pages while leaving the wiki checkout dirty for review.
- Example:
  - `./scripts/lab wiki-render`

### `/lab wiki-check`
- Development-mode command.
- No-op unless `state/project-init.json` has `documentation.wiki.enabled` set to `true`.
- Clone the wiki remote automatically when enabled and the checkout is missing.
- Fail when user-facing repo changes are present but the wiki checkout is clean.
- Example:
  - `./scripts/lab wiki-check`

### `/lab status`
- Report current mode, per-status idea counts, active idea context, inferred finalize target, and finalize-readiness gaps.
- If finalize target selection is ambiguous, list active candidates and call that out explicitly.
- If a single target is inferable, report related session count, summary snapshot presence, and missing fields for a low-friction finalize.
- Example:
  - `./scripts/lab status`

### `/lab doctor [<idea-id>]`
- Explain finalize-readiness in detail for the inferred target or an explicit `--idea-id`.
- Report which idea was selected, why it was selected, and which artifacts or state keys supplied required finalize fields.
- If finalize is blocked, list the exact missing inputs and suggest the next action.
- Example:
  - `./scripts/lab doctor`
  - `./scripts/lab doctor --idea-id idea-template-hardening`

### `/lab commit [message]`
- Commit staged changes manually.
- Message format preferred: `brainstorm: <milestone-type> <idea-id-or-context>`.
- Example:
  - `./scripts/lab commit --message "brainstorm: capture idea-template-hardening"`

### `/lab push`
- Push current branch to `origin/<current-branch>`.
- Requires clean working tree.
- Example:
  - `./scripts/lab push`

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
