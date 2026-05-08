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
| Command | Modes | Backend intent | Wrapper | Required args | Optional args | Write behavior | Output and exit codes |
|---|---|---|---|---|---|---|---|
| `/lab capture` | `brainstorming` | `/lab capture <idea-id>` | `scripts/lab` | `--idea-id` | `--title`, `--owner`, `--problem`, `--summary`, `--scope`, `--constraints`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab activate` | `brainstorming` | `/lab activate <idea-id>` | `scripts/lab` | `--idea-id` | `--title`, `--owner`, `--session`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab decide` | `brainstorming` | `/lab decide <decision-slug>` | `scripts/lab` | `--idea-id` | `--decision-id`, `--owner`, `--session`, `--decision-level`, `--situation`, `--rationale`, `--constraints`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab risk` | `brainstorming` | `/lab risk <idea-id>` | `scripts/lab` | `--idea-id` | `--risk-id`, `--owner`, `--session`, `--mitigation`, `--contingency`, `--probability`, `--impact`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab path-note` | `brainstorming` | `/lab path-note <idea-id>` | `scripts/lab` | `--idea-id`, `--title` | `--summary`, `--deferred`, `--session`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab note` | `brainstorming`, `development` | `/lab note <topic-or-ref>` | `scripts/lab` | `--topic` | `--source`, `--idea-id`, `--tags`, `--summary`, `--summary-file`, `--detail`, `--details-file`, `--fact`, `--facts-file`, `--question`, `--questions-file`, `--link`, `--links-file`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab review` | `brainstorming` | `/lab review <idea-id>` | `scripts/lab` | `--idea-id`, `--result` | `--owner`, `--session`, `--summary`, `--outcome`, `--next-action`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab export` | `brainstorming` | `/lab export <idea-id>` | `scripts/lab` | `--idea-id` | `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab finalize` | `brainstorming` | `/lab finalize [<idea-id>]` | `scripts/lab` | none | `--idea-id`, `--write-export`, `--interactive` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab handoff` | `brainstorming` | `/lab handoff [<idea-id>]` | `scripts/lab` | none | `--idea-id`, `--check`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab park` | `brainstorming` | `/lab park <idea-id>` | `scripts/lab` | `--idea-id` | `--owner`, `--reason`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab kill` | `brainstorming` | `/lab kill <idea-id>` | `scripts/lab` | `--idea-id` | `--owner`, `--reason`, `--no-sync` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab status` | `brainstorming`, `development` | `/lab status` | `scripts/lab` | none | none | `no-write` | human-readable status report on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab doctor` | `brainstorming` | `/lab doctor [<idea-id>]` | `scripts/lab` | none | `--idea-id` | `no-write` | human-readable status report on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab audit` | `brainstorming`, `development` | `/lab audit` | `scripts/lab` | none | none | `no-write` | governance validation summary on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab evidence` | `development` | `/lab evidence <task>` | `scripts/lab` | `--task`, `--command`, `--result` | `--note`, `--no-complete` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab adr` | `development` | `/lab adr <title>` | `scripts/lab` | `--title`, `--decision` | `--context`, `--consequence`, `--alternative`, `--status`, `--deciders`, `--supersedes`, `--date` | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab wiki-render` | `development` | `/lab wiki-render` | `scripts/lab` | none | none | `write` | human-readable command result on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab wiki-check` | `development` | `/lab wiki-check` | `scripts/lab` | none | none | `no-write` | human-readable status report on stdout; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab commit` | `brainstorming`, `development` | `/lab commit [message]` | `scripts/lab` | none | `--message` | `git` | git command progress and result on stdout/stderr; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab push` | `brainstorming`, `development` | `/lab push` | `scripts/lab` | none | none | `git` | git command progress and result on stdout/stderr; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
| `/lab sync` | `brainstorming`, `development` | `/lab sync [message]` | `scripts/lab` | none | `message and git sync args` | `git` | git command progress and result on stdout/stderr; `0` success, `1` runtime or validation failure, `2` usage, mode, or registry error |
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

### `/lab handoff [<idea-id>]`
- Brainstorming-mode command.
- Compile idea, session, optional export, and existing state details into draft canonical state before finalization.
- Default target is the current idea from canonical state or the single active idea.
- Use `--idea-id <idea-id>` when multiple active ideas exist.
- Use `--check` to report fillable fields and gaps without writing.
- Default write mode updates `state/project-init.json` and appends a handoff session under `sessions/`.
- Does not finalize, render development docs, switch `MODE.md`, or move idea state.
- Example:
  - `./scripts/lab handoff --idea-id idea-template-hardening`
  - `./scripts/lab handoff --idea-id idea-template-hardening --check`

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
