from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import run_cmd


@unittest.skipUnless(sys.platform == "linux", "project validation hooks require Linux /proc containment")
class ProjectValidationHookIntegrationTests(ProjectHarnessUpdateTestCase):
    def test_development_warning_is_visible_in_text_and_json(self) -> None:
        self._prepare_development(self.repo)
        count_path = self.tmpdir / "warning-count.jsonl"
        self._install_counting_hook(self.repo, count_path, warning="project warning")

        text_result = run_cmd(["./scripts/validate-development"], cwd=self.repo)
        json_result = run_cmd(["./scripts/validate-development", "--json"], cwd=self.repo)
        payload = json.loads(json_result.stdout)

        self.assertIn("- Warnings: 1", text_result.stdout)
        self.assertIn("- project warning", text_result.stdout)
        self.assertEqual(["project warning"], payload["warnings"])
        self.assertEqual(1, payload["warningCount"])

    def test_direct_development_invokes_hook_once(self) -> None:
        self._prepare_development(self.repo)
        count_path = self.tmpdir / "direct-development.jsonl"
        self._install_counting_hook(self.repo, count_path)

        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        self._assert_invocations(count_path, [("development", "validate-development")])

    def test_direct_governance_invokes_hook_once(self) -> None:
        count_path = self.tmpdir / "direct-governance.jsonl"
        self._install_counting_hook(self.repo, count_path)

        run_cmd(["./scripts/validate-governance"], cwd=self.repo)

        self._assert_invocations(count_path, [("brainstorming", "validate-governance")])

    def test_project_harness_validate_invokes_hook_once(self) -> None:
        self._prepare_development(self.repo)
        count_path = self.tmpdir / "project-harness-validate.jsonl"
        self._install_counting_hook(self.repo, count_path)

        result = run_cmd(["./scripts/project-harness", "validate"], cwd=self.repo)

        self.assertIn("Running: ./scripts/validate-governance", result.stdout)
        self.assertIn("Running: ./scripts/validate-development", result.stdout)
        self._assert_invocations(count_path, [("development", "validate-governance")])

    def test_normal_updater_apply_invokes_hook_once(self) -> None:
        source, project = self._prepare_update()
        count_path = self.tmpdir / "normal-update.jsonl"
        self._install_counting_hook(project, count_path)
        wrapper = source / "scripts/lab.sh"
        wrapper.write_text(wrapper.read_text(encoding="utf-8") + "\n# hook-count update\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self._assert_invocations(count_path, [("brainstorming", "validate-governance")])

    def test_skill_changing_updater_apply_invokes_hook_once(self) -> None:
        source, project = self._prepare_update()
        count_path = self.tmpdir / "skill-update.jsonl"
        self._install_counting_hook(project, count_path)
        skill = source / ".agents/skills/brainstorming-lab/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nHook count marker.\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
        )

        self.assertIn("sync-plugin-skills: 0", result.stdout)
        self._assert_invocations(count_path, [("brainstorming", "validate-governance")])

    def test_mutating_failing_hook_restores_project_file_and_update(self) -> None:
        source, project = self._prepare_update()
        project_file = project / "project-owned.txt"
        project_file.write_text("preserve\n", encoding="utf-8")
        hook = project / "scripts/project_harness_validation.py"
        hook.write_text(
            "import json\n"
            "from pathlib import Path\n"
            "Path('project-owned.txt').write_text('mutated\\n', encoding='utf-8')\n"
            "print(json.dumps({'failures': ['injected hook failure'], 'warnings': []}))\n",
            encoding="utf-8",
        )
        self._mark_hook_project_owned(project)
        wrapper = source / "scripts/lab.sh"
        source_before = (project / "scripts/lab.sh").read_bytes()
        wrapper.write_text(wrapper.read_text(encoding="utf-8") + "\n# rollback marker\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/project-harness", "update", "--apply", "--source-path", str(source), "--yes"],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("mutated protected worktree paths: project-owned.txt", result.stdout)
        self.assertIn("Validation failed after update apply. Rolled back", result.stdout)
        self.assertEqual("preserve\n", project_file.read_text(encoding="utf-8"))
        self.assertEqual(source_before, (project / "scripts/lab.sh").read_bytes())

    def _prepare_development(self, root: Path) -> None:
        self.write_render_fixture("finalized_state_cli_data_pipeline_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=root)

    def _prepare_update(self) -> tuple[Path, Path]:
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / f"generated-project-{len(list(self.tmpdir.iterdir()))}"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        return source, project

    def _install_counting_hook(self, root: Path, count_path: Path, *, warning: str = "") -> None:
        hook = root / "scripts/project_harness_validation.py"
        hook.write_text(
            "import argparse\n"
            "import json\n"
            "from pathlib import Path\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--mode', required=True)\n"
            "parser.add_argument('--command', required=True)\n"
            "parser.add_argument('--json', action='store_true', required=True)\n"
            "args = parser.parse_args()\n"
            f"count_path = Path({str(count_path)!r})\n"
            "with count_path.open('a', encoding='utf-8') as handle:\n"
            "    handle.write(json.dumps({'mode': args.mode, 'command': args.command}) + '\\n')\n"
            f"print(json.dumps({{'failures': [], 'warnings': {[warning] if warning else []!r}}}))\n",
            encoding="utf-8",
        )
        self._mark_hook_project_owned(root)

    def _mark_hook_project_owned(self, root: Path) -> None:
        manifest_path = root / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        project_owned = manifest["artifactInventory"]["projectOwned"]
        if "scripts/project_harness_validation.py" not in project_owned:
            project_owned.append("scripts/project_harness_validation.py")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def _assert_invocations(self, count_path: Path, expected: list[tuple[str, str]]) -> None:
        records = [json.loads(line) for line in count_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(
            [{"mode": mode, "command": command} for mode, command in expected],
            records,
        )


if __name__ == "__main__":
    unittest.main()
