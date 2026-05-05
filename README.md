# Project Harness Template

This public template is a project harness: a cloneable, repo-local operating environment for taking an idea from conversation into governed development.

The intended flow stays simple:

1. Clone this template into a new project repository.
2. Brainstorm the project in `brainstorming` mode.
3. Finalize in place into `development` mode.
4. Develop against the rendered governance docs.

The harness remains self-contained. Project state, deterministic scripts, validation, and generated development docs live in the repository. Plugins and skills provide agent operating knowledge around that harness; they do not replace the harness runtime.

## Tooling Runtime

- Python 3 is required for the repository automation scripts under `scripts/`.
- The shell and PowerShell entrypoints are launchers; the canonical implementation lives in Python.

## Harness Architecture

| Layer | Purpose | Examples |
|---|---|---|
| Project substrate | Durable project lifecycle state and retained docs | `MODE.md`, `ideas/`, `sessions/`, `state/`, `brainstorming/`, `development/` |
| Deterministic tooling | Repeatable local behavior that should remain inspectable in each project | `./scripts/lab`, `./scripts/finalize-project`, `./scripts/validate-governance`, `scripts/python/template_cli/` |
| Repo-scoped skills | Canonical agent instructions for operating this harness in the current repo | `.agents/skills/` |
| Plugin package | Optional portable distribution of reusable agent behavior | `plugins/project-lifecycle-lab/` |
| Future bootstrap helper | Optional convenience for creating/updating harness instances | not required for current use |

## Using This Public Harness

Start each real project from its own clone or generated repository. The harness is meant to travel with the project so brainstorming history, finalization evidence, governance docs, and local scripts remain inspectable in the same Git history as the implementation work.

After creating a project repo:

1. Point `origin` at the new project remote.
2. Keep `MODE.md` as `brainstorming` until finalization.
3. Use `./scripts/lab status` and `./scripts/lab doctor` to check readiness.
4. Treat `ideas/`, `sessions/`, `notes/`, `exports/`, and `state/project-init.json` as project-local history.
5. Run `./scripts/finalize-project` only when the project definition is ready to become development governance.

The public template should stay generic. Project-specific product decisions belong in idea records, sessions, notes, and finalized development docs, not in the reusable harness scripts or template-maintenance skills.

## Start Here

- Read `AGENTS.md`
- Confirm `MODE.md` is `brainstorming`
- Use the brainstorming workflow in `brainstorming/`

## Mode Guide

| Mode | Read First | Main Runtime | Main Goal |
|---|---|---|---|
| `brainstorming` | `.agents/skills/brainstorming-lab/SKILL.md` or `brainstorming/AGENTS.brainstorming.md` | `./scripts/lab <command> ...` | Capture ideas, decisions, risks, and canonical project intent |
| `development` | `.agents/skills/development-governance/SKILL.md` or `development/AGENTS.development.md` | governance docs under `docs/` | Execute delivery work against the finalized project definition |

## Brainstorming Phase

- Repo-scoped skill: `.agents/skills/brainstorming-lab/SKILL.md`
- Conversational rules: `brainstorming/CONVERSATIONAL_MODE.md`
- Backend contract: `brainstorming/COMMANDS.md`
- Quickstart: `brainstorming/QUICKSTART.md`
- Example walkthrough: `brainstorming/EXAMPLE_LIFECYCLE.md`
- Shell runtime: `./scripts/lab <command> ...`
- Examples:
  - `./scripts/lab status`
  - `./scripts/lab doctor`
  - `./scripts/lab capture --idea-id idea-template-hardening --title "Template Hardening"`
  - `./scripts/lab activate --idea-id idea-template-hardening`
  - `./scripts/lab finalize --idea-id idea-template-hardening --write-export`
- Idea state files: `ideas/`
- Sessions: `sessions/`
- Notes: `notes/`
- Optional summaries: `exports/`

## Common Flows

Check current context and inferred finalize target:

```sh
./scripts/lab status
./scripts/lab doctor
```

Capture and activate an idea:

```sh
./scripts/lab capture --idea-id idea-template-hardening --title "Template Hardening"
./scripts/lab activate --idea-id idea-template-hardening
```

Record a decision, risk, and review:

```sh
./scripts/lab decide --idea-id idea-template-hardening --chosen-option "State-first finalize" --rationale "Preserve continuity"
./scripts/lab risk --idea-id idea-template-hardening --statement "Docs/runtime drift" --mitigation "Validate and test the full path"
./scripts/lab review --idea-id idea-template-hardening --result conditional-pass --summary "Ready after parity checks"
```

Create an optional summary snapshot before finalizing:

```sh
./scripts/lab export --idea-id idea-template-hardening
```

## Finalize In Place

Repo-scoped skill: `.agents/skills/project-finalizer/SKILL.md`

Check the inferred target and readiness first if needed:

```sh
./scripts/lab status
```

Then run:

```sh
./scripts/finalize-project
```

If needed, override the inferred current idea with:

```sh
./scripts/finalize-project --idea-id <idea-id>
```

If you also want an archival summary snapshot:

```sh
./scripts/finalize-project --write-export
```

This will:

1. Capture canonical project decisions in `state/project-init.json`.
2. Append a finalization session entry under `sessions/`.
3. Optionally generate a summary snapshot under `exports/`.
4. Render the development governance docs into `docs/`, `README.md`, `CHANGELOG.md`, and `.gitignore`.
5. Switch `MODE.md` to `development`.

## Development Phase

Repo-scoped skill: `.agents/skills/development-governance/SKILL.md`

After finalization, the active runtime rules come from `development/AGENTS.development.md` and the live governance docs under `docs/`.

## Template Maintenance

Repo-scoped skill: `.agents/skills/template-maintenance/SKILL.md`

Use this skill when changing the template runtime, generated intent mappings, validators, wrappers, development templates, repo-scoped skills, or plugin packaging.

When repo-scoped skills change, sync their plugin mirrors before validating:

```sh
./scripts/sync-plugin-skills
```

## Notes Policy

Research notes are retained across both phases in `notes/` and indexed in `NOTES_CATALOG.md`.

They are archival by default:

- not auto-loaded each session
- not part of the mandatory read path
- only searched when explicitly requested or referenced
