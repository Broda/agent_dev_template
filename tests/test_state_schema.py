from __future__ import annotations

import json
import sys

from tests.workflow_test_helpers import REPO_ROOT, LabWorkflowTestCase, run_cmd

SCRIPT_ROOT = REPO_ROOT / "scripts/python"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from template_cli.io_helpers import ValidationResult  # noqa: E402
from template_cli.state_schema import validate_project_state_file  # noqa: E402


class StateSchemaTests(LabWorkflowTestCase):
    def test_valid_draft_state_passes_schema_contract(self) -> None:
        result = ValidationResult()

        validate_project_state_file(self.repo, result, variant="draft")

        self.assertEqual([], result.failures)

    def test_valid_finalized_state_passes_schema_contract(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        result = ValidationResult()

        validate_project_state_file(
            self.repo,
            result,
            variant="finalized",
            check_artifact_references=True,
        )

        self.assertEqual([], result.failures)

    def test_current_schema_fixture_validates_without_mutating_state_file(self) -> None:
        self.write_render_fixture()
        state_before = (self.repo / "state/project-init.json").read_text(encoding="utf-8")
        result = ValidationResult()

        state = validate_project_state_file(self.repo, result, variant="finalized")

        self.assertEqual([], result.failures)
        self.assertEqual(2, state["schemaVersion"])
        self.assertEqual(state_before, (self.repo / "state/project-init.json").read_text(encoding="utf-8"))

    def test_finalized_state_reports_missing_required_field(self) -> None:
        self.write_render_fixture()
        state = self._read_state()
        del state["product"]["problemStatement"]
        self._write_state(state)
        result = ValidationResult()

        validate_project_state_file(self.repo, result, variant="finalized")

        self.assertIn("state/project-init.json must include product.problemStatement.", result.failures)

    def test_finalized_state_reports_wrong_type(self) -> None:
        self.write_render_fixture()
        state = self._read_state()
        state["artifacts"]["sessionFiles"] = "sessions/2026-04-03_idea-render-fixture.md"
        self._write_state(state)
        result = ValidationResult()

        validate_project_state_file(self.repo, result, variant="finalized")

        self.assertIn("state/project-init.json artifacts.sessionFiles must be an array.", result.failures)

    def test_state_reports_unsupported_schema_version(self) -> None:
        state = self._read_state()
        state["schemaVersion"] = 99
        self._write_state(state)
        result = ValidationResult()

        validate_project_state_file(self.repo, result, variant="draft")

        self.assertIn("state/project-init.json schemaVersion must be 2.", result.failures)

    def test_future_finalized_schema_version_fails_before_migration_exists(self) -> None:
        self.write_render_fixture()
        state = self._read_state()
        state["schemaVersion"] = 3
        self._write_state(state)
        result = ValidationResult()

        validate_project_state_file(self.repo, result, variant="finalized")

        self.assertIn("state/project-init.json schemaVersion must be 2.", result.failures)

    def test_finalized_state_reports_missing_artifact_reference(self) -> None:
        self.write_render_fixture()
        state = self._read_state()
        state["artifacts"]["adrReferences"] = ["docs/adr/ADR-9999-missing.md"]
        self._write_state(state)
        result = ValidationResult()

        validate_project_state_file(
            self.repo,
            result,
            variant="finalized",
            check_artifact_references=True,
        )

        self.assertIn(
            "state/project-init.json references a missing ADR file: docs/adr/ADR-9999-missing.md",
            result.failures,
        )

    def _read_state(self) -> dict:
        return json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))

    def _write_state(self, state: dict) -> None:
        (self.repo / "state/project-init.json").write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
