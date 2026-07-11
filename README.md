# Project Harness Template

This public template is a project harness: a cloneable, repo-local operating environment for taking an idea from conversation into governed development.

The intended flow stays simple:

1. Clone this template into a new project repository.
2. Brainstorm the project in `brainstorming` mode.
3. Finalize in place into `development` mode.
4. Develop against the rendered governance docs.

The harness remains self-contained. Project state, deterministic scripts, validation, and generated development docs live in the repository. Plugins and skills provide agent operating knowledge around that harness; they do not replace the harness runtime.

## First 10 Minutes

For a brand-new clone, this is the whole loop:

```sh
./scripts/lab status                                            # confirm brainstorming mode, no ideas yet
./scripts/lab capture --idea-id my-idea --title "My Idea"       # capture the first idea
./scripts/lab activate --idea-id my-idea                        # make it the active thread
./scripts/lab decide --idea-id my-idea --chosen-option "..." --rationale "..."
./scripts/lab risk --idea-id my-idea --statement "..." --mitigation "..."
./scripts/lab review --idea-id my-idea --result conditional-pass --summary "..."
./scripts/lab doctor                                            # see exactly what finalize still needs
./scripts/finalize-project                                      # convert to development mode when ready
```

Milestone writes auto-commit (and push when `origin` exists) unless you pass `--no-sync`. Everything else in this README is reference detail around that loop.

## Agent Operation Model

This harness is optimized for human-agent development, not for humans memorizing commands. The primary interface is conversational intent; the scripts are the auditable implementation layer underneath.

1. The human describes what should happen in normal language.
2. The agent reads `MODE.md` and follows the active repo-scoped skill.
3. The agent maps natural-language requests through `.harness/commands/intent_registry.json` and the generated command docs.
4. The agent runs deterministic `./scripts/lab ...` or validation commands to persist state and evidence.
5. The agent reports the outcome, validation evidence, and the next decision point.

Examples: "capture this idea", "what's missing before finalize?", "finalize this repo", and "commit this milestone" are agent-facing intents. Terminal commands remain documented so the workflow is inspectable and recoverable.

## Command Discovery

External tools should discover supported workflow commands by reading
`.harness/commands/intent_registry.json`, not by scraping Markdown or executing
repository scripts. The registry is the machine-readable command and capability
surface: command names, modes, backend intents, required and optional arguments,
stable wrapper paths, write behavior, read-only safety, mutation scope, output
expectations, and exit-code meanings.

`.harness/commands/COMMANDS.md` and
`.harness/commands/CONVERSATIONAL_MODE.md` are generated views of that registry.
Run `./scripts/render-intent-docs` after changing the registry; governance
validation fails if the generated views drift.

## External Automation

External systems can seed brainstorming projects through the stable import commands documented in `docs/EXTERNAL_INTEGRATION.md`.

Prefer:

```sh
./scripts/lab import-idea --payload-file /tmp/example-idea.json --activate --create-session --json --no-sync
./scripts/project-harness new-from-idea /tmp/example-project --payload-file /tmp/example-idea.json --json
```

over editing `IDEA_CATALOG.md`, `ideas/_*.md`, or `sessions/*.md` directly. Automation examples in this public template must use generic placeholders only.

## Machine-Readable Output

Read-only status and validation commands keep human-readable output as the
default and support `--json` for adapters that need stable fields:

```sh
./scripts/lab status --json
./scripts/lab doctor --json
./scripts/project-harness update --dry-run --source-path <template-checkout> --json
./scripts/validate-governance --json
```

The JSON payloads use stable top-level keys for command identity, mode or target
context, write behavior, counts, failures, warnings, and next-command hints.
Adapters should treat unknown additional keys as forward-compatible metadata and
must not infer write behavior from human-readable text.

## Tooling Runtime

- Python 3 is required for the repository automation scripts under `scripts/`.
- The shell and PowerShell entrypoints are launchers; the canonical implementation lives in Python.
- The public template is MIT licensed. See `LICENSE`.
- Text files are normalized through `.gitattributes` and `.editorconfig` so generated docs and wrappers avoid accidental BOM or line-ending churn.
- `pyproject.toml` records Ruff, Black, and isort defaults for maintainers.
- `requirements-dev.txt` pins Ruff for local and CI lint/format checks.

