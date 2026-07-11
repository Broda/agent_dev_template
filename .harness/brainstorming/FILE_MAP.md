# File Map

Lean file registry for the Project Harness Template.

| Path | Purpose |
|---|---|
| `LICENSE` | MIT license for the public harness template |
| `.editorconfig` | Cross-editor indentation, charset, final-newline, and line-ending policy |
| `.gitattributes` | Git text normalization and binary file classification policy |
| `.gitignore` | Local/derived file exclusions |
| `README.md` | Lightweight overview and usage |
| `pyproject.toml` | Python formatter, linter, and import-order tool configuration |
| `requirements-dev.txt` | Pinned local and CI development check dependencies |
| `.harness/docs/BOOTSTRAP_TOOL.md` | Planning and implementation contract for the harness bootstrap/update helper |
| `.harness/docs/HARNESS_RELEASE_CHECKLIST.md` | Public harness template release checklist |
| `.harness/docs/HARNESS_CHANGELOG.md` | Public harness template release notes |
| `.harness/docs/HARNESS_IMPROVEMENT_ROADMAP.md` | Public-template improvement roadmap and milestone backlog |
| `docs/EXTERNAL_INTEGRATION.md` | Public-safe automation contract for importing external ideas |
| `AGENTS.md` | Agent behavior contract |
| `MODE.md` | Active repository phase selector |
| `.agents/skills/brainstorming-lab/SKILL.md` | Repo-scoped skill for brainstorming-mode lifecycle work |
| `.agents/skills/brainstorming-lab/agents/openai.yaml` | UI metadata for the brainstorming lifecycle skill |
| `.agents/skills/project-finalizer/SKILL.md` | Repo-scoped skill for finalization readiness and mode transition |
| `.agents/skills/project-finalizer/agents/openai.yaml` | UI metadata for the project finalization skill |
| `.agents/skills/development-governance/SKILL.md` | Repo-scoped skill for development-mode governance |
| `.agents/skills/development-governance/agents/openai.yaml` | UI metadata for the development governance skill |
| `.agents/skills/template-maintenance/SKILL.md` | Repo-scoped skill for maintaining this harness template |
| `.agents/skills/template-maintenance/agents/openai.yaml` | UI metadata for the template maintenance skill |
| `.agents/plugins/marketplace.json` | Local plugin marketplace entry for agent-behavior distribution |
| `.harness/plugins/project-lifecycle-lab/README.md` | Plugin packaging decision and external use check |
| `.harness/plugins/project-lifecycle-lab/smoke_package.py` | Standalone plugin package smoke check |
| `.harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json` | Local plugin manifest for the lifecycle agent-behavior package |
| `.harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md` | Plugin mirror of the brainstorming lifecycle skill |
| `.harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/agents/openai.yaml` | Plugin mirror of brainstorming skill UI metadata |
| `.harness/plugins/project-lifecycle-lab/skills/project-finalizer/SKILL.md` | Plugin mirror of the project finalization skill |
| `.harness/plugins/project-lifecycle-lab/skills/project-finalizer/agents/openai.yaml` | Plugin mirror of finalizer skill UI metadata |
| `.harness/plugins/project-lifecycle-lab/skills/development-governance/SKILL.md` | Plugin mirror of the development governance skill |
| `.harness/plugins/project-lifecycle-lab/skills/development-governance/agents/openai.yaml` | Plugin mirror of development skill UI metadata |
| `.harness/plugins/project-lifecycle-lab/skills/template-maintenance/SKILL.md` | Plugin mirror of the harness template maintenance skill |
| `.harness/plugins/project-lifecycle-lab/skills/template-maintenance/agents/openai.yaml` | Plugin mirror of maintenance skill UI metadata |
| `.harness/commands/CONVERSATIONAL_MODE.md` | Agent-facing plain-language intent map across harness modes |
| `.harness/commands/COMMANDS.md` | Backend command contract for human-agent workflow intents |
| `.harness/commands/finalization_overwrite_policy.json` | Finalization and rendered artifact overwrite/ownership policy |
| `.harness/commands/harness_manifest.json` | Harness provenance, compatibility, wrapper, and artifact ownership manifest |
| `.harness/commands/harness_manifest.schema.json` | JSON Schema contract for the harness manifest |
| `.harness/commands/intent_registry.json` | Canonical harness command intent registry for generated NL mapping tables |
| `.harness/commands/intent_registry.schema.json` | JSON Schema contract for the intent registry |
| `.harness/brainstorming/AGENTS.brainstorming.md` | Brainstorming-mode contract |
| `.harness/brainstorming/QUICKSTART.md` | Fast start workflow |
| `.harness/brainstorming/EXAMPLE_LIFECYCLE.md` | End-to-end example from capture through finalize |
| `.harness/brainstorming/FILE_MAP.md` | Registry of retained files |
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
| `.harness/tests/workflow_test_helpers.py` | Shared temp-repo fixtures and command helpers for workflow tests |
| `.harness/tests/test_development_domain_terms.py` | Development validation regression tests for non-template domain language |
| `.harness/tests/test_development_adr.py` | Development ADR command regression tests |
| `.harness/tests/test_development_evidence.py` | Development roadmap evidence command regression tests |
| `.harness/tests/test_development_rendering.py` | Development doc render and validation regression tests |
| `.harness/tests/test_development_wiki.py` | Development wiki render and sync-check regression tests |
| `.harness/tests/test_semantic_finalization_fidelity.py` | Semantic finalization fidelity regression tests for structured contracts and unsupported generated surfaces |
| `.harness/tests/test_finalization_regression.py` | End-to-end finalization regression tests for multi-session detail carryover |
| `.harness/tests/test_harness_manifest.py` | Harness manifest validation and provenance stamping regression tests |
| `.harness/tests/test_lab_handoff.py` | Lab handoff compiler regression tests for lossless brainstorming-to-finalization state |
| `.harness/tests/test_lab_finalization.py` | Lab finalization command regression tests |
| `.harness/tests/test_intent_registry_contract.py` | Intent-registry render, parity, and CI-contract regression suite |
| `.harness/tests/test_intent_registry_parser_parity.py` | Registry-versus-CLI-parser argument parity regression tests |
| `.harness/tests/test_lab_launcher.py` | Lab shell and PowerShell launcher help regression tests |
| `.harness/tests/test_external_idea_import.py` | External idea import and project bootstrap API regression tests |
| `.harness/tests/test_lab_lifecycle.py` | Lab command, finalize, status, doctor, and review regression tests |
| `.harness/tests/test_template_validation.py` | Template governance, skill, plugin, and launcher validation tests |
| `.harness/tests/test_public_safety.py` | Public documentation safety regression tests |
| `.harness/tests/test_project_harness_bootstrap.py` | Project harness bootstrap command regression tests |
| `.harness/tests/test_project_harness_update.py` | Project harness update dry-run regression tests |
| `.harness/tests/test_runtime_discovery.py` | Installed runtime discovery contract tests |
| `.harness/tests/test_state_schema.py` | Project state schema contract regression tests |
| `.harness/tests/test_sync_and_state_robustness.py` | Lab sync failure-path, BackupManager rollback, and malformed catalog row tests |
| `.harness/tests/fixtures/finalized_state_v2.json` | Canonical finalized-state fixture for development render/validate regression |
| `.harness/tests/fixtures/finalized_state_web_app_v2.json` | Non-game finalized-state fixture for product-neutral development rendering regression |
| `.harness/tests/fixtures/finalized_state_with_persistence_v2.json` | Persistence-enabled finalized-state fixture for migration-policy render regression |
| `.harness/tests/fixtures/finalized_state_cli_data_pipeline_v2.json` | CLI/data-pipeline finalized-state fixture for semantic finalization fidelity regressions |
| `.harness/tests/fixtures/finalized_session.md` | Matching finalized session fixture for development render/validate regression |
| `.harness/brainstorming/templates/idea_template.md` | Idea capture template |
| `.harness/brainstorming/templates/decision_template.md` | Decision template |
| `.harness/brainstorming/templates/note_template.md` | Research note template |
| `.harness/brainstorming/templates/project_plan_packet_template.md` | Final export template |
| `.harness/brainstorming/templates/risk_template.md` | Optional risk template |
| `.harness/brainstorming/templates/review_gate_template.md` | Optional review gate template |
| `.harness/brainstorming/docs/adr/template.md` | Optional ADR template |
| `.harness/brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md` | Foundational ADR |
| `.harness/brainstorming/docs/adr/ADR-0002-plan-installed-runtime-boundary.md` | Runtime extraction boundary ADR |
| `.harness/brainstorming/docs/adr/ADR-0003-keep-plugin-skill-mirrors-copied.md` | Plugin mirror ownership ADR |
| `.harness/brainstorming/docs/adr/ADR-0004-defer-official-binary-and-package-manager-install-paths.md` | Runtime install path deferral ADR |
| `.harness/docs/adr/ADR-0002-plan-installed-runtime-boundary.md` | Harness docs copy of runtime extraction boundary ADR |
| `.harness/docs/adr/ADR-0003-keep-plugin-skill-mirrors-copied.md` | Harness docs copy of plugin mirror ownership ADR |
| `.harness/docs/adr/ADR-0004-defer-official-binary-and-package-manager-install-paths.md` | Harness docs copy of runtime install path deferral ADR |
| `scripts/validate-governance` | Cross-platform launcher for Python governance validation |
| `scripts/harness-release-check` | Cross-platform launcher for local public-template release checks |
| `scripts/lab` | Cross-platform launcher for brainstorming lifecycle commands |
| `scripts/lab-sync` | Cross-platform launcher for Python commit+push sync |
| `scripts/lab-note` | Cross-platform launcher for Python research note capture |
| `scripts/project-harness` | Cross-platform launcher for harness bootstrap helpers |
| `scripts/render-intent-docs` | Cross-platform launcher for generated intent table rendering |
| `scripts/sync-plugin-skills` | Cross-platform launcher for syncing canonical repo skills into the plugin package |
| `scripts/finalize-project` | Cross-platform launcher for Python in-place finalization |
| `scripts/render-development-docs` | Development doc renderer from canonical state |
| `scripts/validate-development` | Development-mode integrity validator |
| `scripts/validate-brainstorming` | Brainstorming-mode integrity validator |
| `scripts/validate-governance.ps1` | PowerShell launcher for Python governance validation |
| `scripts/harness-release-check.ps1` | PowerShell launcher for local public-template release checks |
| `scripts/lab.ps1` | PowerShell launcher for brainstorming lifecycle commands |
| `scripts/lab-sync.ps1` | PowerShell launcher for Python commit+push sync |
| `scripts/lab-note.ps1` | PowerShell launcher for Python research note capture |
| `scripts/project-harness.ps1` | PowerShell launcher for harness bootstrap helpers |
| `scripts/render-intent-docs.ps1` | PowerShell launcher for generated intent table rendering |
| `scripts/sync-plugin-skills.ps1` | PowerShell launcher for plugin skill mirror syncing |
| `scripts/validate-brainstorming.ps1` | Windows brainstorming validator |
| `scripts/finalize-project.sh` | POSIX launcher for Python in-place finalization |
| `scripts/harness-release-check.sh` | POSIX launcher for local public-template release checks |
| `scripts/render-intent-docs.sh` | POSIX launcher for generated intent table rendering |
| `scripts/sync-plugin-skills.sh` | POSIX launcher for plugin skill mirror syncing |
| `scripts/render-development-docs.sh` | Native macOS/Linux development doc renderer |
| `scripts/validate-development.sh` | Native macOS/Linux development validator |
| `scripts/validate-brainstorming.sh` | Native macOS/Linux brainstorming validator |
| `scripts/validate-governance.sh` | POSIX launcher for Python governance validation |
| `scripts/lab.sh` | POSIX launcher for brainstorming lifecycle commands |
| `scripts/lab-sync.sh` | POSIX launcher for Python commit+push sync |
| `scripts/lab-note.sh` | POSIX launcher for Python research note capture helper |
| `scripts/project-harness.sh` | POSIX launcher for harness bootstrap helpers |
| `state/project-init.json` | Canonical structured handoff state |
| `state/project-init.schema.v2.json` | JSON Schema and variant contract for canonical state schemaVersion 2 |
| `.github/workflows/ci.yml` | Blocking CI for tests and governance validation |
| `.github/workflows/governance-audit.yml` | Warn-only CI audit |
| `.github/workflows/release-readiness.yml` | Manual public-template release readiness smoke workflow |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Bug report issue template |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Feature request issue template |
| `.harness/runtime/python/template_cli/io_helpers.py` | I/O primitives, regex constants, ValidationResult, and summary printers shared across the CLI |
| `.harness/runtime/python/template_cli/adr.py` | Development ADR capture command implementation |
| `.harness/runtime/python/template_cli/bootstrap/projects.py` | Project harness bootstrap command implementation |
| `.harness/runtime/python/template_cli/bootstrap/update.py` | Project harness update dry-run and apply orchestration |
| `.harness/runtime/python/template_cli/bootstrap/update_apply.py` | Project harness update apply execution, backup, rollback, hook, and validation helpers |
| `.harness/runtime/python/template_cli/bootstrap/update_output.py` | Project harness update dry-run output rendering helpers |
| `.harness/runtime/python/template_cli/bootstrap/update_plan.py` | Project harness update plan classification and baseline comparison helpers |
| `.harness/runtime/python/template_cli/bootstrap/update_source.py` | Project harness update source resolution helpers |
| `.harness/runtime/python/template_cli/external_idea.py` | External idea payload validation and JSON result contracts |
| `.harness/runtime/python/template_cli/git_helpers.py` | Shared captured-output git command runner |
| `.harness/runtime/python/template_cli/evidence.py` | Development roadmap evidence capture command implementation |
| `.harness/runtime/python/template_cli/finalize/artifacts.py` | Finalization artifact directory setup, backup registration, existing-state load, and session-log writing helpers |
| `.harness/runtime/python/template_cli/finalize/context.py` | Finalization target, owner, session, and hydration context resolution |
| `.harness/runtime/python/template_cli/finalize/existing.py` | Existing finalized-state value collection helpers |
| `.harness/runtime/python/template_cli/finalize/execution.py` | Transactional finalization state writing, rendering, and validation execution |
| `.harness/runtime/python/template_cli/finalize/history.py` | Brainstorming history archival into `.harness/history/` during finalization |
| `.harness/runtime/python/template_cli/finalize/output.py` | Finalization user-facing success output helpers |
| `.harness/runtime/python/template_cli/finalize/project.py` | In-place finalization orchestration |
| `.harness/runtime/python/template_cli/finalize/project_settings.py` | Finalization project setting prompt and noninteractive choice collection |
| `.harness/runtime/python/template_cli/finalize/state_builder.py` | Finalized canonical state assembly helpers |
| `.harness/runtime/python/template_cli/finalize/validation.py` | Finalization required-value and noninteractive missing-field validation helpers |
| `.harness/runtime/python/template_cli/finalize/value_collection.py` | Finalization hydrated value collection from existing state and source files |
| `.harness/runtime/python/template_cli/handoff.py` | Brainstorming handoff compiler orchestration for draft canonical finalization state |
| `.harness/runtime/python/template_cli/handoff_contract.py` | Handoff default-state, label, required-field, and implementation-contract constants |
| `.harness/runtime/python/template_cli/handoff_implementation.py` | Handoff implementation-contract extraction and state fill helpers |
| `.harness/runtime/python/template_cli/handoff_labels.py` | Handoff source-file ordering and label extraction helpers |
| `.harness/runtime/python/template_cli/handoff_state.py` | Handoff state-default merge and nested field fill helpers |
| `.harness/runtime/python/template_cli/handoff_summary.py` | Handoff summary output and session-log rendering helpers |
| `.harness/runtime/python/template_cli/validator_artifacts.py` | Retained artifact lists for brainstorming and development validation |
| `.harness/runtime/python/template_cli/validator_code_size.py` | Python file-size validation for template tooling and tests |
| `.harness/runtime/python/template_cli/validator_intents.py` | Intent registry, generated command docs, and CI sync validation helpers |
| `.harness/runtime/python/template_cli/validator_launchers.py` | Launcher consistency checks for shell and PowerShell entrypoints |
| `.harness/runtime/python/template_cli/validator_manifest.py` | Harness manifest validation and provenance stamping helpers |
| `.harness/runtime/python/template_cli/validator_module_boundaries.py` | Import-boundary checks for template CLI modules |
| `.harness/runtime/python/template_cli/validator_overwrite_policy.py` | Finalization/render output ownership policy validation helpers |
| `.harness/runtime/python/template_cli/validator_plugins.py` | Local plugin manifest and marketplace validation helpers |
| `.harness/runtime/python/template_cli/validator_python_config.py` | Python tool configuration validation helpers |
| `.harness/runtime/python/template_cli/validator_semantics.py` | Semantic validation for finalized development docs and structured contract fidelity |
| `.harness/runtime/python/template_cli/validator_skills.py` | Repo-scoped skill and skill metadata validation helpers |
| `.harness/runtime/python/template_cli/plugin_sync.py` | Plugin skill mirror sync command implementation |
| `.harness/runtime/python/template_cli/posix_modes.py` | Canonical POSIX launcher mode inventory plus generation, Git-index, and validation helpers |
| `.harness/runtime/python/template_cli/intent_registry.py` | Intent registry loading, schema validation, and command lookup helpers |
| `.harness/runtime/python/template_cli/intents.py` | Intent registry rendering and compatibility exports for generated intent-doc sync helpers |
| `.harness/runtime/python/template_cli/lab_cli.py` | Compatibility exports for lab parser and dispatch wiring |
| `.harness/runtime/python/template_cli/lab_cli_dispatch.py` | Lab subcommand dispatch table for the top-level CLI |
| `.harness/runtime/python/template_cli/lab_cli_parsers.py` | Declarative lab subcommand parser argument table |
| `.harness/runtime/python/template_cli/notes.py` | Durable research note capture command implementation |
| `.harness/runtime/python/template_cli/render.py` | Development document render orchestration |
| `.harness/runtime/python/template_cli/render_capabilities.py` | Capability and structured finalized-contract helpers for development doc rendering |
| `.harness/runtime/python/template_cli/render_ci.py` | Pure renderer for generated development CI workflow |
| `.harness/runtime/python/template_cli/render_contract.py` | Implementation contract extraction and formatting for finalized development docs |
| `.harness/runtime/python/template_cli/render_helpers.py` | State-extraction, file-manipulation, and hydration helpers for development doc rendering |
| `.harness/runtime/python/template_cli/render_policy_docs.py` | Capability-aware policy document cleanup for generated development docs |
| `.harness/runtime/python/template_cli/render_governance_templates.py` | Compatibility exports for governance document renderers |
| `.harness/runtime/python/template_cli/render_adr.py` | Pure renderer for the generated initial architecture ADR |
| `.harness/runtime/python/template_cli/render_architecture.py` | Pure renderer for generated architecture governance docs |
| `.harness/runtime/python/template_cli/render_roadmap.py` | Pure renderer for generated roadmap governance docs |
| `.harness/runtime/python/template_cli/render_templates.py` | Compatibility exports for development document renderers |
| `.harness/runtime/python/template_cli/render_project_context.py` | Pure renderer for generated project context docs |
| `.harness/runtime/python/template_cli/render_readme.py` | Pure renderer for generated README docs |
| `.harness/runtime/python/template_cli/release_check.py` | Local public-template release check orchestration |
| `.harness/runtime/python/template_cli/runtime_discovery.py` | Installed runtime discovery and compatibility resolution helpers |
| `.harness/runtime/python/template_cli/state_schema.py` | Shared schema-backed validator for draft and finalized canonical state |
| `.harness/runtime/python/template_cli/sync.py` | Git sync helpers for milestone commit and push flows |
| `.harness/runtime/python/template_cli/validator_placeholders.py` | Precise unresolved-placeholder detection for generated development docs |
| `.harness/runtime/python/template_cli/validators.py` | Brainstorming and development validation orchestration |
| `.harness/runtime/python/template_cli/wiki.py` | Optional development GitHub Wiki command orchestration |
| `.harness/runtime/python/template_cli/wiki_config.py` | Wiki configuration and checkout-path resolution helpers |
| `.harness/runtime/python/template_cli/wiki_git.py` | Wiki git execution, clone, and relevant-change detection helpers |
| `.harness/runtime/python/template_cli/wiki_pages.py` | Curated GitHub Wiki page rendering helpers |
| `.harness/runtime/python/template_cli/finalize/helpers.py` | Utility functions, interactive prompts, markdown extraction, and state helpers for finalization |
| `.harness/runtime/python/template_cli/finalize/state.py` | BackupManager, catalog transition functions, and summary export writer for finalization |
| `.harness/runtime/python/template_cli/workflow_catalog.py` | IDEA_CATALOG row parsing and upsert helpers for lab workflow state |
| `.harness/runtime/python/template_cli/workflow_data.py` | Idea-block I/O, session helpers, and data primitives for lab workflow commands |
| `.harness/runtime/python/template_cli/workflow_commands.py` | Session-scoped lab mutation commands for path notes, decisions, risks, and reviews |
| `.harness/runtime/python/template_cli/workflow_development_status.py` | Development-mode status reporting helpers |
| `.harness/runtime/python/template_cli/workflow_export.py` | Lab idea summary export command handler |
| `.harness/runtime/python/template_cli/workflow_idea_commands.py` | Idea lifecycle command handlers for capture, activation, parking, and killing |
| `.harness/runtime/python/template_cli/workflow_readiness.py` | Finalization target resolution and readiness signal helpers |
| `.harness/runtime/python/template_cli/workflow_render.py` | Pure markdown renderers for lab workflow artifacts |
| `.harness/runtime/python/template_cli/workflow_sessions.py` | Brainstorming session file creation, sequence IDs, and section appends |
| `.harness/runtime/python/template_cli/workflow_status.py` | Lab status and finalize-doctor reporting helpers |
| `.harness/runtime/python/template_cli/workflow.py` | Lab status, doctor, audit, and finalize command orchestration |
| `.harness/runtime/python/template_cli/json_schema.py` | Dependency-free JSON Schema subset validator for harness-owned contracts |
