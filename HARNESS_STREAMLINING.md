# Harness Streamlining Phase

This note records the close of the harness-first streamlining phase that began at the annotated tag `before-skills-plugin-streamline`.

## Done In This Phase

- Reframed the public repository as a project harness template.
- Kept deterministic lifecycle tooling inside the repo.
- Established `.agents/skills` as the canonical repo-scoped agent layer.
- Packaged mirrored plugin skills under `plugins/project-lifecycle-lab/skills/`.
- Added plugin mirror drift validation and `./scripts/sync-plugin-skills`.
- Added a bootstrap-tool contract without moving runtime behavior into a global tool.
- Split large validation, rendering, and workflow modules into smaller helper modules.
- Added guardrails for plugin boundary language, launcher consistency, module boundaries, Python file size, and FILE_MAP coverage.

## Current Boundary

The repository remains the source of truth for project state and deterministic behavior:

- `MODE.md`
- `ideas/`
- `sessions/`
- `notes/`
- `exports/`
- `state/project-init.json`
- `scripts/`
- `scripts/python/template_cli/`
- generated development governance docs after finalization

The plugin package is a portable agent-behavior layer. It should not own project state, validators, finalization behavior, or generated governance docs.

## Deferred To Next Phase

- Build an actual `project-harness new/update/validate` helper if the documented bootstrap contract proves worth automating.
- Decide whether plugin skill mirrors should remain copied or become generated artifacts.
- Continue tactical module cleanup only when it reduces real maintenance pressure.
- Validate the plugin package in an external install/use path when the local plugin workflow is ready for that test.

## Completion Check

This phase is complete when:

- `./scripts/validate-governance` passes.
- `python3 -m unittest discover -s tests -v` passes.
- `git status --short --branch` is clean.
- `main` is pushed to `origin`.
