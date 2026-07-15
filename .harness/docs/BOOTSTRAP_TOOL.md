# Harness Bootstrap Tool Sketch

This is the planning and implementation contract for the local `project-harness` helper.

The public template remains the canonical, inspectable harness. A bootstrap helper should make clone/update workflows easier without moving lifecycle runtime out of project repositories.

## Proposed Commands

```sh
./scripts/project-harness new <project-name>
project-harness update
./scripts/project-harness validate
```

The local `new`, `validate`, and explicit-source `update --dry-run`/`update --apply`
commands are implemented. Update sources can be local template checkouts,
40-character Git commits, or release tags resolved from the recorded template
repository.

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
- Normalizes every declared POSIX launcher to mode `100755` and records that mode
  in the initial Git index, including when the source copy lost local mode bits.
- Refuses to overwrite an existing target.
- Excludes local Git history and common cache/dependency directories.
- Stamps `.harness/commands/harness_manifest.json` with the source checkout commit when available.
- Initializes a fresh Git repository with no remote by default.
- Creates an initial commit by default.
- Adds `origin` only when `--origin` is supplied.
- Skips Git initialization only when `--no-git` is supplied.

## Harness Manifest

The checked-in manifest lives at `.harness/commands/harness_manifest.json`.
Validation treats it as the compatibility contract for generated projects.

The manifest records:

- manifest schema version and harness release version
- template repository URL and source commit provenance
- wrapper/runtime compatibility versions
- supported modes
- stable wrapper entrypoints and their backend commands
- POSIX launcher paths that must be distributed as mode `100755`
- expected `state/project-init.json` schema version and schema file path
- artifact ownership classes: harness-owned, project-owned, mixed/generated, and archival

Future `update` work should load this manifest rather than scraping Markdown
docs. Update tooling must preserve project-owned and archival paths by default
and classify mixed/generated paths conservatively.

Compatible state schema evolution ships through the harness-owned schema
artifact while `state/project-init.json` remains project-owned. Incompatible
changes must ship as a new schema artifact, update the manifest compatibility
entry, and include migration tests before finalization or rendering starts
writing the new version.

## Command Discovery

External adapters should read `.harness/commands/intent_registry.json` for the
allowlist-ready command surface. The registry records each `/lab` command's
supported modes, backend intent, required and optional arguments, wrapper path,
write behavior, read-only safety, mutation scope, and output/exit-code
expectations.

Do not discover command capability by scraping `.harness/commands/COMMANDS.md` or
by invoking repository scripts. Those Markdown docs are generated from the
registry for human review.

## `update`

Bring harness-maintained files in an existing project up to date from a selected template version.

Status: dry-run and conservative apply are implemented for explicit local source
checkouts, Git source commits, and Git release tags.

Current local interface:

```sh
./scripts/project-harness update --dry-run --source-path <template-checkout>
./scripts/project-harness update --dry-run --source-commit <40-char-sha>
./scripts/project-harness update --dry-run --release-version <version>
./scripts/project-harness update --apply --source-path <template-checkout> --yes
./scripts/project-harness update --apply --source-commit <40-char-sha> --yes
./scripts/project-harness update --apply --release-version <version> --yes
```

The dry-run command is implemented for an explicit local source checkout or a
40-character Git source commit. Release resolution checks out a matching Git
tag from the current project's recorded `templateRepository`, trying `v<version>`
before `<version>`. Commit and release resolution both use temporary detached
checkouts. The helper loads the current project's recorded harness manifest,
loads the source manifest, classifies candidate files by manifest ownership
class, and prints a deterministic no-write plan.

Apply mode is conservative. It applies only clean `harnessOwned` additions,
changes, and removals by default, refuses conflicts, refuses mixed/generated
paths unless `--include-mixed` is supplied, writes backups under
`.harness-update-backups/`, runs generated-file hooks when relevant, validates
before provenance stamping, then validates the stamped manifest. Review changed
paths with `git diff`. Mode-only launcher drift is a harness-owned update and is
repaired from the target manifest even when file bytes are unchanged.

Expected behavior:

1. Show a dry-run summary before changing files.
2. Preserve project-local state: `ideas/`, `sessions/`, `notes/`, `exports/`, `state/project-init.json`, and finalized `docs/`.
3. Deliver the harness-owned `state/project-init.schema.v2.json` with compatible runtime evolution while preserving the project-owned state instance.
4. Update reusable harness runtime files only after confirmation.
5. Run `./scripts/sync-plugin-skills` when repo-scoped skills change.
6. Run `./scripts/validate-governance`.

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
preserve `.harness/runtime/python/cli.py` as the repo-local fallback.

ADR-0004 defers official compiled binary, Homebrew, Cargo, and GitHub runtime
artifact install paths. Source archives and release notes may be published, but
no official external runtime artifact should be advertised until the first
read-only extraction proves compatibility, fallback, verification, and rollback
behavior.

The planned installed Python package is `project_harness_runtime` with a
`project-harness-runtime` console entrypoint. Wrappers may call
`project-harness-runtime version --json` for `runtimeVersion`,
`wrapperRuntimeVersion`, `capabilityVersion`, `stateSchemaVersion`, and
`supportedBackendCommands`, then compare those values with
`.harness/commands/harness_manifest.json`. Python 3.12 is the first supported
runtime baseline.

Only read-only validation and contract commands are eligible for the first
installed-runtime slice. Commands that write project state, generated docs,
plugin mirrors, update backups, or Git history remain repo-local until
compatibility, rollback, and fallback behavior are tested.

Compatibility failures follow ADR-0002's fail-open/fail-closed split. Read-only
commands may write `harness-runtime warning: installed runtime is incompatible;
using repo-local fallback at .harness/runtime/python/cli.py` to stderr and then exit with
the repo-local command's exit code. Mutating commands must write
`harness-runtime error: installed runtime is incompatible for mutating command;
refusing to continue` to stderr and exit 78 without running either runtime.

Candidate extraction order:

1. `validator_python_config.py`, exposed behind an internal
   `validate-python-config` backend that returns JSON failures/warnings while
   `./scripts/validate-governance` remains the user-facing command.
2. Other read-only contract and validation helpers.
3. Bootstrap/update planning after explicit source/version resolution is stable.
4. Render, finalize, and workflow mutation commands only after rollback and
   compatibility behavior are proven.

This section records the durable runtime-versioning conclusions: keep project
state and stable local wrappers in generated repositories, remove duplicated
mutable implementation only behind manifest-backed compatibility checks, and
avoid any global "latest" runtime dependency.