PowerShell launchers prefer `py -3`, then `python3`, then `python`, so they also
work under PowerShell on macOS/Linux. Shell launchers prefer `python3` and fall
back to `python`.
CI runs on pull requests and manual dispatch; push triggers stay disabled in
brainstorming mode so milestone auto-commits do not spawn CI runs. The Ubuntu
job runs Ruff, mypy, generated-artifact drift checks, the full regression
suite, and governance plus brainstorming validation. The Windows job runs the
same regression suite through the PowerShell launchers plus launcher-specific
update and rendering smoke checks.

Runtime extraction is planned but not active. ADR-0002 records the boundary:
the first extracted runtime should remain Python, wrappers must verify manifest
compatibility before using an installed runtime, and `.harness/runtime/python/cli.py`
remains the local fallback for users without a global harness install.

## Harness Architecture

| Layer | Purpose | Examples |
|---|---|---|
| Project substrate | Durable project lifecycle state and retained docs | `MODE.md`, `ideas/`, `sessions/`, `notes/`, `exports/`, `state/` |
| Deterministic tooling | Repeatable local behavior that should remain inspectable in each project | `./scripts/lab`, `./scripts/finalize-project`, `./scripts/validate-governance`, `.harness/runtime/python/template_cli/` |
| Repo-scoped skills | Canonical agent instructions for operating this harness in the current repo | `.agents/skills/` |
| Plugin package | Optional portable distribution of reusable agent behavior | `.harness/plugins/project-lifecycle-lab/` |
| Bootstrap/update helper | Optional convenience for creating/updating harness instances | `.harness/docs/BOOTSTRAP_TOOL.md` |

`.harness/docs/HARNESS_IMPROVEMENT_ROADMAP.md` tracks public-template improvement milestones.
`.harness/docs/HARNESS_RELEASE_CHECKLIST.md` and `.harness/docs/HARNESS_CHANGELOG.md` track template release
readiness and release notes separately from generated project changelogs.
Before dispatching the manual release-readiness workflow, maintainers can run
the local release checks with `./scripts/harness-release-check`.

## Harness Manifest

`.harness/commands/harness_manifest.json` records the template provenance and
compatibility contract a generated project expects. It includes the manifest
schema version, harness release version, template repository URL, source commit
provenance, supported modes, stable wrapper entrypoints, the expected
`state/project-init.json` schema version and schema file path, and artifact
ownership classes for conservative update dry-run and apply tooling. The
`posixExecutablePaths` inventory is the distribution contract for launchers that
must remain mode `100755` in generated repositories and source archives.

In the template repository, `sourceCommitType` is `template`. When
`./scripts/project-harness new` creates a project from a Git checkout, it stamps
the generated copy with the source checkout's exact 40-character commit SHA and
sets `sourceCommitType` to `git`. The `sourceWorktreeDirty` flag records whether
the source checkout had uncommitted changes at generation time. If the source is
not a Git checkout, the copy is stamped as `unknown` instead of inventing
provenance.

## Using This Public Harness

Start each real project from its own clone or generated repository. The harness is meant to travel with the project so brainstorming history, finalization evidence, governance docs, and local scripts remain inspectable in the same Git history as the implementation work.

After creating a project repo:

1. Point `origin` at the new project remote.
2. Keep `MODE.md` as `brainstorming` until finalization.
3. Use `./scripts/lab status` and `./scripts/lab doctor` to check readiness.
4. Treat `ideas/`, `sessions/`, `notes/`, `exports/`, and `state/project-init.json` as project-local brainstorming history.
5. Run `./scripts/finalize-project` only when the project definition is ready to become development governance.

The public template should stay generic. Project-specific product decisions belong in idea records, sessions, notes, and finalized development docs, not in the reusable harness scripts or template-maintenance skills.

To create a fresh harness copy from a local checkout:

```sh
./scripts/project-harness new ../my-project
```

This creates an independent Git repository with a baseline commit and no remote. Pass `--origin <url>` only when you want to connect the new project to its own remote.

To inspect available lab commands:

```sh
./scripts/lab --help
./scripts/lab help
```

## Start Here

- Read `AGENTS.md`
- Confirm `MODE.md` is `brainstorming`
- Use the brainstorming workflow in `.harness/brainstorming/`

## Mode Guide

