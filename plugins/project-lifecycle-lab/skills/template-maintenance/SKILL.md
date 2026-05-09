---
name: template-maintenance
description: Use when editing this project harness template itself, including scripts/python/template_cli, generated intent docs, validators, wrappers, development templates, repo-scoped skills, or plugin packaging.
---

# Template Maintenance

Use this skill when maintaining the harness template rather than brainstorming a user project or developing a finalized generated project.

## Source Of Truth

- Python under `scripts/python/template_cli/` is the canonical tooling implementation.
- Shell and PowerShell entrypoints should stay thin wrappers.
- `harness_commands/intent_registry.json` is the source for generated intent tables.
- Development docs are rendered from `development/templates/` and `state/project-init.json`.

## Editing Rules

- Keep command names and entrypoint paths stable unless the user explicitly asks for a breaking change.
- Update `brainstorming/FILE_MAP.md` when the retained harness template inventory changes.
- Review `HARNESS_IMPROVEMENT_ROADMAP.md` for public-template behavior, inventory, workflow, or packaging changes; update or check off the relevant roadmap/backlog item in the same slice.
- Update tests or fixtures when behavior changes.
- Do not hand-edit generated intent tables in `harness_commands/CONVERSATIONAL_MODE.md` or `harness_commands/COMMANDS.md`.
- To change natural-language mappings, edit `harness_commands/intent_registry.json`, run `./scripts/render-intent-docs`, then validate.

## Verification

Run targeted checks first, then the full suite before completion:

- `./scripts/validate-governance`
- `python3 -m unittest discover -s tests -v`

When renderer/finalizer behavior changes, also validate rendered development docs with existing fixtures through the regression suite.

## Skill And Plugin Work

- Keep `SKILL.md` concise and task-focused.
- Put deterministic behavior in scripts when a workflow is fragile or repeated.
- Start skills repo-scoped under `.agents/skills`; package as a plugin only after the workflow proves reusable.
- After changing repo-scoped skills, run `./scripts/sync-plugin-skills` so plugin mirrors stay in lockstep.
