# File Map

Lean file registry for the Project Idea Lab.

| Path | Purpose |
|---|---|
| `README.md` | Lightweight overview and usage |
| `AGENTS.md` | Agent behavior contract |
| `MODE.md` | Active repository phase selector |
| `.agents/skills/brainstorming-lab/SKILL.md` | Repo-scoped skill for brainstorming-mode lifecycle work |
| `.agents/skills/brainstorming-lab/agents/openai.yaml` | UI metadata for the brainstorming lifecycle skill |
| `.agents/skills/project-finalizer/SKILL.md` | Repo-scoped skill for finalization readiness and mode transition |
| `.agents/skills/project-finalizer/agents/openai.yaml` | UI metadata for the project finalization skill |
| `.agents/skills/development-governance/SKILL.md` | Repo-scoped skill for development-mode governance |
| `.agents/skills/development-governance/agents/openai.yaml` | UI metadata for the development governance skill |
| `.agents/skills/template-maintenance/SKILL.md` | Repo-scoped skill for maintaining this template itself |
| `.agents/skills/template-maintenance/agents/openai.yaml` | UI metadata for the template maintenance skill |
| `.agents/plugins/marketplace.json` | Local plugin marketplace entry for future reusable distribution |
| `plugins/project-lifecycle-lab/.codex-plugin/plugin.json` | Local plugin manifest scaffold for the lifecycle skill package |
| `brainstorming/AGENTS.brainstorming.md` | Brainstorming-mode contract |
| `brainstorming/CONVERSATIONAL_MODE.md` | Plain-language interaction and milestone capture |
| `brainstorming/COMMANDS.md` | Optional backend command mapping |
| `brainstorming/intent_registry.json` | Canonical brainstorming intent registry for generated NL mapping tables |
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
| `tests/workflow_test_helpers.py` | Shared temp-repo fixtures and command helpers for workflow tests |
| `tests/test_development_rendering.py` | Development doc render and validation regression tests |
| `tests/test_intent_registry_contract.py` | Intent-registry render, parity, and CI-contract regression suite |
| `tests/test_lab_lifecycle.py` | Lab command, finalize, status, doctor, and review regression tests |
| `tests/test_template_validation.py` | Template governance, skill, plugin, and launcher validation tests |
| `tests/fixtures/finalized_state_v2.json` | Canonical finalized-state fixture for development render/validate regression |
| `tests/fixtures/finalized_state_web_app_v2.json` | Non-game finalized-state fixture for product-neutral development rendering regression |
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
| `scripts/render-intent-docs` | Cross-platform launcher for generated intent table rendering |
| `scripts/finalize-project` | Cross-platform launcher for Python in-place finalization |
| `scripts/render-development-docs` | Development doc renderer from canonical state |
| `scripts/validate-development` | Development-mode integrity validator |
| `scripts/validate-brainstorming` | Brainstorming-mode integrity validator |
| `scripts/validate-governance.ps1` | PowerShell launcher for Python governance validation |
| `scripts/lab.ps1` | PowerShell launcher for brainstorming lifecycle commands |
| `scripts/lab-sync.ps1` | PowerShell launcher for Python commit+push sync |
| `scripts/lab-note.ps1` | PowerShell launcher for Python research note capture |
| `scripts/render-intent-docs.ps1` | PowerShell launcher for generated intent table rendering |
| `scripts/validate-brainstorming.ps1` | Windows brainstorming validator |
| `scripts/finalize-project.sh` | POSIX launcher for Python in-place finalization |
| `scripts/render-intent-docs.sh` | POSIX launcher for generated intent table rendering |
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
| `scripts/python/template_cli/io_helpers.py` | I/O primitives, regex constants, ValidationResult, and summary printers shared across the CLI |
| `scripts/python/template_cli/validator_code_size.py` | Python file-size validation for template tooling and tests |
| `scripts/python/template_cli/validator_launchers.py` | Launcher consistency checks for shell and PowerShell entrypoints |
| `scripts/python/template_cli/validator_plugins.py` | Local plugin manifest and marketplace validation helpers |
| `scripts/python/template_cli/validator_skills.py` | Repo-scoped skill and skill metadata validation helpers |
| `scripts/python/template_cli/render_helpers.py` | State-extraction, file-manipulation, and hydration helpers for development doc rendering |
| `scripts/python/template_cli/render_templates.py` | Pure template functions for README and PROJECT_CONTEXT document generation |
| `scripts/python/template_cli/finalize_helpers.py` | Utility functions, interactive prompts, markdown extraction, and state helpers for finalization |
| `scripts/python/template_cli/finalize_state.py` | BackupManager, catalog transition functions, and summary export writer for finalization |
| `scripts/python/template_cli/workflow_data.py` | Idea-block I/O, catalog helpers, session helpers, and data primitives for lab workflow commands |
| `scripts/python/template_cli/workflow_commands.py` | Lab lifecycle mutation commands (capture, activate, park, kill, decide, risk, review, export) |
