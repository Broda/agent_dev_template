from __future__ import annotations

import shutil
import unittest

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabLauncherTests(LabWorkflowTestCase):
    def test_lab_help_prints_command_guidance(self) -> None:
        for args in (["./scripts/lab", "--help"], ["./scripts/lab", "help"]):
            with self.subTest(args=args):
                result = run_cmd(args, cwd=self.repo)

                self.assertIn("Usage: ./scripts/lab <command> [args]", result.stdout)
                self.assertIn("Commands:", result.stdout)
                self.assertIn("status", result.stdout)
                self.assertIn("capture --idea-id <id>", result.stdout)
                self.assertIn("path-note --idea-id <id>", result.stdout)
                self.assertIn("evidence --task <task>", result.stdout)
                self.assertIn("wiki-render", result.stdout)
                self.assertIn("Run ./scripts/lab <command> --help", result.stdout)

    def test_lab_command_help_still_reaches_argparse(self) -> None:
        result = run_cmd(["./scripts/lab", "status", "--help"], cwd=self.repo)

        self.assertIn("usage: template-cli lab-status", result.stdout)

    def test_lab_leading_root_flag_is_forwarded(self) -> None:
        result = run_cmd(["./scripts/lab", "--root", str(self.repo), "status"], cwd=self.repo)

        self.assertIn("Mode: brainstorming", result.stdout)

    def test_lab_leading_root_flag_without_path_fails_with_usage_error(self) -> None:
        result = run_cmd(["./scripts/lab", "--root"], cwd=self.repo, check=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn("--root requires a path", result.stdout + result.stderr)

    def test_finalize_project_help_reaches_argparse(self) -> None:
        result = run_cmd(["./scripts/finalize-project", "--help"], cwd=self.repo)

        self.assertIn("usage: template-cli finalize-project", result.stdout)

    def test_validate_governance_help_reaches_argparse(self) -> None:
        result = run_cmd(["./scripts/validate-governance", "--help"], cwd=self.repo)

        self.assertIn("usage: template-cli validate-governance", result.stdout)

    def test_harness_release_check_help_reaches_argparse(self) -> None:
        result = run_cmd(["./scripts/harness-release-check", "--help"], cwd=self.repo)

        self.assertIn("usage: template-cli harness-release-check", result.stdout)

    @unittest.skipUnless(shutil.which("pwsh") or shutil.which("powershell"), "PowerShell is not available")
    def test_lab_powershell_help_prints_command_guidance(self) -> None:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        assert powershell is not None

        for arg in ("--help", "help"):
            with self.subTest(arg=arg):
                result = run_cmd(
                    [
                        powershell,
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(self.repo / "scripts/lab.ps1"),
                        arg,
                    ],
                    cwd=self.repo,
                )

                self.assertIn("Usage: ./scripts/lab <command> [args]", result.stdout)
                self.assertIn("Commands:", result.stdout)
                self.assertIn("capture --idea-id <id>", result.stdout)

    @unittest.skipUnless(shutil.which("pwsh") or shutil.which("powershell"), "PowerShell is not available")
    def test_powershell_launcher_smoke_commands(self) -> None:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        assert powershell is not None

        smoke_commands = [
            ("lab.ps1", ["status", "--help"], "usage: template-cli lab-status"),
            ("finalize-project.ps1", ["--help"], "usage: template-cli finalize-project"),
            ("harness-release-check.ps1", ["--help"], "usage: template-cli harness-release-check"),
            ("validate-governance.ps1", ["--help"], "usage: template-cli validate-governance"),
        ]
        for script_name, args, expected in smoke_commands:
            with self.subTest(script_name=script_name):
                result = run_cmd(
                    [
                        powershell,
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(self.repo / "scripts" / script_name),
                        *args,
                    ],
                    cwd=self.repo,
                )

                self.assertIn(expected, result.stdout)
