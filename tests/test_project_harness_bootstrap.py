from __future__ import annotations

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class ProjectHarnessBootstrapTests(LabWorkflowTestCase):
    def test_project_harness_new_creates_valid_brainstorming_copy(self) -> None:
        target = self.tmpdir / "new-project"

        result = run_cmd(["./scripts/project-harness", "new", str(target)], cwd=self.repo)

        self.assertIn("Created project harness:", result.stdout)
        self.assertTrue((target / "README.md").exists())
        self.assertFalse((target / ".git").exists())
        self.assertIn("Current mode: brainstorming", (target / "MODE.md").read_text(encoding="utf-8"))
        run_cmd(["./scripts/validate-governance"], cwd=target)

    def test_project_harness_new_refuses_existing_target(self) -> None:
        target = self.tmpdir / "existing-project"
        target.mkdir()

        result = run_cmd(["./scripts/project-harness", "new", str(target)], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target already exists:", result.stdout)

    def test_project_harness_new_origin_initializes_git_remote(self) -> None:
        target = self.tmpdir / "remote-project"

        result = run_cmd(
            [
                "./scripts/project-harness",
                "new",
                str(target),
                "--origin",
                "https://example.com/example/project.git",
            ],
            cwd=self.repo,
        )

        self.assertIn("Configured origin: https://example.com/example/project.git", result.stdout)
        origin = run_cmd(["git", "remote", "get-url", "origin"], cwd=target)
        self.assertEqual(origin.stdout.strip(), "https://example.com/example/project.git")
        self.assertIn("Current mode: brainstorming", (target / "MODE.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    import unittest

    unittest.main()
