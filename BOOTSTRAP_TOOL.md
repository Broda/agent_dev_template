# Harness Bootstrap Tool Sketch

This is the planning and implementation contract for the local `project-harness` helper.

The public template remains the canonical, inspectable harness. A bootstrap helper should make clone/update workflows easier without moving lifecycle runtime out of project repositories.

## Proposed Commands

```sh
./scripts/project-harness new <project-name>
project-harness update
./scripts/project-harness validate
```

The local `new` and `validate` commands are implemented. `update` remains deferred until the safe refresh boundary is designed in more detail.

## `new`

Create a new project repository from this harness template.

Expected behavior:

1. Copy or clone the harness into `<project-name>`.
2. Initialize a fresh independent Git repository by default.
3. Point `origin` at the user-provided project remote when one is supplied.
4. Leave `MODE.md` as `brainstorming`.
5. Run `./scripts/validate-governance`.

The command should not collect project product requirements. Those belong in brainstorming records after the harness exists.

Current local interface:

```sh
./scripts/project-harness new <path> [--origin <url>] [--no-git]
```

Behavior:

- Copies the harness working tree to a new path.
- Refuses to overwrite an existing target.
- Excludes local Git history and common cache/dependency directories.
- Stamps `harness_commands/harness_manifest.json` with the source checkout commit when available.
- Initializes a fresh Git repository with no remote by default.
- Creates an initial commit by default.
- Adds `origin` only when `--origin` is supplied.
- Skips Git initialization only when `--no-git` is supplied.

## Harness Manifest

The checked-in manifest lives at `harness_commands/harness_manifest.json`.
Validation treats it as the compatibility contract for generated projects.

The manifest records:

- manifest schema version and harness release version
- template repository URL and source commit provenance
- wrapper/runtime compatibility versions
- supported modes
- stable wrapper entrypoints and their backend commands
- expected `state/project-init.json` schema version and schema file path
- artifact ownership classes: harness-owned, project-owned, mixed/generated, and archival

Future `update` work should load this manifest rather than scraping Markdown
docs. Update tooling must preserve project-owned and archival paths by default
and classify mixed/generated paths conservatively.

State schema changes must ship as a new schema artifact, update the manifest
compatibility entry, and include migration tests before finalization or
rendering starts writing the new version.

## Command Discovery

External adapters should read `harness_commands/intent_registry.json` for the
allowlist-ready command surface. The registry records each `/lab` command's
supported modes, backend intent, required and optional arguments, wrapper path,
write behavior, read-only safety, mutation scope, and output/exit-code
expectations.

Do not discover command capability by scraping `harness_commands/COMMANDS.md` or
by invoking repository scripts. Those Markdown docs are generated from the
registry for human review.

## `update`

Bring harness-maintained files in an existing project up to date from a selected template version.

Status: dry-run and conservative apply are implemented for explicit local source
checkouts. Release/source resolution remains deferred.

Current local interface:

```sh
./scripts/project-harness update --dry-run --source-path <template-checkout>
./scripts/project-harness update --apply --source-path <template-checkout> --yes
```

The dry-run command is implemented for an explicit local source checkout. It
loads the current project's recorded harness manifest, loads the source
manifest, classifies candidate files by manifest ownership class, and prints a
deterministic no-write plan. `--source-commit` and `--release-version` are
reserved explicit source selectors; until release/source resolution exists, the
local helper refuses them with guidance to use `--source-path`.

Apply mode is conservative. It applies only clean `harnessOwned` paths by
default, refuses conflicts, refuses mixed/generated paths unless
`--include-mixed` is supplied, writes backups under `.harness-update-backups/`,
runs generated-file hooks when relevant, validates before provenance stamping,
then validates the stamped manifest. Review changed paths with `git diff`.

Expected behavior:

1. Show a dry-run summary before changing files.
2. Preserve project-local state: `ideas/`, `sessions/`, `notes/`, `exports/`, `state/project-init.json`, and finalized `docs/`.
3. Update reusable harness runtime files only after confirmation.
4. Run `./scripts/sync-plugin-skills` when repo-scoped skills change.
5. Run `./scripts/validate-governance`.

## `validate`

Run the same local checks the harness already exposes.

Current local interface:

```sh
./scripts/project-harness validate
```

Expected behavior:

1. Run `./scripts/validate-governance`.
2. If `MODE.md` is `development`, also run `./scripts/validate-development`.
3. Report commands and exit codes without hiding local validation output.

## Boundary

The bootstrap helper is convenience tooling. It must not become the source of truth for project state, finalization behavior, validation rules, or agent instructions.

## Installed Runtime Study

ADR-0002 defines the long-term runtime extraction direction. The first
extracted runtime should remain Python and should be installable from an
explicit source checkout or GitHub release archive before any Cargo, Homebrew,
or standalone binary path is considered. Thin wrappers may discover an installed
runtime later, but they must validate the recorded harness manifest first and
preserve `scripts/python/cli.py` as the repo-local fallback.

Candidate extraction order:

1. Read-only contract and validation helpers.
2. Bootstrap/update planning after explicit source/version resolution is stable.
3. Render, finalize, and workflow mutation commands only after rollback and
   compatibility behavior are proven.
