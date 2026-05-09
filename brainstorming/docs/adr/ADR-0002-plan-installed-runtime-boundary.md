# ADR-0002: Plan Installed Runtime Boundary

- Status: Accepted
- Date: 2026-05-09
- Deciders: template-maintainers
- Technical Story: Prepare for a versioned installed harness runtime without hiding behavior from generated project repositories.
- Related Ideas: harness-improvement-roadmap-ms9
- Supersedes:
- Superseded by:

## Context and Problem Statement

The harness currently copies Python runtime modules into every generated
project. This keeps behavior inspectable and local, but it also duplicates
runtime code across downstream repositories. A future installed runtime could
reduce duplication, but only if generated projects still record exactly which
runtime they expect and can keep working without a global install.

## Decision Drivers

- Preserve stable repo-local commands: `./scripts/lab`, `./scripts/finalize-project`, and `./scripts/validate-governance`.
- Keep generated projects auditable without requiring trust in a mutable global "latest" runtime.
- Avoid introducing binary distribution before the Python runtime boundary is stable.
- Keep fallback behavior available for users who clone a project without installing any external harness tool.
- Make compatibility checks explicit through `harness_commands/harness_manifest.json`.

## Considered Options

1. Keep copying the full Python runtime forever
- Pros: maximum inspectability, no external install path, simplest recovery.
- Cons: duplicated updates, larger downstream diffs, harder long-term release management.

2. Extract a Python package/runtime first, with local source fallback
- Pros: preserves current implementation language, supports versioned installs, allows gradual module migration, keeps local fallback.
- Cons: requires wrapper/runtime compatibility checks and release discipline.

3. Move directly to a compiled binary runtime
- Pros: simple single executable for users, easier Homebrew/Cargo-style distribution later.
- Cons: premature rewrite pressure, harder source inspection, larger compatibility risk.

## Decision Outcome

Use option 2 as the first extraction direction: a Python installed runtime may
be introduced after the compatibility contract is stable. Compiled binaries are
deferred until a later ADR proves there is enough operational value to justify
the packaging and inspection tradeoff.

No current wrapper should stop using the checked-in local runtime as part of
this ADR. Runtime extraction remains a future implementation boundary, not a
behavior change in this milestone.

## Runtime Discovery Contract

Future thin wrappers should resolve runtime in this order:

1. An explicit environment override for a harness runtime command or source checkout.
2. A versioned installed runtime whose version and capabilities match `harness_commands/harness_manifest.json`.
3. The repository-local fallback at `scripts/python/cli.py`.

If an installed runtime is present but incompatible, wrappers must print a clear
compatibility error and either fall back to the local runtime or explain why
fallback is unsafe for that command.

## Compatibility Error Policy

Runtime compatibility problems must be reported on stderr so stdout remains
machine-readable for commands that emit structured output. Messages should use
stable prefixes:

- `harness-runtime warning:` for recoverable read-only fallback.
- `harness-runtime error:` for non-recoverable compatibility failure.

For read-only commands, an incompatible installed runtime may fall back to the
repo-local runtime when `scripts/python/cli.py` is present and the wrapper can
prove that the backend command is read-only in `harness_commands/intent_registry.json`
or `harness_commands/harness_manifest.json`. The warning format is:

```text
harness-runtime warning: installed runtime is incompatible; using repo-local fallback at scripts/python/cli.py
```

After fallback, the wrapper must exit with the repo-local command's exit code.
If no repo-local fallback is available, the wrapper must fail with exit code 78
and this stderr format:

```text
harness-runtime error: installed runtime is incompatible and repo-local fallback is unavailable
```

For mutating commands, incompatible installed runtimes must fail closed without
running the installed runtime or repo-local fallback. The stderr format is:

```text
harness-runtime error: installed runtime is incompatible for mutating command; refusing to continue
```

The exit code must be 78. A mutating command may run through the repo-local
runtime only when no installed runtime is selected or when an explicit
environment override points directly at the repo-local runtime.

## Installed Python Runtime Interface

The first installed runtime interface should be a Python package named
`project_harness_runtime` with one console entrypoint:

```sh
project-harness-runtime BACKEND_COMMAND [args]
```

The package should support Python 3.12 as the release baseline and may support
newer CPython versions after CI proves compatibility. The package layout should
keep public adapter modules separate from implementation modules:

- `project_harness_runtime.__main__` for `python -m project_harness_runtime`
- `project_harness_runtime.cli` for console entrypoint dispatch
- `project_harness_runtime.compat` for manifest/runtime compatibility checks
- `project_harness_runtime.commands` for stable backend command adapters
- `project_harness_runtime.template_cli` only as an internal compatibility
  namespace while modules are migrated out of repo-local source

