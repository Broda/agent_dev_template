from __future__ import annotations

import os

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class ProjectHarnessBootstrapTests(LabWorkflowTestCase):
    def test_project_harness_new_creates_valid_brainstorming_copy(self) -> None:
        target = self.tmpdir / "new-project"

        result = run_cmd(["./scripts/project-harness", "new", str(target)], cwd=self.repo)

        self.assertIn("Created project harness:", result.stdout)
        self.assertTrue((target / "README.md").exists())
        self.assertTrue((target / ".git").exists())
        self.assertIn("Initialized independent Git repository with no remote.", result.stdout)
        remotes = run_cmd(["git", "remote"], cwd=target)
        self.assertEqual(remotes.stdout.strip(), "")
        log = run_cmd(["git", "log", "--oneline", "-1"], cwd=target)
        self.assertIn("Initialize project harness", log.stdout)
        self.assertIn("Current mode: brainstorming", (target / "MODE.md").read_text(encoding="utf-8"))
        run_cmd(["./scripts/validate-governance"], cwd=target)

    def test_project_harness_new_commits_without_global_git_identity(self) -> None:
        target = self.tmpdir / "ci-project"
        empty_home = self.tmpdir / "empty-home"
        empty_xdg = self.tmpdir / "empty-xdg"
        empty_home.mkdir()
        empty_xdg.mkdir()
        env = os.environ.copy()
        env["HOME"] = str(empty_home)
        env["XDG_CONFIG_HOME"] = str(empty_xdg)
        env["GIT_CONFIG_GLOBAL"] = str(self.tmpdir / "missing-global-gitconfig")

        result = run_cmd(["./scripts/project-harness", "new", str(target)], cwd=self.repo, env=env)

        self.assertIn("Created project harness:", result.stdout)
        log = run_cmd(["git", "log", "--oneline", "-1"], cwd=target, env=env)
        self.assertIn("Initialize project harness", log.stdout)
        name = run_cmd(["git", "config", "--get", "user.name"], cwd=target, env=env)
        email = run_cmd(["git", "config", "--get", "user.email"], cwd=target, env=env)
        self.assertEqual(name.stdout.strip(), "Project Harness")
        self.assertEqual(email.stdout.strip(), "project-harness@example.invalid")

    def test_project_harness_new_no_git_creates_plain_copy(self) -> None:
        target = self.tmpdir / "plain-project"

        result = run_cmd(["./scripts/project-harness", "new", str(target), "--no-git"], cwd=self.repo)

        self.assertIn("Git was not initialized because --no-git was supplied.", result.stdout)
        self.assertFalse((target / ".git").exists())
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

    def test_project_harness_new_rejects_origin_with_no_git(self) -> None:
        target = self.tmpdir / "invalid-project"

        result = run_cmd(
            [
                "./scripts/project-harness",
                "new",
                str(target),
                "--origin",
                "https://example.com/example/project.git",
                "--no-git",
            ],
            cwd=self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--origin cannot be used with --no-git.", result.stdout)

    def test_project_harness_validate_runs_governance_checks(self) -> None:
        result = run_cmd(["./scripts/project-harness", "validate"], cwd=self.repo)

        self.assertIn("Running: ./scripts/validate-governance", result.stdout)
        self.assertIn("Exit code: 0", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
