from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class GithubWorkflowPolicyTests(LabWorkflowTestCase):
    def test_validate_brainstorming_checks_pr_only_ci_cancellation(self) -> None:
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace(
                "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
                "cancel-in-progress: true",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Workflow .github/workflows/ci.yml is missing CI-efficiency contract: PR-only cancellation",
            result.stdout,
        )

    def test_validate_brainstorming_checks_ci_timeout_and_retention(self) -> None:
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8")
            .replace("timeout-minutes: 30", "timeout-minutes: 3", 1)
            .replace("retention-days: 3", "retention-days: 4", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: measured Ubuntu timeout", result.stdout)
        self.assertIn("missing CI-efficiency contract: three-day diagnostic retention", result.stdout)

    def test_validate_brainstorming_keeps_manual_release_runs_independent(self) -> None:
        workflow_path = self.repo / ".github/workflows/release-readiness.yml"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
                "cancel-in-progress: true",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Workflow .github/workflows/release-readiness.yml is missing CI-efficiency contract: PR-only cancellation",
            result.stdout,
        )

    def test_validate_brainstorming_checks_release_readiness_timeout(self) -> None:
        workflow_path = self.repo / ".github/workflows/release-readiness.yml"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace("timeout-minutes: 45", "", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: measured release-readiness timeout", result.stdout)

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
