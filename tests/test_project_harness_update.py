from __future__ import annotations

import json

from tests.project_harness_update_helpers import ProjectHarnessUpdateTestCase
from tests.workflow_test_helpers import run_cmd


class ProjectHarnessUpdateTests(ProjectHarnessUpdateTestCase):
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
        self.assertIn("apply clean harness-owned updates:", result.stdout)
        self.assertIn("--include-mixed", result.stdout)
        self.assertNotIn("not implemented yet", result.stdout)
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
        self.assertIn("Target source worktree: dirty", result.stdout)
        self.assertIn("harness-owned:", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)
        self.assertNotIn("conflicted: 1\n  - scripts/lab.sh", result.stdout)

    def test_update_dry_run_can_resolve_source_commit_from_template_repository(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        project_manifest_path = project / "harness_commands/harness_manifest.json"
        project_manifest = json.loads(project_manifest_path.read_text(encoding="utf-8"))
        project_manifest["templateRepository"] = source.as_posix()
        project_manifest_path.write_text(json.dumps(project_manifest, indent=2) + "\n", encoding="utf-8")

        source_wrapper = source / "scripts/lab.sh"
        source_wrapper.write_text(
            source_wrapper.read_text(encoding="utf-8") + "\n# committed source-commit update\n",
            encoding="utf-8",
        )
        run_cmd(["git", "add", "scripts/lab.sh"], cwd=source)
        run_cmd(["git", "commit", "-m", "update wrapper"], cwd=source)
        target_commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-commit", target_commit],
            cwd=project,
        )

        self.assertIn("Project harness update dry run", result.stdout)
        self.assertIn(f"Target harness: 0.1.0 ({target_commit})", result.stdout)
        self.assertIn("Target source worktree: clean", result.stdout)
        self.assertIn("Recorded source baseline: resolved", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)

    def test_update_dry_run_can_resolve_release_version_from_template_repository_tag(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        project_manifest_path = project / "harness_commands/harness_manifest.json"
        project_manifest = json.loads(project_manifest_path.read_text(encoding="utf-8"))
        project_manifest["templateRepository"] = source.as_posix()
        project_manifest_path.write_text(json.dumps(project_manifest, indent=2) + "\n", encoding="utf-8")

        source_wrapper = source / "scripts/lab.sh"
        source_wrapper.write_text(
            source_wrapper.read_text(encoding="utf-8") + "\n# tagged release update\n",
            encoding="utf-8",
        )
        source_manifest_path = source / "harness_commands/harness_manifest.json"
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        source_manifest["harnessVersion"] = "0.2.0"
        source_manifest_path.write_text(json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8")
        run_cmd(["git", "add", "scripts/lab.sh", "harness_commands/harness_manifest.json"], cwd=source)
        run_cmd(["git", "commit", "-m", "release 0.2.0"], cwd=source)
        target_commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
        run_cmd(["git", "tag", "v0.2.0"], cwd=source)

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--release-version", "0.2.0"],
            cwd=project,
        )

        self.assertIn(f"Target harness: 0.2.0 ({target_commit})", result.stdout)
        self.assertIn("Target source worktree: clean", result.stdout)
        self.assertIn("Recorded source baseline: resolved", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)

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

    def test_update_dry_run_conflicts_removed_harness_file_with_local_edits(self) -> None:
        source = self.copy_source()
        obsolete_source = source / "scripts/obsolete-helper"
        obsolete_source.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        obsolete_source.unlink()
        obsolete_project = project / "scripts/obsolete-helper"
        obsolete_project.write_text("#!/usr/bin/env sh\n# local edit\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=project,
        )

        self.assertIn("conflicted:", result.stdout)
        self.assertIn("scripts/obsolete-helper", result.stdout)
