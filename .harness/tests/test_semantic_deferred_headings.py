from __future__ import annotations

import json
import unittest

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class SemanticDeferredHeadingTests(LabWorkflowTestCase):
    def test_semantic_validation_allows_deferred_scope_checkbox_under_nested_deferred_heading(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        self._append_deferred_scope("Web UI")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8").replace(
                "\n# Deferred Scope\n\n",
                "\n# Deferred Scope\n\n## Web UI\n\n- [ ] Build Web UI\n\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self.assertEqual(0, result.returncode)

    def test_semantic_validation_rejects_deferred_scope_checkbox_after_deferred_section(self) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        self._append_deferred_scope("Web UI")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap = self.repo / "docs/ROADMAP.md"
        roadmap.write_text(
            roadmap.read_text(encoding="utf-8") + "\n# Follow Up\n\n- [ ] Build Web UI\n",
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Deferred scope appears as an active roadmap task: Web UI", result.stdout)

    def _append_deferred_scope(self, item: str) -> None:
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["finalizedContract"]["deferredScope"].append(item)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
