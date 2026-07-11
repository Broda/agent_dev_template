from __future__ import annotations

import json
import os
import stat
import unittest

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import REPO_ROOT, run_cmd


class ProjectHarnessUpdateApplyTests(ProjectHarnessUpdateTestCase):
    @unittest.skipIf(os.name == "nt", "POSIX file modes are not represented by the Windows filesystem")
    def test_update_apply_repairs_mode_only_drift_from_degraded_source_copy(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        manifest = json.loads((project / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        for relative_path in manifest["posixExecutablePaths"]:
            (source / relative_path).chmod(0o644)
            (project / relative_path).chmod(0o644)
        backend = ["python3", ".harness/runtime/python/cli.py", "project-harness-update"]

        dry_run = run_cmd([*backend, "--dry-run", "--source-path", str(source)], cwd=project)
        result = run_cmd([*backend, "--apply", "--source-path", str(source), "--yes"], cwd=project)

        self.assertIn("scripts/lab", dry_run.stdout)
        self.assertIn("Applied harness update.", result.stdout)
        for relative_path in manifest["posixExecutablePaths"]:
            with self.subTest(relative_path=relative_path):
                self.assertEqual(stat.S_IMODE((project / relative_path).stat().st_mode), 0o755)

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
        plugin_skill = (project / ".harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Update hook regression marker.", canonical_skill)
        self.assertEqual(canonical_skill, plugin_skill)

    def test_update_apply_renders_intent_docs_when_registry_changes(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        registry_path = source / ".harness/commands/intent_registry.json"
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
            (project / ".harness/commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8"),
        )

    def test_update_apply_rolls_back_when_intent_hook_fails(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        registry_path = source / ".harness/commands/intent_registry.json"
        registry_path.write_text("{ invalid json\n", encoding="utf-8")
        original_registry = (project / ".harness/commands/intent_registry.json").read_text(encoding="utf-8")
        original_commands = (project / ".harness/commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Post-update hook failed. Rolled back copied files from backup:", result.stdout)
        self.assertEqual(
            original_registry, (project / ".harness/commands/intent_registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            original_commands, (project / ".harness/commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8")
        )

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

    def test_update_apply_keeps_old_finalized_cli_docs_valid_without_overwrite(self) -> None:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        self._install_finalized_cli_project(project)
        readme_path = project / "README.md"
        readme_before = readme_path.read_text(encoding="utf-8") + "\nProject-owned note: preserve this old doc.\n"
        readme_path.write_text(readme_before, encoding="utf-8")
        roadmap_path = project / "docs/ROADMAP.md"
        roadmap_before = (
            roadmap_path.read_text(encoding="utf-8")
            + "\n# Deferred Scope\n\n"
            + "- Old boilerplate mentions Web UI, API endpoints, DTO structures, TypeScript, and npm here only.\n"
        )
        roadmap_path.write_text(roadmap_before, encoding="utf-8")
        source_validator = source / ".harness/runtime/python/template_cli/validator_semantics.py"
        source_validator.write_text(
            source_validator.read_text(encoding="utf-8") + "\n# update compatibility regression marker\n",
            encoding="utf-8",
        )

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn("validate-development: 0", result.stdout)
        self.assertIn(".harness/runtime/python/template_cli/validator_semantics.py", result.stdout)
        self.assertEqual(readme_before, readme_path.read_text(encoding="utf-8"))
        self.assertEqual(roadmap_before, roadmap_path.read_text(encoding="utf-8"))

    def _install_finalized_cli_project(self, project) -> None:
        fixture_path = REPO_ROOT / ".harness/tests/fixtures/finalized_state_cli_data_pipeline_v2.json"
        state = json.loads(fixture_path.read_text(encoding="utf-8"))
        history_root = project / ".harness/history"
        (history_root / "sessions").mkdir(parents=True, exist_ok=True)
        (history_root / "notes").mkdir(parents=True, exist_ok=True)
        (history_root / "ideas").mkdir(parents=True, exist_ok=True)
        (history_root / "exports").mkdir(parents=True, exist_ok=True)
        session_files = []
        for relative_path in state["artifacts"]["sessionFiles"] + [state["artifacts"]["finalizationSession"]]:
            if not relative_path:
                continue
            archived = f".harness/history/{relative_path}"
            session_files.append(archived)
            session_path = project / archived
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session_path.write_text("# Finalized Session\n\n- Status: finalized\n", encoding="utf-8")
        state["artifacts"]["sessionFiles"] = session_files
        state["artifacts"]["finalizationSession"] = session_files[-1]
        state["governance"]["latestReviewSession"] = session_files[0]
        (history_root / "IDEA_CATALOG.md").write_text(
            "# Idea Catalog\n\n| ID | Title | Status | Owner | Sessions | Export | Notes |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| {state['ideaId']} | {state['projectName']} | finalized | Test User | `{session_files[0]}` | _n/a_ | _none_ |\n",
            encoding="utf-8",
        )
        (history_root / "NOTES_CATALOG.md").write_text(
            "# Notes Catalog\n\n| ID | Title | Date | Idea | Source | Path | Tags |\n|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        (project / "state/project-init.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        (project / "MODE.md").write_text(
            "# Repository Mode\n\nCurrent mode: development\n\nAllowed values:\n\n- brainstorming\n- development\n\n"
            "Switch modes with `./scripts/finalize-project`.\n",
            encoding="utf-8",
        )
        run_cmd(["./scripts/render-development-docs"], cwd=project)
