# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Code Agent Behavior

### Brainstorming mode

- **Auto-sync is built in.** Every `./scripts/lab` command auto-commits and auto-pushes on success. Do not run separate git commands for milestone writes unless explicitly asked or the push fails.
- **Milestone detection.** Use natural language understanding to detect intent. Phrases like "capture this idea", "record this decision", "finalize this repo" map directly to `lab` subcommands (see `brainstorming/COMMANDS.md` for the full intent table). Run the corresponding command when intent is clear.
- **Topic-shift nudging.** Track three values in-context (not in any file):
  - `last_milestone_ts` — timestamp of last milestone write
  - `last_nudge_ts` — timestamp of last nudge prompt
  - `current_thread_signature` — lightweight keyword summary of the active topic
  When a likely topic shift is detected (explicit shift phrases, abrupt domain drift, or decision/risk markers) and at least 10 minutes have passed since the last nudge, ask once: *"Before we switch, save the previous thread?"* Offer: `capture idea`, `record decision`, `log risk`, `save path note`, `skip`. Reset nudge state at conversation start.
- **Session boundary checkpoint.** At the start of a conversation in brainstorming mode, ask once: *"Any key prior thread to persist before we continue?"* Offer the same quick actions.
- **Finalize interactivity.** `./scripts/finalize-project` uses stdin prompts for any missing required fields. Always pass `--idea-id <id>` to avoid blocking. Populate `state/project-init.json` with the project's known values before running finalize — or use `./scripts/lab doctor` to identify exactly what is missing.

### Development mode

- **Pre-work read sequence** (before any meaningful change): Read `docs/GOVERNANCE_INDEX.md` first, then all documents it lists, then recent ADRs in `docs/adr/`, then `CHANGELOG.md`. Use the Read tool for each file.
- **Code changes**: Use the Edit tool. Cross-reference layer boundaries in `docs/ARCHITECTURE.md` and file ownership in `docs/FILE_MAP.md` before editing.
- **Build/test/validate**: Use the Bash tool to run the `build`, `run`, and `test` commands defined in `docs/PROJECT_CONTEXT.md`. Record evidence under the completed task in `docs/ROADMAP.md`.
- **Research notes**: Run `./scripts/lab-note` via Bash. Never load `notes/` content into context unless the user asks. Check `NOTES_CATALOG.md` first when notes are needed.
- **Governance validation**: Run `./scripts/validate-governance` via Bash after any structural change.

---

## Mode System

This repository has two phases controlled by `MODE.md`:

- **`brainstorming`** — Capture ideas, decisions, and risks. Active runtime: `./scripts/lab`. Agent contract: `brainstorming/AGENTS.brainstorming.md`.
- **`development`** — Execute delivery work against finalized project definition. Agent contract: `development/AGENTS.development.md`. Read `docs/GOVERNANCE_INDEX.md` first.

**Always read `MODE.md` first and follow the contract for the current mode. Do not mix rule sets.**

Transition from brainstorming → development is one-way via `./scripts/finalize-project`.

## Common Commands

### Brainstorming phase

```sh
./scripts/lab status                          # current mode, idea counts, finalize readiness
./scripts/lab doctor [--idea-id <id>]         # detailed finalize-readiness explanation
./scripts/lab capture --idea-id <id> --title "Title"
./scripts/lab activate --idea-id <id>
./scripts/lab decide --idea-id <id> --chosen-option "..." --rationale "..."
./scripts/lab risk --idea-id <id> --statement "..."
./scripts/lab review --idea-id <id> --result conditional-pass --summary "..."
./scripts/lab export --idea-id <id>           # optional archival snapshot
./scripts/finalize-project [--idea-id <id>] [--write-export]
```

### Validation and intent doc maintenance

```sh
./scripts/validate-governance                 # full governance audit (also run as CI)
./scripts/render-intent-docs                  # regenerate intent tables from registry
```

After editing `brainstorming/intent_registry.json`, always run `render-intent-docs` then `validate-governance`.

### Tests

```sh
python3 -m unittest discover -s tests -v     # full regression suite
python3 -m unittest tests.test_lab_workflow  # single module
```

## Architecture

### Script layer

All `scripts/` entrypoints are cross-platform launchers (shell `.sh`, PowerShell `.ps1`, and a bare wrapper) that delegate to the Python implementation in `scripts/python/template_cli/`. The canonical logic lives in Python; the launchers just resolve the interpreter.

Key Python modules:
- `workflow.py` — `lab` subcommands (capture, activate, decide, risk, review, etc.)
- `finalize.py` — in-place finalization (writes `state/project-init.json`, renders docs, switches mode)
- `render.py` — renders development governance docs from `state/project-init.json` templates
- `validators.py` — governance validation logic used by `validate-governance`
- `intents.py` — renders intent tables into `brainstorming/COMMANDS.md` and `brainstorming/CONVERSATIONAL_MODE.md`
- `sync.py` / `notes.py` — git sync and research note helpers

### Intent registry

`brainstorming/intent_registry.json` is the single source of truth for conversational NL → command mappings. The generated sections inside `brainstorming/CONVERSATIONAL_MODE.md` and `brainstorming/COMMANDS.md` (bounded by `<!-- BEGIN/END GENERATED ... -->` markers) must not be hand-edited. CI enforces this with a sync check.

### State and artifacts

| Path | Role |
|---|---|
| `MODE.md` | Active phase selector |
| `state/project-init.json` | Canonical handoff state written at finalization |
| `ideas/_inbox.md`, `_active.md`, `_parked.md`, `_killed.md` | Idea lifecycle tracking |
| `IDEA_CATALOG.md` | Central idea index |
| `sessions/` | Session records and finalization continuity logs |
| `notes/` | Research notes (archival, not auto-loaded) |
| `NOTES_CATALOG.md` | Index for `notes/`; search here first before opening note files |
| `exports/` | Optional archival project summaries |
| `development/templates/docs/` | Templates used by `finalize-project` to render `docs/` |

### CI

`.github/workflows/ci.yml` runs on every PR and push to main:
1. Verifies generated intent docs are in sync (`render-intent-docs` produces no diff)
2. Runs `python3 -m unittest discover -s tests -v`
3. Runs `validate-governance`

### Development mode (post-finalization)

After `finalize-project` runs, `docs/` contains rendered governance documents. The active rules shift to `development/AGENTS.development.md`:
- Read `docs/GOVERNANCE_INDEX.md` before any meaningful change
- Align changes with the active milestone in `docs/ROADMAP.md`
- Record architectural decisions as ADRs in `docs/adr/`
- Update `CHANGELOG.md` for user-visible changes
- Public contracts (API, CLI, config formats) require an ADR before changing
