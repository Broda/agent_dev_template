# File Map

Lean file registry for the Project Idea Lab.

| Path | Purpose |
|---|---|
| `README.md` | Lightweight overview and usage |
| `AGENTS.md` | Agent behavior contract |
| `MODE.md` | Active repository phase selector |
| `brainstorming/AGENTS.brainstorming.md` | Brainstorming-mode contract |
| `brainstorming/CONVERSATIONAL_MODE.md` | Plain-language interaction and milestone capture |
| `brainstorming/COMMANDS.md` | Optional backend command mapping |
| `brainstorming/QUICKSTART.md` | Fast start workflow |
| `brainstorming/EXAMPLE_LIFECYCLE.md` | End-to-end example from capture through finalize |
| `brainstorming/FILE_MAP.md` | Registry of retained files |
| `IDEA_CATALOG.md` | Central idea index |
| `NOTES_CATALOG.md` | Central research note index |
| `ideas/_inbox.md` | Captured ideas |
| `ideas/_active.md` | Active ideas |
| `ideas/_parked.md` | Parked ideas |
| `ideas/_killed.md` | Killed ideas |
| `sessions/` | Session records and finalization continuity logs |
| `notes/` | Saved research/context notes |
| `exports/` | Optional archival project summaries |
| `tests/` | Regression tests for CLI and workflow runtime |
| `tests/fixtures/finalized_state_v2.json` | Canonical finalized-state fixture for development render/validate regression |
| `tests/fixtures/finalized_state_with_persistence_v2.json` | Persistence-enabled finalized-state fixture for migration-policy render regression |
| `tests/fixtures/finalized_session.md` | Matching finalized session fixture for development render/validate regression |
| `brainstorming/templates/idea_template.md` | Idea capture template |
| `brainstorming/templates/decision_template.md` | Decision template |
| `brainstorming/templates/note_template.md` | Research note template |
| `brainstorming/templates/project_plan_packet_template.md` | Final export template |
| `brainstorming/templates/risk_template.md` | Optional risk template |
| `brainstorming/templates/review_gate_template.md` | Optional review gate template |
| `brainstorming/docs/adr/template.md` | Optional ADR template |
| `brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md` | Foundational ADR |
| `scripts/validate-governance` | Cross-platform launcher for Python governance validation |
| `scripts/lab` | Cross-platform launcher for brainstorming lifecycle commands |
| `scripts/lab-sync` | Cross-platform launcher for Python commit+push sync |
| `scripts/lab-note` | Cross-platform launcher for Python research note capture |
| `scripts/finalize-project` | Cross-platform launcher for Python in-place finalization |
| `scripts/render-development-docs` | Development doc renderer from canonical state |
| `scripts/validate-development` | Development-mode integrity validator |
| `scripts/validate-brainstorming` | Brainstorming-mode integrity validator |
| `scripts/validate-governance.ps1` | PowerShell launcher for Python governance validation |
| `scripts/lab.ps1` | PowerShell launcher for brainstorming lifecycle commands |
| `scripts/lab-sync.ps1` | PowerShell launcher for Python commit+push sync |
| `scripts/lab-note.ps1` | PowerShell launcher for Python research note capture |
| `scripts/validate-brainstorming.ps1` | Windows brainstorming validator |
| `scripts/finalize-project.sh` | POSIX launcher for Python in-place finalization |
| `scripts/render-development-docs.sh` | Native macOS/Linux development doc renderer |
| `scripts/validate-development.sh` | Native macOS/Linux development validator |
| `scripts/validate-brainstorming.sh` | Native macOS/Linux brainstorming validator |
| `scripts/validate-governance.sh` | POSIX launcher for Python governance validation |
| `scripts/lab.sh` | POSIX launcher for brainstorming lifecycle commands |
| `scripts/lab-sync.sh` | POSIX launcher for Python commit+push sync |
| `scripts/lab-note.sh` | POSIX launcher for Python research note capture helper |
| `state/project-init.json` | Canonical structured handoff state |
| `.github/workflows/ci.yml` | Blocking CI for tests and governance validation |
| `.github/workflows/governance-audit.yml` | Warn-only CI audit |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist |
| `.gitignore` | Local/derived file exclusions |
