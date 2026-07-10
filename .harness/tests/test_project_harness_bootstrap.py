from __future__ import annotations

import json
import os
import shutil
import stat
import tarfile
import unittest

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


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

    @unittest.skipIf(os.name == "nt", "POSIX file modes are not represented by the Windows filesystem")
    def test_project_harness_new_normalizes_all_posix_launcher_modes(self) -> None:
        target = self.tmpdir / "mode-project"

        run_cmd(["./scripts/project-harness", "new", str(target), "--no-git"], cwd=self.repo)
        manifest = json.loads((target / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))

        for relative_path in manifest["posixExecutablePaths"]:
            with self.subTest(relative_path=relative_path):
                self.assertEqual(stat.S_IMODE((target / relative_path).stat().st_mode), 0o755)

    @unittest.skipIf(os.name == "nt", "POSIX file modes are not represented by the Windows filesystem")
    def test_project_harness_new_repairs_mode_loss_in_source_copy(self) -> None:
        manifest = json.loads((self.repo / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        for relative_path in manifest["posixExecutablePaths"]:
            (self.repo / relative_path).chmod(0o644)
        target = self.tmpdir / "repaired-project"

        run_cmd(
            [
                "python3",
                ".harness/runtime/python/cli.py",
                "project-harness-new",
                str(target),
                "--no-git",
            ],
            cwd=self.repo,
        )

        for relative_path in manifest["posixExecutablePaths"]:
            with self.subTest(relative_path=relative_path):
                self.assertEqual(stat.S_IMODE((target / relative_path).stat().st_mode), 0o755)

    def test_generated_git_archive_preserves_posix_launcher_modes(self) -> None:
        target = self.tmpdir / "archive-project"
        archive = self.tmpdir / "archive-project.tar"
        run_cmd(["./scripts/project-harness", "new", str(target)], cwd=self.repo)
        manifest = json.loads((target / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))

        index = run_cmd(
            ["git", "ls-files", "--stage", "--", *manifest["posixExecutablePaths"]],
            cwd=target,
        )
        run_cmd(
            ["git", "-c", "tar.umask=0022", "archive", "--format=tar", f"--output={archive}", "HEAD"],
            cwd=target,
        )
        with tarfile.open(archive) as package:
            members = {member.name: member for member in package.getmembers()}

        self.assertEqual(len(index.stdout.splitlines()), len(manifest["posixExecutablePaths"]))
        self.assertTrue(all(line.startswith("100755 ") for line in index.stdout.splitlines()))
        for relative_path in manifest["posixExecutablePaths"]:
            with self.subTest(relative_path=relative_path):
                self.assertEqual(members[relative_path].mode, 0o755)

    @unittest.skipUnless(
        os.name == "nt" or shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell is not available",
    )
    def test_project_harness_new_ps1_no_git_validates_copy(self) -> None:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            self.skipTest("PowerShell is not available")
        target = self.tmpdir / "windows-project"

        result = run_cmd(
            [
                powershell,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.repo / "scripts/project-harness.ps1"),
                "new",
                str(target),
                "--no-git",
            ],
            cwd=self.repo,
        )

        self.assertIn("Created project harness:", result.stdout)
        self.assertIn("Git was not initialized because --no-git was supplied.", result.stdout)
        self.assertTrue((target / "README.md").exists())

    def test_project_harness_leading_template_root_flag_is_forwarded(self) -> None:
        target = self.tmpdir / "template-root-project"

        result = run_cmd(
            ["./scripts/project-harness", "--template-root", str(self.repo), "new", str(target), "--no-git"],
            cwd=self.repo,
        )

        self.assertIn("Created project harness:", result.stdout)
        self.assertTrue((target / "README.md").exists())

    def test_project_harness_leading_template_root_without_path_fails_with_usage_error(self) -> None:
        result = run_cmd(["./scripts/project-harness", "--template-root"], cwd=self.repo, check=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn("--template-root requires a path", result.stdout + result.stderr)

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
