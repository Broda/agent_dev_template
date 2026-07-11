from __future__ import annotations

import json
import sys

from workflow_test_helpers import REPO_ROOT, LabWorkflowTestCase, run_cmd

SCRIPT_ROOT = REPO_ROOT / ".harness/runtime/python"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from template_cli.render_helpers import _infer_domain_concepts  # noqa: E402


class SemanticFinalizationFidelityTests(LabWorkflowTestCase):
    def test_cli_data_pipeline_fixture_renders_structured_contract_without_web_residue(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        docs = self._rendered_docs()
        combined = "\n".join(docs.values())
        roadmap = docs["docs/ROADMAP.md"]
        context = docs["docs/PROJECT_CONTEXT.md"]
        architecture = docs["docs/ARCHITECTURE.md"]

        for expected in [
            "AutomateThought.com newsletter packet",
            "Report runs are append-only.",
            "Markdown is written unconditionally for every run.",
            "Packet valid, invalid, and missing states are recorded but do not gate run creation.",
            "Child rows are inserted only for valid packet items.",
            "Corrections supersede previous facts without destructive rewrites.",
            "Canonical allowlisted JSON v1 is the only accepted packet input format.",
            "Derived Markdown is deterministic for identical stored inputs.",
            "Hermes owns source packet production outside this repository.",
            "XDG data directory contains the SQLite database.",
            "CLI command: report-pipeline run --packet <path>",
            "Packet JSON schema v1",
            "Remote APIs",
            "Browser UI",
        ]:
            self.assertIn(expected, combined)

        milestone_positions = [roadmap.index(f"## M{idx} -") for idx in range(6)]
        self.assertEqual(sorted(milestone_positions), milestone_positions)
        self.assertIn("Active Milestone: M0 - Repository And CLI Baseline", context)
        self.assertIn("CLI Boundary\n-> Application\n-> Domain/Core", architecture)
        self.assertIn("- CLI commands", architecture)
        self.assertNotIn("- HTTP routes and transport schemas", architecture)

        banned_terms = [
            "Web UI",
            "admin UI",
            "API endpoints",
            "DTO structures",
            "configure auth",
            "configure authentication",
            "npm",
            "unhandled promise",
            "Com,",
        ]
        for banned in banned_terms:
            self.assertNotIn(banned, combined)
        self.assertNotIn("TypeScript", combined)

    def test_semantic_validation_rejects_unsupported_cli_surface_residue(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Deferred Scope\n",
                "\n- [ ] Build Web UI admin flow with API endpoints and DTO structures.\n\n# Deferred Scope\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported cli project surface: web ui", result.stdout.lower())
        self.assertIn("unsupported non-API project surface: api endpoints", result.stdout)
        self.assertIn("unsupported non-API project surface: dto structures", result.stdout)

    def test_semantic_validation_allows_banned_phrases_in_deferred_scope(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8")
            + "\n# Deferred Scope\n\n- Web UI, API endpoints, DTO structures, TypeScript, and npm remain deferred.\n",
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_semantic_validation_allows_deferred_scope_checkbox_under_deferred_section(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        self._append_deferred_scope("Web UI")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Verification Baseline\n",
                "\n- [ ] Web UI\n\n# Verification Baseline\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_semantic_validation_rejects_deferred_scope_checkbox_in_active_milestone(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        self._append_deferred_scope("Web UI")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Deferred Scope\n",
                "\n- [ ] Web UI\n\n# Deferred Scope\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Deferred scope appears as an active roadmap task: Web UI", result.stdout)

    def test_structured_cli_api_capabilities_allow_active_api_tasks(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["finalizedContract"]["capabilities"]["interfaces"] = ["api", "cli"]
        state["finalizedContract"]["capabilities"]["surfaces"] = [
            "cli_commands",
            "data_pipeline",
            "http_api",
            "sqlite",
        ]
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Deferred Scope\n",
                "\n- [ ] Build API endpoints for CLI automation.\n\n# Deferred Scope\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_legacy_capability_fallback_uses_word_boundaries(self) -> None:
        self.write_render_fixture()
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projectType"] = "Apiary CLI"
        state.pop("finalizedContract", None)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap_text = roadmap.read_text(encoding="utf-8")
        if "\n# Deferred Scope\n" in roadmap_text:
            roadmap_text = roadmap_text.replace(
                "\n# Deferred Scope\n",
                "\n- [ ] Build API endpoints from apiary records.\n\n# Deferred Scope\n",
                1,
            )
        else:
            roadmap_text += "\n- [ ] Build API endpoints from apiary records.\n"
        roadmap.write_text(
            roadmap_text,
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported non-API project surface: api endpoints", result.stdout)

    def test_semantic_validation_rejects_missing_invariant_and_active_deferred_scope(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Deferred Scope\n",
                "\n- [ ] Collectors\n\n# Deferred Scope\n",
                1,
            ),
            encoding="utf-8",
        )
        for relative_path in [
            "README.md",
            "docs/PROJECT_CONTEXT.md",
            "docs/ROADMAP.md",
            "docs/ARCHITECTURE.md",
            "docs/adr/ADR-0001-record-architecture-decisions.md",
        ]:
            path = self.repo / relative_path
            path.write_text(
                path.read_text(encoding="utf-8").replace("Report runs are append-only.", ""),
                encoding="utf-8",
            )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Deferred scope appears as an active roadmap task: Collectors", result.stdout)
        self.assertIn("missing captured invariant: Report runs are append-only.", result.stdout)

    def test_legacy_domain_concept_inference_preserves_dotted_names(self) -> None:
        concepts = _infer_domain_concepts(
            "AutomateThought.com newsletters need deterministic reports. Corrections supersede prior facts."
        )

        self.assertIn("AutomateThought.com newsletters need deterministic reports", concepts)
        self.assertNotIn("Com newsletters need deterministic reports", concepts)

    def test_structured_contract_state_validates_as_schema_v2_extension(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)
        state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        self.assertEqual(2, state["schemaVersion"])
        self.assertEqual(1, state["finalizedContract"]["schemaVersion"])

    def _append_deferred_scope(self, item: str) -> None:
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["finalizedContract"]["deferredScope"].append(item)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def test_normal_finalize_hydrates_structured_contract_from_session_json(self) -> None:
        idea_id = "idea-finalize-contract-json"
        self.write_finalize_fixture(idea_id)
        session_path = self.repo / f"sessions/2026-04-03_{idea_id}.md"
        session_path.write_text(
            session_path.read_text(encoding="utf-8")
            + """

## Finalized Contract

```json
{
  "capabilities": {
    "interfaces": ["CLI"],
    "surfaces": ["data pipeline", "SQLite"],
    "authentication": "None"
  },
  "ownershipBoundaries": [
    "Operator owns packet selection before command execution.",
    "Core owns validation and append-only run storage."
  ],
  "invariants": [
    "Report runs are append-only.",
    "Invalid packets still create audit records."
  ],
  "domainConcepts": ["packet run", "audit record"],
  "domainModel": [
    {"name": "ReportRun", "description": "Append-only command execution record."}
  ],
  "dataModel": [
    {"name": "SQLite report_runs table"}
  ],
  "publicContracts": [
    {"name": "CLI command: packet-report run --packet <path>", "surface": "cli_commands"}
  ],
  "versionDomains": [
    {"domain": "Packet JSON schema", "version": "v1"}
  ],
  "milestones": [
    {
      "id": "M0",
      "name": "CLI Baseline",
      "goal": "Create the packet-report command shell.",
      "tasks": [{"area": "CLI", "text": "Implement packet-report help and argument parsing."}],
      "gates": [{"name": "CLI help runs locally.", "evidence": "./packet-report --help"}]
    }
  ],
  "deferredScope": ["Web UI", "Remote APIs"]
}
```
""",
            encoding="utf-8",
        )

        run_cmd(["./scripts/finalize-project", "--idea-id", idea_id], cwd=self.repo)

        state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        contract = state["finalizedContract"]
        self.assertEqual(1, contract["schemaVersion"])
        self.assertEqual(["cli"], contract["capabilities"]["interfaces"])
        self.assertEqual("none", contract["capabilities"]["authentication"])
        self.assertIn("data_pipeline", contract["capabilities"]["surfaces"])
        self.assertEqual("M0", contract["milestones"][0]["id"])

        docs = self._rendered_docs()
        combined = "\n".join(docs.values())
        self.assertIn("Report runs are append-only.", combined)
        self.assertIn("Core owns validation and append-only run storage.", combined)
        self.assertIn("CLI command: packet-report run --packet <path>", combined)
        self.assertIn("M0 - CLI Baseline", docs["docs/ROADMAP.md"])
        self.assertIn("Active Milestone: M0 - CLI Baseline", docs["docs/PROJECT_CONTEXT.md"])

    def _rendered_docs(self) -> dict[str, str]:
        paths = [
            "README.md",
            "CHANGELOG.md",
            "docs/PROJECT_CONTEXT.md",
            "docs/ROADMAP.md",
            "docs/ARCHITECTURE.md",
            "docs/VERSIONING_AND_RELEASE_POLICY.md",
            "docs/SECURITY_POLICY.md",
            "docs/RUNTIME_VERIFICATION_REPORT.md",
            "docs/MIGRATION_POLICY.md",
            "docs/adr/ADR-0001-record-architecture-decisions.md",
        ]
        return {path: (self.repo / path).read_text(encoding="utf-8") for path in paths if (self.repo / path).exists()}


if __name__ == "__main__":
    import unittest

    unittest.main()