| Mode | Read First | Main Runtime | Main Goal |
|---|---|---|---|
| `brainstorming` | `.agents/skills/brainstorming-lab/SKILL.md` or `.harness/brainstorming/AGENTS.brainstorming.md` | `./scripts/lab <command> ...` | Capture ideas, decisions, risks, and canonical project intent |
| `development` | `.agents/skills/development-governance/SKILL.md` or `.harness/development/AGENTS.development.md` | governance docs under `docs/` | Execute delivery work against the finalized project definition |

## Brainstorming Phase

- Repo-scoped skill: `.agents/skills/brainstorming-lab/SKILL.md`
- Conversational rules: `.harness/commands/CONVERSATIONAL_MODE.md`
- Backend contract: `.harness/commands/COMMANDS.md`
- Quickstart: `.harness/brainstorming/QUICKSTART.md`
- Example walkthrough: `.harness/brainstorming/EXAMPLE_LIFECYCLE.md`
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

Finalization is non-interactive by default. If the inferred idea has complete canonical state, it converts directly. If required fields are missing or multiple active ideas make the target ambiguous, it stops with explicit fix-up guidance instead of prompting.

If needed, override the inferred current idea with:

```sh
./scripts/finalize-project --idea-id <idea-id>
```

To use the older prompt-fill flow:

```sh
./scripts/finalize-project --interactive
```

If you also want an archival summary snapshot:

```sh
./scripts/finalize-project --write-export
```

This will:

1. Capture canonical project decisions in `state/project-init.json`.
2. Append a finalization session entry under `sessions/`.
3. Optionally generate a summary snapshot under `exports/`.
4. Move brainstorming history into `.harness/history/` before development validation.
4. Render the development governance docs into `docs/`, `README.md`, `CHANGELOG.md`, and `.gitignore`.
5. Switch `MODE.md` to `development`.

`state/project-init.json` uses schemaVersion 2, with the checked-in contract at
`state/project-init.schema.v2.json`. Draft state keeps the full canonical shape
but may leave values empty while brainstorming. Finalized state must include the
non-empty product, governance, session, and ADR fields required to render and
validate development mode.

Finalized schema v2 also accepts an optional `finalizedContract` object for
structured ownership boundaries, invariants, domain/data model details, public
contracts, version domains, ordered milestones, and deferred scope. Renderers
prefer that structure when present and fall back to legacy prose fields for
older states.

Generated development docs include a GitHub Actions baseline by default. Set
`documentation.ciPolicy` in `state/project-init.json` before rendering when a
project needs different CI versus local verification wording.

Future state schema changes should add a new schema file, update
`.harness/commands/harness_manifest.json` compatibility metadata, keep fixture
coverage for old and new valid states, and include an explicit migration path
before changing finalization or rendering behavior.

## Development Phase

Repo-scoped skill: `.agents/skills/development-governance/SKILL.md`

After finalization, the active runtime rules come from `.harness/development/AGENTS.development.md` and the live governance docs under `docs/`.

## Template Maintenance

Repo-scoped skill: `.agents/skills/template-maintenance/SKILL.md`

Use this skill when changing the template runtime, generated intent mappings, validators, wrappers, development templates, repo-scoped skills, or plugin packaging.

When repo-scoped skills change, sync their plugin mirrors before validating:

```sh
./scripts/sync-plugin-skills
```

Repo-scoped skills are canonical for this template because they can reference
local state, scripts, validators, and governance docs directly. The
`.harness/plugins/project-lifecycle-lab/` package is an optional distribution mirror for
portable agent behavior; it must not replace repo-local runtime state or
validation. The current harness and plugin version is `0.1.1`; keep the plugin
version aligned with the harness version and use
`.harness/plugins/project-lifecycle-lab/README.md` for the external smoke-check steps.

## Notes Policy

Research notes start in `notes/` during brainstorming and move to `.harness/history/notes/` during finalization.

They are archival by default:

- not auto-loaded each session
- not part of the mandatory read path
- only searched when explicitly requested or referenced

Capture detailed notes with structured fields so the saved note is useful without
manual cleanup:

```sh
./scripts/lab-note \
  --topic "Service identity boundary" \
  --summary "External integrations may eventually need dedicated service identities." \
  --detail "A GitHub App is preferred over a broad bot account for most repo workflows." \
  --fact "Secrets must stay outside git." \
  --question "Should inbound email be read-only at first?"
```

For longer captures, use `--details-file`, `--facts-file`, `--questions-file`,
or `--links-file`; pass `-` to one file option to read that section from stdin.
