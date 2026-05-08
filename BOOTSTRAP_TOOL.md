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
- expected `state/project-init.json` schema version
- artifact ownership classes: harness-owned, project-owned, mixed/generated, and archival

Future `update` work should load this manifest rather than scraping Markdown
docs. Update tooling must preserve project-owned and archival paths by default
and classify mixed/generated paths conservatively.

## `update`

Bring harness-maintained files in an existing project up to date from a selected template version.

Status: deferred.

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
