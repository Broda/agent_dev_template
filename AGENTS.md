# Agent Dispatcher

This repository is a two-phase project harness template. It starts in **brainstorming mode** and finalizes in place into **development mode**.

## Start Here

1. Read `MODE.md`.
2. Do not mix brainstorming and development rule sets in one task.
3. Use the matching repo skill when your agent supports skills:

| Situation | Skill | Legacy contract |
|---|---|---|
| `MODE.md` says `brainstorming` | `$brainstorming-lab` | `.harness/brainstorming/AGENTS.brainstorming.md` |
| Preparing or running finalization | `$project-finalizer` | `.harness/brainstorming/AGENTS.brainstorming.md` |
| `MODE.md` says `development` | `$development-governance` | `.harness/development/AGENTS.development.md` |
| Maintaining this harness template itself | `$template-maintenance` | this file plus current mode contract |

The legacy contracts remain available for agents that do not support skills.

## Stable Runtime

Python 3 is required. Keep these command paths stable:

```sh
./scripts/lab status
./scripts/lab doctor
./scripts/lab capture --idea-id <id> --title "Title"
./scripts/lab activate --idea-id <id>
./scripts/finalize-project --idea-id <id>
./scripts/validate-governance
```

`./scripts/lab` is the canonical brainstorming CLI. Milestone writes auto-commit and best-effort push unless `--no-sync` is used.
