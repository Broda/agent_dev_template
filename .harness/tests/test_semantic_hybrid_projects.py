from __future__ import annotations

import json

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class SemanticHybridProjectTests(LabWorkflowTestCase):
    def test_structured_cli_plus_web_allows_web_but_rejects_admin_and_editor_claims(self) -> None:
        self._write_hybrid_capabilities(["cli", "web_ui"], ["cli_commands", "browser_ui"])
        self._append_active_task("Build Web UI with an admin UI and editor-facing workflow.")

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("unsupported cli project surface: web ui", result.stdout.lower())
        self.assertIn("unsupported cli project surface: admin ui", result.stdout.lower())
        self.assertIn("unsupported cli project surface: editor-facing", result.stdout.lower())

    def test_structured_cli_plus_admin_allows_admin_and_editor_claims(self) -> None:
        self._write_hybrid_capabilities(["admin_ui", "cli"], ["admin_ui", "cli_commands"])
        self._append_active_task("Build admin UI with an editor-facing workflow.")

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_structured_cli_plus_web_and_admin_allows_all_ui_claims(self) -> None:
        self._write_hybrid_capabilities(
            ["admin_ui", "cli", "web_ui"],
            ["admin_ui", "browser_ui", "cli_commands"],
        )
        self._append_active_task("Build Web UI and admin UI with an editor-facing workflow.")

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_legacy_cli_plus_web_uses_tech_stack_heuristic(self) -> None:
        self._write_legacy_profile("CLI application", "React and Vite")
        self._append_active_task("Build Web UI for CLI job inspection.")

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_legacy_cli_plus_admin_editor_uses_project_and_stack_heuristics(self) -> None:
        self._write_legacy_profile("CLI with an admin editor", "React admin console")
        self._append_active_task("Build admin UI with an editor-facing workflow.")

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def _write_hybrid_capabilities(self, interfaces: list[str], surfaces: list[str]) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["finalizedContract"]["capabilities"]["interfaces"] = interfaces
        state["finalizedContract"]["capabilities"]["surfaces"] = surfaces
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

    def _write_legacy_profile(self, project_type: str, framework: str) -> None:
        self.write_render_fixture()
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projectType"] = project_type
        state["techStack"]["framework"] = framework
        state.pop("finalizedContract", None)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

    def _append_active_task(self, task: str) -> None:
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Deferred Scope\n",
                f"\n- [ ] {task}\n\n# Deferred Scope\n",
                1,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
