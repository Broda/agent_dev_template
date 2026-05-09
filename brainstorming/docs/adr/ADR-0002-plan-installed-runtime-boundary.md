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
