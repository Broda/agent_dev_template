from __future__ import annotations

import json

from tests.project_harness_update_helpers import ProjectHarnessUpdateTestCase
from tests.workflow_test_helpers import run_cmd


class ProjectHarnessUpdateApplyTests(ProjectHarnessUpdateTestCase):
    def test_update_apply_requires_yes_confirmation(self) -> None:
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
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source)],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to apply without --yes confirmation.", result.stdout)
        self.assertNotIn("# target wrapper update", (project / "scripts/lab.sh").read_text(encoding="utf-8"))

    def test_update_apply_applies_clean_harness_owned_update_and_validates(self) -> None:
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
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn("Target source worktree: dirty", result.stdout)
        self.assertIn("scripts/lab.sh", result.stdout)
        self.assertIn("validate-governance: 0", result.stdout)
        self.assertIn("# target wrapper update", (project / "scripts/lab.sh").read_text(encoding="utf-8"))
        self.assertTrue((project / ".harness-update-backups").exists())

    def test_update_apply_removes_clean_harness_owned_deleted_source_file(self) -> None:
        source = self.copy_source()
        obsolete_source = source / "scripts/obsolete-helper"
        obsolete_source.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        obsolete_source.unlink()

        dry_run = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(source)],
            cwd=project,
        )

        self.assertIn("removed: 1", dry_run.stdout)
        self.assertIn("scripts/obsolete-helper", dry_run.stdout)

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn("scripts/obsolete-helper", result.stdout)
        self.assertFalse((project / "scripts/obsolete-helper").exists())
        backup_files = list((project / ".harness-update-backups").glob("*/scripts/obsolete-helper"))
        self.assertTrue(backup_files)

    def test_update_apply_syncs_plugin_skills_when_repo_skill_changes(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        source_skill = source / ".agents/skills/brainstorming-lab/SKILL.md"
        source_skill.write_text(
            source_skill.read_text(encoding="utf-8") + "\nUpdate hook regression marker.\n",
            encoding="utf-8",
        )

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("Hooks:", result.stdout)
        self.assertIn("sync-plugin-skills: 0", result.stdout)
        canonical_skill = (project / ".agents/skills/brainstorming-lab/SKILL.md").read_text(encoding="utf-8")
        plugin_skill = (project / "plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Update hook regression marker.", canonical_skill)
        self.assertEqual(canonical_skill, plugin_skill)

    def test_update_apply_renders_intent_docs_when_registry_changes(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        registry_path = source / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["phrases"].append("capture hook regression")
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("Hooks:", result.stdout)
        self.assertIn("render-intent-docs: 0", result.stdout)
        self.assertIn(
            "capture hook regression",
            (project / "harness_commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8"),
        )

    def test_update_apply_rolls_back_when_intent_hook_fails(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        registry_path = source / "harness_commands/intent_registry.json"
        registry_path.write_text("{ invalid json\n", encoding="utf-8")
        original_registry = (project / "harness_commands/intent_registry.json").read_text(encoding="utf-8")
        original_commands = (project / "harness_commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Post-update hook failed. Rolled back copied files from backup:", result.stdout)
        self.assertEqual(original_registry, (project / "harness_commands/intent_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(original_commands, (project / "harness_commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8"))

    def test_update_apply_rolls_back_when_validation_fails(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        launcher_path = source / "scripts/render-intent-docs.sh"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8").replace("set -euo pipefail", "set -eo pipefail", 1),
            encoding="utf-8",
        )
        project_launcher_path = project / "scripts/render-intent-docs.sh"
        original_launcher = project_launcher_path.read_text(encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Validation failed after update apply. Rolled back copied files from backup:", result.stdout)
        self.assertEqual(original_launcher, project_launcher_path.read_text(encoding="utf-8"))

    def test_update_apply_refuses_mixed_generated_update_by_default(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        source_readme = source / "README.md"
        source_readme.write_text(
            source_readme.read_text(encoding="utf-8") + "\ntarget readme update\n",
            encoding="utf-8",
        )

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to apply mixed/generated updates without --include-mixed", result.stdout)
        self.assertNotIn("target readme update", (project / "README.md").read_text(encoding="utf-8"))

    def test_update_apply_can_include_reviewed_mixed_generated_update(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        source_readme = source / "README.md"
        source_readme.write_text(
            source_readme.read_text(encoding="utf-8") + "\ntarget readme update\n",
            encoding="utf-8",
        )

        result = run_cmd(
            [
                "./scripts/project-harness",
                "update",
                "--apply",
                "--source-path",
                str(source),
                "--yes",
                "--include-mixed",
            ],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn("README.md", result.stdout)
        self.assertIn("validate-governance: 0", result.stdout)
        self.assertIn("target readme update", (project / "README.md").read_text(encoding="utf-8"))
        backup_files = list((project / ".harness-update-backups").glob("*/README.md"))
        self.assertTrue(backup_files)
