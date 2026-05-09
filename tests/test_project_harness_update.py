from __future__ import annotations

import shutil
from pathlib import Path

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class ProjectHarnessUpdateTests(LabWorkflowTestCase):
    def copy_source(self) -> Path:
        source = self.tmpdir / "source-template"
        shutil.copytree(
            self.repo,
            source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        return source

    def init_git_source(self, source: Path) -> str:
        run_cmd(["git", "init", "-b", "main"], cwd=source)
        run_cmd(["git", "config", "user.name", "Test User"], cwd=source)
        run_cmd(["git", "config", "user.email", "test@example.com"], cwd=source)
        run_cmd(["git", "add", "-A"], cwd=source)
        run_cmd(["git", "commit", "-m", "baseline"], cwd=source)
        return run_cmd(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()

    def test_update_dry_run_clean_project_writes_nothing(self) -> None:
        source = self.copy_source()
        before = (self.repo / "scripts/lab.sh").read_text(encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=self.repo,
        )

        self.assertIn("Project harness update dry run", result.stdout)
        self.assertIn("Writes: none", result.stdout)
        self.assertIn("unchanged:", result.stdout)
        self.assertEqual(before, (self.repo / "scripts/lab.sh").read_text(encoding="utf-8"))

    def test_update_dry_run_refuses_ambiguous_sources(self) -> None:
        source = self.copy_source()

        result = run_cmd(
            [
                "./scripts/project-harness",
                "update",
                "--dry-run",
                "--source-path",
                str(source),
                "--source-commit",
                "abc123",
            ],
            cwd=self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires exactly one explicit update source", result.stdout)

    def test_update_dry_run_reports_locally_modified_wrapper_conflict(self) -> None:
        self.init_git_repo()
        source = self.copy_source()
        wrapper = self.repo / "scripts/lab.sh"
        wrapper.write_text(wrapper.read_text(encoding="utf-8") + "\n# local wrapper edit\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=self.repo,
        )

        self.assertIn("conflicted:", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)

    def test_update_dry_run_preserves_finalized_project_owned_paths(self) -> None:
        source = self.copy_source()
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=self.repo,
        )

        self.assertIn("project-owned-preserved:", result.stdout)
        self.assertIn("state/project-init.json", result.stdout)
        self.assertIn("docs/PROJECT_CONTEXT.md", result.stdout)

    def test_update_dry_run_reports_missing_harness_file(self) -> None:
        source = self.copy_source()
        (self.repo / "scripts/lab.sh").unlink()

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=self.repo,
        )

        self.assertIn("missing:", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)

    def test_update_dry_run_reports_conflicted_mixed_generated_file(self) -> None:
        self.init_git_repo()
        source = self.copy_source()
        readme = self.repo / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nlocal readme edit\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=self.repo,
        )

        self.assertIn("conflicted:", result.stdout)
        self.assertIn("README.md", result.stdout)

    def test_update_dry_run_uses_recorded_source_baseline_for_clean_harness_update(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        source_wrapper = source / "scripts/lab.sh"
        source_wrapper.write_text(
            source_wrapper.read_text(encoding="utf-8") + "\n# target wrapper update\n",
            encoding="utf-8",
        )

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=project,
        )

        self.assertIn("Recorded source baseline: resolved", result.stdout)
        self.assertIn("harness-owned:", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)
        self.assertNotIn("conflicted: 1\n  - scripts/lab.sh", result.stdout)

    def test_update_dry_run_conflicts_when_current_and_target_changed_from_recorded_source(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        source_wrapper = source / "scripts/lab.sh"
        source_wrapper.write_text(
            source_wrapper.read_text(encoding="utf-8") + "\n# target wrapper update\n",
            encoding="utf-8",
        )
        project_wrapper = project / "scripts/lab.sh"
        project_wrapper.write_text(
            project_wrapper.read_text(encoding="utf-8") + "\n# local wrapper update\n",
            encoding="utf-8",
        )

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=project,
        )

        self.assertIn("Recorded source baseline: resolved", result.stdout)
        self.assertIn("conflicted:", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)
