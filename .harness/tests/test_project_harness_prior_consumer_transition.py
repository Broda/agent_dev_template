from __future__ import annotations

import json
import os
import shutil
import stat

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import REPO_ROOT, run_cmd

PRIOR_CONSUMER_COMMIT = "af6d7a702467ad8c559a730db9060dc41deb3e82"
EXCLUDED_TEMPLATE_FILES = [
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/governance-audit.yml",
    ".github/workflows/release-readiness.yml",
]
CUSTOM_SCRIPT_PATHS = [
    "scripts/application_report.py",
    "scripts/project_maintenance",
]


class ProjectHarnessPriorConsumerTransitionTests(ProjectHarnessUpdateTestCase):
    def test_exact_prior_consumer_transitions_safely_and_rolls_back_hook_failure(self) -> None:
        old_source = self._checkout(PRIOR_CONSUMER_COMMIT, "prior-template")
        target_source = self._target_source()
        project = self.tmpdir / "prior-consumer"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=old_source)
        self.install_finalized_cli_project(project)
        self._install_project_content(project)
        self._remove_excluded_template_files(project)
        self._initialize_consumer_git(project)
        self._prepare_target_candidate(target_source, project)

        old_planner = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(target_source)],
            cwd=project,
        )
        self.assertIn("scripts/application_report.py", self._category(old_planner.stdout, "conflicted"))
        self.assertIn("scripts/project_harness_validation.py", self._category(old_planner.stdout, "conflicted"))

        target_backend = [
            "python3",
            str(target_source / ".harness/runtime/python/cli.py"),
            "project-harness-update",
        ]
        dry_run = run_cmd(
            [*target_backend, "--dry-run", "--source-path", str(target_source), "--json"],
            cwd=project,
        )
        payload = json.loads(dry_run.stdout)
        plan = payload["plan"]

        self.assertTrue(payload["plannerTransition"]["required"])
        self.assertIn("project-harness-update --apply", payload["plannerTransition"]["applyCommand"])
        self.assertEqual([], plan["added"])
        self.assertEqual([], plan["removed"])
        self.assertEqual([], plan["conflicted"])
        self.assertEqual([], plan["mixed-generated"])
        self.assertIn(".gitignore", plan["project-owned-preserved"])
        self.assertIn(".harness/history/exports/.gitkeep", plan["missing"])
        for relative_path in [*CUSTOM_SCRIPT_PATHS, "scripts/project_harness_validation.py"]:
            self.assertIn(relative_path, plan["project-owned-preserved"])
        self.assertIn(".harness/history/sessions/project-history.md", plan["project-owned-preserved"])
        self._assert_missing_paths_are_explained(plan["missing"], target_source)
        for relative_path in EXCLUDED_TEMPLATE_FILES:
            self.assertNotIn(relative_path, {path for paths in plan.values() for path in paths})

        before = self._preserved_bytes(project)
        result = run_cmd(
            [*target_backend, "--apply", "--source-path", str(target_source), "--yes"],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertEqual(before, self._preserved_bytes(project))
        for relative_path in EXCLUDED_TEMPLATE_FILES:
            self.assertFalse((project / relative_path).exists())
        self.assertIn(
            "# 0.2.0 wrapper transition marker",
            (project / "scripts/lab.sh").read_text(encoding="utf-8"),
        )
        manifest = json.loads((project / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("0.2.0", manifest["harnessVersion"])
        self.assertEqual(2, manifest["compatibility"]["capabilityVersion"])
        self.assertNotIn("scripts/", manifest["artifactInventory"]["harnessOwned"])
        self.assertIn("scripts/project_harness_validation.py", manifest["artifactInventory"]["projectOwned"])
        self.assertIn(".harness/history/", manifest["artifactInventory"]["archival"])
        self._assert_executable_modes(project, manifest["posixExecutablePaths"])
        plugin_manifest = json.loads(
            (project / ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads((project / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual("0.2.0", plugin_manifest["version"])
        self.assertEqual("0.1.1", marketplace["plugins"][0]["version"])
        self.assertEqual(
            (project / ".agents/skills/brainstorming-lab/SKILL.md").read_bytes(),
            (project / ".harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md").read_bytes(),
        )

        self._assert_mutating_hook_failure_rolls_back(project, target_source)

    def _install_project_content(self, project) -> None:
        (project / CUSTOM_SCRIPT_PATHS[0]).write_text("print('project report')\n", encoding="utf-8")
        executable = project / CUSTOM_SCRIPT_PATHS[1]
        executable.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
        hook = project / "scripts/project_harness_validation.py"
        hook.write_text(
            "import json\nprint(json.dumps({'failures': [], 'warnings': []}))\n",
            encoding="utf-8",
        )
        history = project / ".harness/history"
        (history / "sessions").mkdir(parents=True, exist_ok=True)
        (history / "exports").mkdir(parents=True, exist_ok=True)
        (history / "sessions/project-history.md").write_text("# Project history\n", encoding="utf-8")
        (history / "exports/project-summary.md").write_text("# Project summary\n", encoding="utf-8")
        ignored = project / ".cache/local-state.txt"
        ignored.parent.mkdir(parents=True, exist_ok=True)
        ignored.write_text("keep local\n", encoding="utf-8")
        mode = project / "MODE.md"
        mode.write_text(mode.read_text(encoding="utf-8") + "\nProject-local mixed marker.\n", encoding="utf-8")

    def _prepare_target_candidate(self, target_source, project) -> None:
        shutil.copy2(project / "README.md", target_source / "README.md")
        wrapper = target_source / "scripts/lab.sh"
        wrapper.write_text(
            wrapper.read_text(encoding="utf-8") + "\n# 0.2.0 wrapper transition marker\n",
            encoding="utf-8",
        )
        run_cmd(["git", "config", "user.name", "Test User"], cwd=target_source)
        run_cmd(["git", "config", "user.email", "test@example.com"], cwd=target_source)
        run_cmd(["git", "add", "-A"], cwd=target_source)
        run_cmd(["git", "commit", "-m", "target 0.2.0 candidate"], cwd=target_source)

    def _assert_mutating_hook_failure_rolls_back(self, project, target_source) -> None:
        hook = project / "scripts/project_harness_validation.py"
        hook.write_text(
            "import json\n"
            "from pathlib import Path\n"
            "Path('scripts/application_report.py').write_text('mutated\\n', encoding='utf-8')\n"
            "print(json.dumps({'failures': ['injected transition rollback failure'], 'warnings': []}))\n",
            encoding="utf-8",
        )
        custom_before = (project / CUSTOM_SCRIPT_PATHS[0]).read_bytes()
        wrapper_path = project / "scripts/lab.sh"
        wrapper_before = wrapper_path.read_bytes()
        target_wrapper = target_source / "scripts/lab.sh"
        target_wrapper.write_text(
            target_wrapper.read_text(encoding="utf-8") + "\n# rollback candidate\n",
            encoding="utf-8",
        )

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(target_source), "--yes"],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("mutated protected worktree paths: scripts/application_report.py", result.stdout)
        self.assertIn("Validation failed after update apply. Rolled back", result.stdout)
        self.assertEqual(custom_before, (project / CUSTOM_SCRIPT_PATHS[0]).read_bytes())
        self.assertEqual(wrapper_before, wrapper_path.read_bytes())

    def _assert_missing_paths_are_explained(self, missing_paths, target_source) -> None:
        manifest = json.loads((target_source / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        harness_owned = set(manifest["artifactInventory"]["harnessOwned"])
        for relative_path in missing_paths:
            self.assertTrue(
                relative_path in harness_owned
                or any(entry.endswith("/") and relative_path.startswith(entry) for entry in harness_owned),
                relative_path,
            )

    def _preserved_bytes(self, project):
        paths = [
            *CUSTOM_SCRIPT_PATHS,
            "scripts/project_harness_validation.py",
            ".harness/history/sessions/project-history.md",
            ".harness/history/exports/project-summary.md",
            ".cache/local-state.txt",
            "MODE.md",
            "state/project-init.json",
            "state/project-init.schema.v2.json",
        ]
        return {path: (project / path).read_bytes() for path in paths}

    def _initialize_consumer_git(self, project) -> None:
        run_cmd(["git", "init", "-b", "main"], cwd=project)
        run_cmd(["git", "config", "user.name", "Test User"], cwd=project)
        run_cmd(["git", "config", "user.email", "test@example.com"], cwd=project)
        run_cmd(["git", "add", "-A"], cwd=project)
        run_cmd(["git", "commit", "-m", "prior consumer with project content"], cwd=project)

    def _target_source(self):
        source = self.tmpdir / "target-template"
        run_cmd(["git", "clone", "--quiet", str(REPO_ROOT), str(source)], cwd=self.tmpdir)
        shutil.copytree(
            REPO_ROOT,
            source,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        return source

    def _checkout(self, commit, dirname):
        source = self.tmpdir / dirname
        run_cmd(["git", "clone", "--quiet", str(REPO_ROOT), str(source)], cwd=self.tmpdir)
        run_cmd(["git", "checkout", "--quiet", commit], cwd=source)
        return source

    def _remove_excluded_template_files(self, project) -> None:
        for relative_path in EXCLUDED_TEMPLATE_FILES:
            (project / relative_path).unlink()

    def _assert_executable_modes(self, project, paths) -> None:
        if os.name == "nt":
            return
        for relative_path in paths:
            self.assertEqual(0o755, stat.S_IMODE((project / relative_path).stat().st_mode))
        self.assertEqual(0o755, stat.S_IMODE((project / CUSTOM_SCRIPT_PATHS[1]).stat().st_mode))

    @staticmethod
    def _category(output: str, label: str) -> str:
        section = output.split(f"{label}:", 1)[1].splitlines()[1:]
        paths = []
        for line in section:
            if line and not line.startswith("  "):
                break
            if line.startswith("  - "):
                paths.append(line[4:])
        return "\n".join(paths)


if __name__ == "__main__":
    import unittest

    unittest.main()
