from __future__ import annotations

import json

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabStatusTests(LabWorkflowTestCase):
    def test_lab_allows_shared_commands_in_development_mode(self) -> None:
        self.write_render_fixture()
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Mode: development", result.stdout)

    def test_lab_mode_enforcement_uses_registry_modes(self) -> None:
        self.write_render_fixture()
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for intent in registry["intents"]:
            if intent["command"] == "status":
                intent["modes"] = ["brainstorming"]
                break
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("/lab status is not available in development mode", result.stdout + result.stderr)

    def test_lab_status_reports_development_context_after_finalize(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertIn("Mode: development", result.stdout)
        self.assertIn("Project: Render Fixture", result.stdout)
        self.assertIn("Canonical state: finalized for idea-render-fixture", result.stdout)
        self.assertIn("Active milestone: Milestone 0", result.stdout)
        self.assertIn("Governance docs:", result.stdout)
        self.assertIn("Roadmap tasks:", result.stdout)
        self.assertIn("Validation command:", result.stdout)
        self.assertNotIn("Finalize readiness:", result.stdout)
        self.assertNotIn("Finalize target:", result.stdout)

    def test_lab_status_reports_ready_target_context(self) -> None:
        self.write_finalize_fixture("idea-status-ready")
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertIn("Mode: brainstorming", result.stdout)
        self.assertIn("Ideas tracked: 1 (inbox 0, active 1, parked 0, killed 0, finalized 0)", result.stdout)
        self.assertIn("Canonical state: draft for idea-status-ready", result.stdout)
        self.assertIn("Finalize target: idea-status-ready (from canonical state)", result.stdout)
        self.assertIn("Target title: Finalize Smoke", result.stdout)
        self.assertIn("Related sessions: 1", result.stdout)
        self.assertIn("Finalize readiness: ready", result.stdout)

    def test_lab_status_reports_ambiguous_multiple_active_ideas(self) -> None:
        self.write_finalize_fixture("idea-status-first")
        state_path = self.repo / "state/project-init.json"
        state_text = state_path.read_text(encoding="utf-8").replace('"ideaId": "idea-status-first"', '"ideaId": ""')
        state_path.write_text(state_text, encoding="utf-8")
        catalog_path = self.repo / "IDEA_CATALOG.md"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8")
            + "| idea-status-second | Second Idea | active | Test User | `sessions/2026-04-03_idea-status-second.md` | _n/a_ | _none_ |\n",
            encoding="utf-8",
        )
        (self.repo / "sessions/2026-04-03_idea-status-second.md").write_text(
            "# Brainstorming Session\n\n- Idea ID: `idea-status-second`\n",
            encoding="utf-8",
        )
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertIn("Active ideas:", result.stdout)
        self.assertIn("- idea-status-first (Finalize Smoke)", result.stdout)
        self.assertIn("- idea-status-second (Second Idea)", result.stdout)
        self.assertIn("Finalize target: ambiguous", result.stdout)
        self.assertIn("Finalize readiness: blocked", result.stdout)
        self.assertIn("Missing before finalize: explicit --idea-id or a single active idea", result.stdout)

    def test_lab_doctor_reports_missing_finalize_fields(self) -> None:
        run_cmd(
            [
                "./scripts/lab",
                "capture",
                "--idea-id",
                "idea-doctor-blocked",
                "--title",
                "Doctor Blocked",
                "--no-sync",
            ],
            cwd=self.repo,
        )
        run_cmd(["./scripts/lab", "activate", "--idea-id", "idea-doctor-blocked", "--no-sync"], cwd=self.repo)
        result = run_cmd(["./scripts/lab", "doctor"], cwd=self.repo)
        self.assertIn("Finalize doctor", result.stdout)
        self.assertIn("Finalize target: idea-doctor-blocked (from single active idea)", result.stdout)
        self.assertIn("Finalize readiness: needs-input", result.stdout)
        self.assertIn("- session history: OK via sessions/", result.stdout)
        self.assertIn("- problem statement: MISSING", result.stdout)
        self.assertIn("- MVP scope: MISSING", result.stdout)
        self.assertIn("- build command: MISSING", result.stdout)
        self.assertIn("Blocked on:", result.stdout)
        self.assertIn("./scripts/lab handoff --idea-id idea-doctor-blocked --check", result.stdout)
        self.assertIn("update the active idea/session or state/project-init.json", result.stdout)

    def test_lab_doctor_reports_sources_for_ready_target(self) -> None:
        self.write_finalize_fixture("idea-doctor-ready")
        result = run_cmd(["./scripts/lab", "doctor"], cwd=self.repo)
        self.assertIn("Finalize target: idea-doctor-ready (from canonical state)", result.stdout)
        self.assertIn("Finalize readiness: ready", result.stdout)
        self.assertIn("- problem statement: OK via state.product.problemStatement", result.stdout)
        self.assertIn("- build command: OK via state.commands.build", result.stdout)
        self.assertIn("- top risks: OK via state.governance.topRisks", result.stdout)
        self.assertIn("Next step: finalize can run now with ./scripts/finalize-project --idea-id idea-doctor-ready", result.stdout)