The version interface must be machine-readable:

```sh
project-harness-runtime version --json
```

It should print a JSON object with `runtimeVersion`, `pythonPackage`,
`pythonVersion`, `wrapperRuntimeVersion`, `capabilityVersion`,
`stateSchemaVersion`, and `supportedBackendCommands`. Human-readable
`project-harness-runtime --version` may exist, but wrappers must use
`version --json`.

Generated wrappers may read compatibility metadata only from the checked-in
`harness_commands/harness_manifest.json` and the installed runtime version JSON.
They must not import private package modules or inspect package internals.

The first extraction slice may expose only read-only backend commands through
the installed runtime, such as manifest validation, artifact inventory
validation, intent registry validation, launcher validation, plugin/skill
validation, Python config validation, and state schema validation. Mutating
commands must remain repo-local in the first slice, including `lab-*`,
`finalize-project`, `render-development-docs`, `render-intent-docs`,
`sync-plugin-skills`, and `project-harness update --apply`.

## Compatibility Checks

The installed runtime must validate:

- manifest schema version
- harness version or compatible runtime version
- `compatibility.wrapperRuntimeVersion`
- `compatibility.capabilityVersion`
- `compatibility.stateSchemaVersion`
- stable wrapper command names and backend command mappings

Runtime validation must not depend on scraping Markdown docs.

## Release And Install Plan

The first release path should be a plain source checkout or GitHub release
archive containing the Python runtime. Homebrew, Cargo, and standalone binary
distribution are deferred until there is a separate ADR for compiled or packaged
runtime delivery.

Generated projects must continue to record source commit provenance, and update
tooling must continue to operate against explicit source paths or explicit
versions rather than a mutable latest runtime.

## Candidate Module Migration

Runtime modules can be considered for extraction in this order:

1. Read-only contract and validation helpers such as intent rendering, manifest validation, launcher checks, skill/plugin validation, and state schema validation.
2. Project-harness bootstrap/update planning once source and version resolution are stable.
3. Render/finalize/workflow mutation commands only after state schema, backup, and local fallback behavior are stable.

Modules that mutate project history, state, or generated docs must remain
repo-local until rollback and compatibility behavior are proven by tests.

## First Extraction Target

The first read-only validation target should be
`scripts/python/template_cli/validator_python_config.py`.

Rationale:

- It reads only `pyproject.toml`.
- It has no subprocess, mode, manifest, plugin, skill, state, or generated-doc
  dependencies.
- Its current contract is deterministic: report missing required sections and
  snippets through a validation result.
- A failed extraction can be reverted without changing project state,
  finalization, rendering, update planning, or wrapper command names.

The installed runtime adapter should expose an internal backend named
`validate-python-config`. Repo-local `./scripts/validate-governance` remains
the user-facing command. During extraction, the local validation orchestrator
may resolve `validate-python-config` through runtime discovery and then merge
the adapter's findings into the normal governance validation summary. If no
compatible installed runtime is available, the existing repo-local validator
continues to run.

The adapter should accept a repository root path and return machine-readable
JSON:

```json
{
  "failures": [],
  "warnings": []
}
```

It must not write files, mutate environment, inspect Git state, or import
private wrapper modules. The repo-local and installed-runtime implementations
must produce identical failure strings for the same `pyproject.toml`.

## Consequences

### Positive

- Gives maintainers a clear migration path without committing to a binary rewrite.
- Keeps the local project repository inspectable and self-contained.
- Makes runtime compatibility a manifest-backed contract.

### Negative

- Requires wrappers to handle discovery and compatibility states carefully.
- Leaves runtime duplication in place until the extraction boundary is proven.

### Neutral

- Current commands and local scripts keep their behavior.
- Future release tooling remains optional.

## Alternatives Considered But Rejected

- Use a global latest runtime with no recorded project compatibility.
- Why rejected: generated projects would become dependent on mutable external behavior.

- Remove local runtime fallback once an installed runtime exists.
- Why rejected: it would break the template's inspectable, repo-local recovery model.

## Implementation Notes

- Required updates: document this ADR, update bootstrap/runtime docs, keep roadmap Milestone 9 tied to this decision.
- Affected files: `README.md`, `BOOTSTRAP_TOOL.md`, `HARNESS_IMPROVEMENT_ROADMAP.md`, `brainstorming/FILE_MAP.md`.
- Follow-up actions: add runtime discovery implementation only after a separate scoped milestone defines the installed package interface and tests.
