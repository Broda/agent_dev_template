# Project Lifecycle Lab Plugin

This plugin packages reusable Codex operating knowledge for project harness templates.

The plugin is intentionally not the project runtime. Canonical project state, deterministic scripts, validators, generated development docs, and local workflow history stay in the harness repository.
Current plugin version: `0.1.0`.

## Packaging Decision

- `.agents/skills/` remains the canonical skill source for this template.
- `plugins/project-lifecycle-lab/skills/` contains copied mirrors for distribution.
- The plugin manifest exposes those mirrors through `./skills/`.
- The local plugin marketplace points at `./plugins/project-lifecycle-lab`.
- Copied mirrors remain checked in until plugin packaging needs release-time generation.
- `./scripts/sync-plugin-skills` is the maintenance path for refreshing plugin mirrors.
- `./scripts/validate-governance` validates manifest shape, marketplace registration, mirror drift, and the harness/plugin boundary wording.
- The plugin `version` stays aligned with `harness_commands/harness_manifest.json` `harnessVersion`.

ADR-0003 records the plugin mirror ownership decision. Generated plugin mirrors are deliberately deferred. Copied mirrors are simpler to inspect in a public template, and drift validation keeps the package honest until there is a stronger reason to generate plugin artifacts.

## Workflow Boundary

Repo-scoped skills under `.agents/skills/` are the source of truth for operating
this repository. They can reference local state, validators, wrappers, generated
docs, and template-maintenance rules directly.

Portable plugin skills under `plugins/project-lifecycle-lab/skills/` are
distribution mirrors. They may teach the same lifecycle workflow, but they must not replace repo-local scripts, validators, state files, or governance docs.
If repo-scoped skills change, run `./scripts/sync-plugin-skills` and then
`./scripts/validate-governance`.

## External Use Check

To smoke-check the package outside the repo context, install or expose `plugins/project-lifecycle-lab` as a local Codex plugin and confirm the four skills are visible:

```sh
python3 smoke_package.py
```

- `brainstorming-lab`
- `development-governance`
- `project-finalizer`
- `template-maintenance`

Each skill should describe the harness workflow and should treat repo scripts and state as canonical.
