# CLAUDE.md

Guidance for Claude Code when working in this project harness template.

## Start Here

1. Read `AGENTS.md`.
2. Read `MODE.md`.
3. Follow the matching mode contract:
   - `brainstorming`: `brainstorming/AGENTS.brainstorming.md`
   - `development`: `development/AGENTS.development.md`

This repo also provides Codex-style skills under `.agents/skills/`. Claude Code may not load them automatically, but they are concise workflow references worth reading when the task matches:

- `.agents/skills/brainstorming-lab/SKILL.md`
- `.agents/skills/project-finalizer/SKILL.md`
- `.agents/skills/development-governance/SKILL.md`
- `.agents/skills/template-maintenance/SKILL.md`

## Stable Commands

Python 3 is required. The shell and PowerShell entrypoints are wrappers; canonical logic lives under `scripts/python/template_cli/`.

```sh
./scripts/lab status
./scripts/lab doctor [--idea-id <id>]
./scripts/lab capture --idea-id <id> --title "Title"
./scripts/lab activate --idea-id <id>
./scripts/lab decide --idea-id <id> --chosen-option "..." --rationale "..."
./scripts/lab risk --idea-id <id> --statement "..."
./scripts/lab review --idea-id <id> --result conditional-pass --summary "..."
./scripts/lab export --idea-id <id>
./scripts/finalize-project --idea-id <id> [--write-export]
./scripts/render-intent-docs
./scripts/sync-plugin-skills
./scripts/validate-governance
python3 -m unittest discover -s tests -v
```

## Brainstorming Notes

- Use `./scripts/lab` for durable milestone writes.
- Milestone writes auto-commit and best-effort push unless `--no-sync` is passed.
- Do not run separate git commands for milestone writes unless explicitly asked or recovering from failure.
- Do not load `notes/` by default; search `NOTES_CATALOG.md` first when prior research is requested.

## Development Notes

- Before meaningful development work, read `docs/GOVERNANCE_INDEX.md`, every listed governance document, recent ADRs, and `CHANGELOG.md`.
- Run the build, run, and test commands recorded in `docs/PROJECT_CONTEXT.md`.
- Record evidence under completed tasks in `docs/ROADMAP.md`.
- Keep code files at or under 500 lines.
- Public contract changes require ADR and version alignment.

## Template Maintenance

For changes to this harness template itself:

- Keep command paths stable.
- Edit `harness_commands/intent_registry.json` before regenerating generated intent docs.
- Run `./scripts/sync-plugin-skills` after changing repo-scoped skills.
- Update `brainstorming/FILE_MAP.md` when retained template inventory changes.
- Run `./scripts/validate-governance` and the regression suite before finishing.
