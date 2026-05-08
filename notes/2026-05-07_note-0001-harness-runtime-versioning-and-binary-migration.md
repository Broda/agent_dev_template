# Research Note

## Metadata

- Note ID: note-0001
- Title: Harness runtime versioning and binary migration
- Date: 2026-05-07
- Related Idea ID: n/a
- Source Context: Codex discussion
- Tags: harness,versioning,binary,rust,devos,public-template

## Captured Information

- Discussed preserving the brainstorming to handoff/finalize to development workflow while reducing copied harness baggage in generated projects. The preferred direction is repo-local project state plus stable wrapper command paths, with harness implementation moving toward a versioned canonical runtime that may eventually be compiled as a Rust binary.
- Generated projects should keep project-owned artifacts such as MODE.md, state/project-init.json, roadmap, ADRs, notes, and governance records. They should also keep stable local command affordances such as ./scripts/lab, ./scripts/finalize-project, and ./scripts/validate-governance so agents and users have predictable entrypoints. The duplicated implementation under scripts/python/template_cli and related validators/renderers is the part that should eventually stop being copied wholesale into every project.
- For public template users, an opaque binary should not be the only trust path. The harness should remain inspectable from source, while a versioned CLI such as project-harness can be installed from Cargo/Homebrew/GitHub releases later. Thin generated wrappers can delegate to that runtime after checking compatibility.
- A generated project should record both a human release version and exact harness commit provenance. Commit IDs provide reproducibility and a clean update base; semver or a schema/capability version communicates compatibility. Wrappers and tools such as DevOS can check the installed harness runtime against the recorded commit/version before executing commands.
- Commit provenance enables safer project updates: project-harness update can diff old harness commit, target harness commit, and current project files, then apply only harness-owned changes. This supports update plans that distinguish harness-owned files, project-owned files, and mixed/generated files requiring review or managed regions.
- DevOS makes this design more important because it is moving toward a read-only harness command adapter. DevOS should eventually discover harness capabilities through a manifest and execute fixed allowlisted commands instead of treating each repository as an arbitrary folder of copied scripts.

## Key Facts / Constraints

- The long-term target is not to remove local commands, but to remove duplicated mutable implementation while preserving stable command UX.
- Do not rely on a global latest harness runtime. Generated projects should pin or record the expected harness commit/version and compatibility contract.
- Harness update tooling should classify files as harness-owned, project-owned, or mixed/generated before applying changes.

## Open Questions / Follow-ups

- Should the harness expose a machine-readable command/capability manifest before or alongside any Rust binary migration?
- What files should be considered harness-owned after finalization, and which should become project-owned forever?

## Links

- Referenced local DevOS context during discussion: DevOS ADR-0010, "Read-Only Harness Command Adapter Boundary".
- Referenced local DevOS roadmap during discussion: DevOS Milestone 7, "Read-Only Harness Command Adapter".
