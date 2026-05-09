from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentEvidenceTests(LabWorkflowTestCase):
    def test_lab_evidence_records_roadmap_evidence_in_development_mode(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        result = run_cmd(
            [
                "./scripts/lab",
                "evidence",
                "--task",
                "Tests pass",
                "--command",
                "python3 -m unittest discover -s .harness/tests -v",
                "--result",
                "60 tests passed",
                "--note",
                "Validated on CI-shaped fixture",
            ],
            cwd=self.repo,
        )

        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("Recorded evidence for roadmap task: Tests pass", result.stdout)
        self.assertIn("- [x] Tests pass", roadmap)
        self.assertIn(
            "  - Evidence: `python3 -m unittest discover -s .harness/tests -v` -> 60 tests passed",
            roadmap,
        )
        self.assertIn("  - Notes: Validated on CI-shaped fixture", roadmap)

    def test_lab_evidence_can_record_without_completing_task(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        run_cmd(
            [
                "./scripts/lab",
                "evidence",
                "--task",
                "Manual smoke test complete",
                "--command",
                "./scripts/validate-development",
                "--result",
                "not run yet",
                "--no-complete",
            ],
            cwd=self.repo,
        )

        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("- [ ] Manual smoke test complete", roadmap)
        self.assertIn("  - Evidence: `./scripts/validate-development` -> not run yet", roadmap)


if __name__ == "__main__":
    import unittest

    unittest.main()
