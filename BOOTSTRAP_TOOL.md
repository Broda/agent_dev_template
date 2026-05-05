# Harness Bootstrap Tool Sketch

This is a planning contract for a possible future `project-harness` helper. It is not required for current use.

The public template remains the canonical, inspectable harness. A bootstrap helper should make clone/update workflows easier without moving lifecycle runtime out of project repositories.

## Proposed Commands

```sh
project-harness new <project-name>
project-harness update
project-harness validate
```

## `new`

Create a new project repository from this harness template.

Expected behavior:

1. Copy or clone the harness into `<project-name>`.
2. Reset Git history only when the user explicitly asks for a fresh initial commit.
3. Point `origin` at the user-provided project remote when one is supplied.
4. Leave `MODE.md` as `brainstorming`.
5. Run `./scripts/validate-governance`.

The command should not collect project product requirements. Those belong in brainstorming records after the harness exists.

## `update`

Bring harness-maintained files in an existing project up to date from a selected template version.

Expected behavior:

1. Show a dry-run summary before changing files.
2. Preserve project-local state: `ideas/`, `sessions/`, `notes/`, `exports/`, `state/project-init.json`, and finalized `docs/`.
3. Update reusable harness runtime files only after confirmation.
4. Run `./scripts/sync-plugin-skills` when repo-scoped skills change.
5. Run `./scripts/validate-governance`.

## `validate`

Run the same local checks the harness already exposes.

Expected behavior:

1. Run `./scripts/validate-governance`.
2. If `MODE.md` is `development`, also run `./scripts/validate-development`.
3. Report commands and exit codes without hiding local validation output.

## Boundary

The bootstrap helper is convenience tooling. It must not become the source of truth for project state, finalization behavior, validation rules, or agent instructions.
