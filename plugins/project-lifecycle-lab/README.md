# Project Lifecycle Lab Plugin

This plugin packages reusable Codex operating knowledge for project harness templates.

The plugin is intentionally not the project runtime. Canonical project state, deterministic scripts, validators, generated development docs, and local workflow history stay in the harness repository.

## Packaging Decision

- `.agents/skills/` remains the canonical skill source for this template.
- `plugins/project-lifecycle-lab/skills/` contains copied mirrors for distribution.
- `./scripts/sync-plugin-skills` is the maintenance path for refreshing plugin mirrors.
- `./scripts/validate-governance` validates manifest shape, marketplace registration, mirror drift, and the harness/plugin boundary wording.

Generated plugin mirrors are deliberately deferred. Copied mirrors are simpler to inspect in a public template, and drift validation keeps the package honest until there is a stronger reason to generate plugin artifacts.

## External Use Check

To smoke-check the package outside the repo context, install or expose `plugins/project-lifecycle-lab` as a local Codex plugin and confirm the four skills are visible:

- `brainstorming-lab`
- `project-finalizer`
- `development-governance`
- `template-maintenance`

Each skill should describe the harness workflow and should treat repo scripts and state as canonical.
