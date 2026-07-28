from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


def _mapping_block(text: str, key: str, indent: int) -> str:
    lines = text.splitlines()
    target = f"{' ' * indent}{key}:"
    for index, line in enumerate(lines):
        if line != target:
            continue
        for end in range(index + 1, len(lines)):
            candidate = lines[end]
            if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= indent:
                return "\n".join(lines[index:end])
        return "\n".join(lines[index:])
    return ""


def _checkout_step(job_block: str) -> str:
    lines = job_block.splitlines()
    target = "      - name: Checkout"
    for index, line in enumerate(lines):
        if line != target:
            continue
        for end in range(index + 1, len(lines)):
            candidate = lines[end]
            if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= 6:
                return "\n".join(lines[index:end])
        return "\n".join(lines[index:])
    return ""


class GithubWorkflowPolicyTests(LabWorkflowTestCase):
    def test_historical_suite_jobs_fetch_full_prior_consumer_history(self) -> None:
        required_jobs = {
            ".github/workflows/ci.yml": (
                "test-and-validate",
                "windows-powershell-launchers",
            ),
            ".github/workflows/release-readiness.yml": ("public-template-smoke",),
        }

        for relative_path, job_names in required_jobs.items():
            workflow_text = (self.repo / relative_path).read_text(encoding="utf-8")
            for job_name in job_names:
                with self.subTest(workflow=relative_path, job=job_name):
                    job_block = _mapping_block(workflow_text, job_name, 2)
                    checkout_step = _checkout_step(job_block)
                    self.assertIn("        uses: actions/checkout@v6", checkout_step)
                    self.assertIn("          fetch-depth: 0", checkout_step)

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

    def test_validate_development_checks_generated_ci_concurrency_identity(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8")
            .replace(
                "group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}",
                "group: ${{ github.workflow }}-${{ github.event.pull_request.number }}",
                1,
            )
            .replace(
                "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
                "cancel-in-progress: true",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: PR-scoped concurrency group", result.stdout)
        self.assertIn("missing CI-efficiency contract: PR-only cancellation", result.stdout)

    def test_validate_development_rejects_concurrency_rebound_outside_concurrency_block(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace(
                "concurrency:\n"
                "  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}\n"
                "  cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
                "env:\n"
                "  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}\n"
                "  cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: PR-scoped concurrency group", result.stdout)
        self.assertIn("missing CI-efficiency contract: PR-only cancellation", result.stdout)

    def test_validate_development_rejects_missing_generated_job_timeout(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace("    timeout-minutes: 60\n", "", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: conservative generated-job timeout", result.stdout)

    def test_validate_development_rejects_generated_timeout_rebound_under_permissions(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace(
                "    timeout-minutes: 60\n    permissions:\n      contents: read",
                "    permissions:\n      timeout-minutes: 60\n      contents: read",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: conservative generated-job timeout", result.stdout)

    def test_validate_development_requires_timeout_on_every_emitted_job_including_windows(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace(
                "jobs:\n",
                "jobs:\n"
                "  windows-smoke:\n"
                "    runs-on: windows-latest\n"
                "    permissions:\n"
                "      contents: read\n"
                "    steps:\n"
                "      - name: Windows smoke\n"
                "        shell: pwsh\n"
                "        run: ./scripts/validate-development.ps1\n"
                "\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "missing CI-efficiency contract: conservative generated-job timeout (windows-smoke)",
            result.stdout,
        )

    def test_validate_development_checks_failure_only_three_day_drift_upload(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8")
            .replace("        if: failure()", "        if: always()", 1)
            .replace("          retention-days: 3", "          retention-days: 4", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: failure-only drift upload", result.stdout)
        self.assertIn("missing CI-efficiency contract: three-day diagnostic retention", result.stdout)

    def test_validate_development_rejects_drift_policy_rebound_to_different_step(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace(
                "      - name: Upload generated intent-doc drift",
                "      - name: Upload unrelated diagnostics",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract: failure-only drift upload", result.stdout)
        self.assertIn("missing CI-efficiency contract: three-day diagnostic retention", result.stdout)

    def test_validate_development_does_not_require_template_only_workflows(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        (self.repo / ".github/workflows/governance-audit.yml").unlink()
        (self.repo / ".github/workflows/release-readiness.yml").unlink()

        run_cmd(["./scripts/validate-development"], cwd=self.repo)

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
