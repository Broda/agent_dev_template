# Master Codex Template

This template starts in brainstorming mode and finalizes in place into development mode.

## Tooling Runtime

- Python 3 is required for the repository automation scripts under `scripts/`.
- The shell and PowerShell entrypoints are launchers; the canonical implementation lives in Python.

## Start Here

- Read `AGENTS.md`
- Confirm `MODE.md` is `brainstorming`
- Use the brainstorming workflow in `brainstorming/`

## Brainstorming Phase

- Conversational rules: `brainstorming/CONVERSATIONAL_MODE.md`
- Backend contract: `brainstorming/COMMANDS.md`
- Quickstart: `brainstorming/QUICKSTART.md`
- Shell runtime: `./scripts/lab <command> ...`
- Examples:
  - `./scripts/lab capture --idea-id idea-template-hardening --title "Template Hardening"`
  - `./scripts/lab activate --idea-id idea-template-hardening`
  - `./scripts/lab finalize --idea-id idea-template-hardening --write-export`
- Idea state files: `ideas/`
- Sessions: `sessions/`
- Notes: `notes/`
- Optional summaries: `exports/`

## Finalize In Place

Run:

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

After finalization, the active runtime rules come from `development/AGENTS.development.md` and the live governance docs under `docs/`.

## Notes Policy

Research notes are retained across both phases in `notes/` and indexed in `NOTES_CATALOG.md`.

They are archival by default:

- not auto-loaded each session
- not part of the mandatory read path
- only searched when explicitly requested or referenced
