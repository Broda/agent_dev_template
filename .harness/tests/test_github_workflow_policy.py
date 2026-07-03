from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class GithubWorkflowPolicyTests(LabWorkflowTestCase):
    def test_validate_brainstorming_rejects_push_triggered_workflows(self) -> None:
        workflow_path = self.repo / ".github/workflows/governance-audit.yml"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                "  workflow_dispatch:\n", "  workflow_dispatch:\n  push:\n"
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Brainstorming workflow must not run on push: .github/workflows/governance-audit.yml has a push trigger.",
            result.stdout,
        )

    def test_validate_brainstorming_allows_pull_request_triggered_workflows(self) -> None:
        workflow_path = self.repo / ".github/workflows/governance-audit.yml"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                "  workflow_dispatch:\n", "  workflow_dispatch:\n  pull_request:\n"
            ),
            encoding="utf-8",
        )

        run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo)


if __name__ == "__main__":
    import unittest

    unittest.main()
