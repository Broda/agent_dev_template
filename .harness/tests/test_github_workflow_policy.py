from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class GithubWorkflowPolicyTests(LabWorkflowTestCase):
    def test_validate_brainstorming_keeps_github_workflows_manual_only(self) -> None:
        workflow_path = self.repo / ".github/workflows/governance-audit.yml"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                "  workflow_dispatch:\n", "  workflow_dispatch:\n  pull_request:\n"
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Brainstorming workflow must stay manual-only: .github/workflows/governance-audit.yml "
            "has pull_request/push trigger.",
            result.stdout,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
