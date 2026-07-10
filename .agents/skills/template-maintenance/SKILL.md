---
name: template-maintenance
description: Use when editing this project harness template itself, including .harness/runtime/python/template_cli, generated intent docs, validators, wrappers, development templates, repo-scoped skills, or plugin packaging.
---

# Template Maintenance

Use this skill when maintaining the harness template rather than brainstorming a user project or developing a finalized generated project.

## Source Of Truth

- Python under `.harness/runtime/python/template_cli/` is the canonical tooling implementation.
- Shell and PowerShell entrypoints should stay thin wrappers.
- `.harness/commands/intent_registry.json` is the source for generated intent tables.
- Development docs are rendered from `.harness/development/templates/` and `state/project-init.json`.

## Editing Rules

- Keep command names and entrypoint paths stable unless the user explicitly asks for a breaking change.
- Update `.harness/brainstorming/FILE_MAP.md` when the retained harness template inventory changes.
- Review `.harness/docs/HARNESS_IMPROVEMENT_ROADMAP.md` for public-template behavior, inventory, workflow, or packaging changes; update or check off the relevant roadmap/backlog item in the same slice.
- Update tests or fixtures when behavior changes.
- Keep every path in the manifest's `posixExecutablePaths` at mode `100755`; generation, update/apply, and release checks must preserve that contract.
- Do not hand-edit generated intent tables in `.harness/commands/CONVERSATIONAL_MODE.md` or `.harness/commands/COMMANDS.md`.
- To change natural-language mappings, edit `.harness/commands/intent_registry.json`, run `./scripts/render-intent-docs`, then validate.
- For external idea ingestion, keep `docs/EXTERNAL_INTEGRATION.md`, `lab import-idea`, and `project-harness new-from-idea` public-safe: examples must use generic placeholders and callers must not edit catalog, bucket, or session internals directly.

## Verification

Run targeted checks first, then the full suite before completion:

- `./scripts/validate-governance`
- `python3 -m unittest discover -s .harness/tests -v`

When renderer/finalizer behavior changes, also validate rendered development docs with existing fixtures through the regression suite.

## Skill And Plugin Work

- Keep `SKILL.md` concise and task-focused.
- Put deterministic behavior in scripts when a workflow is fragile or repeated.
- Start skills repo-scoped under `.agents/skills`; package as a plugin only after the workflow proves reusable.
- After changing repo-scoped skills, run `./scripts/sync-plugin-skills` so plugin mirrors stay in lockstep.
