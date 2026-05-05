from __future__ import annotations

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class TemplateValidationTests(LabWorkflowTestCase):
    def test_validate_brainstorming_clean_template(self) -> None:
        run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo)

    def test_validate_brainstorming_requires_repo_skills(self) -> None:
        skill_path = self.repo / ".agents/skills/brainstorming-lab/SKILL.md"
        skill_path.unlink()
        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required artifact: .agents/skills/brainstorming-lab/SKILL.md", result.stdout)
        self.assertIn("Missing required repo skill: .agents/skills/brainstorming-lab/SKILL.md", result.stdout)

    def test_validate_brainstorming_checks_skill_frontmatter_and_dispatcher(self) -> None:
        skill_path = self.repo / ".agents/skills/project-finalizer/SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8").replace(
            "name: project-finalizer",
            "name: wrong-finalizer",
            1,
        )
        skill_path.write_text(skill_text, encoding="utf-8")
        agents_path = self.repo / "AGENTS.md"
        agents_path.write_text(
            agents_path.read_text(encoding="utf-8").replace("$project-finalizer", "$missing-finalizer", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Repo skill has incorrect name in .agents/skills/project-finalizer/SKILL.md", result.stdout)
        self.assertIn("AGENTS.md does not reference repo skill: $project-finalizer", result.stdout)

    def test_validate_brainstorming_checks_skill_ui_metadata(self) -> None:
        metadata_path = self.repo / ".agents/skills/template-maintenance/agents/openai.yaml"
        metadata_path.write_text(
            metadata_path.read_text(encoding="utf-8").replace("$template-maintenance", "$wrong-skill", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Repo skill UI metadata must include default_prompt with $template-maintenance",
            result.stdout,
        )

    def test_validate_brainstorming_checks_python_launcher_delegation(self) -> None:
        launcher_path = self.repo / "scripts/render-intent-docs.sh"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8").replace('python/cli.py" render-intent-docs', 'legacy-render'),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Shell launcher scripts/render-intent-docs.sh is missing expected snippet", result.stdout)

    def test_validate_brainstorming_checks_powershell_launcher_delegation(self) -> None:
        launcher_path = self.repo / "scripts/lab.ps1"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8").replace('py -3 "$scriptDir/python/cli.py"', "py -3 legacy.ps1"),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PowerShell launcher scripts/lab.ps1 is missing expected snippet", result.stdout)

    def test_validate_brainstorming_checks_plugin_marketplace_entry(self) -> None:
        marketplace_path = self.repo / ".agents/plugins/marketplace.json"
        marketplace_path.write_text(
            marketplace_path.read_text(encoding="utf-8").replace(
                "./plugins/project-lifecycle-lab",
                "./plugins/wrong-plugin",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin marketplace path is incorrect for project-lifecycle-lab", result.stdout)

    def test_validate_brainstorming_checks_plugin_harness_boundary(self) -> None:
        manifest_path = self.repo / "plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace("harness runtime stays in the repo", "plugin owns runtime", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Plugin longDescription must preserve harness/plugin boundary phrase: harness runtime stays in the repo",
            result.stdout,
        )

    def test_validate_brainstorming_checks_plugin_skills_path(self) -> None:
        manifest_path = self.repo / "plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace('"skills": "./skills/"', '"skills": "./wrong-skills/"', 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin manifest skills path must be ./skills/", result.stdout)

    def test_validate_brainstorming_checks_plugin_skill_mirror_drift(self) -> None:
        plugin_skill_path = self.repo / "plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md"
        plugin_skill_path.write_text(
            plugin_skill_path.read_text(encoding="utf-8").replace("Keep conversation natural", "Keep conversation scripted", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Plugin skill mirror drifted from canonical repo skill: "
            "plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md",
            result.stdout,
        )

    def test_sync_plugin_skills_repairs_mirror_drift(self) -> None:
        source_skill_path = self.repo / ".agents/skills/brainstorming-lab/SKILL.md"
        plugin_skill_path = self.repo / "plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md"
        plugin_skill_path.write_text("stale plugin copy\n", encoding="utf-8")

        result = run_cmd(["./scripts/sync-plugin-skills"], cwd=self.repo)

        self.assertIn("Synced plugin skill mirrors from canonical repo skills", result.stdout)
        self.assertEqual(source_skill_path.read_text(encoding="utf-8"), plugin_skill_path.read_text(encoding="utf-8"))

    def test_validate_brainstorming_checks_plugin_file_map_rows(self) -> None:
        file_map_path = self.repo / "brainstorming/FILE_MAP.md"
        file_map_path.write_text(
            file_map_path.read_text(encoding="utf-8").replace(
                "| `.agents/plugins/marketplace.json` | Local plugin marketplace entry for agent-behavior distribution |\n",
                "",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FILE_MAP.md missing registry row for plugin artifact: .agents/plugins/marketplace.json", result.stdout)

    def test_validate_brainstorming_checks_template_cli_file_map_rows(self) -> None:
        file_map_path = self.repo / "brainstorming/FILE_MAP.md"
        file_map_path.write_text(
            file_map_path.read_text(encoding="utf-8").replace(
                "| `scripts/python/template_cli/workflow_render.py` | Pure markdown renderers for lab workflow artifacts |\n",
                "",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "FILE_MAP.md missing registry row for template CLI module: scripts/python/template_cli/workflow_render.py",
            result.stdout,
        )

    def test_validate_brainstorming_checks_python_file_size(self) -> None:
        oversized_path = self.repo / "tests/oversized_fixture.py"
        oversized_path.write_text("\n".join("x = 1" for _ in range(501)) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python code file exceeds 500 lines: tests/oversized_fixture.py (501)", result.stdout)

    def test_validate_brainstorming_checks_workflow_finalize_helper_imports(self) -> None:
        workflow_path = self.repo / "scripts/python/template_cli/workflow_data.py"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                "from template_cli.finalize_helpers import (",
                "from template_cli.finalize import (",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Workflow module must import finalize helper 'existing_state_value' from a helper module",
            result.stdout,
        )

    def test_validate_development_requires_repo_skills(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        (self.repo / ".agents/skills/development-governance/SKILL.md").unlink()

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required artifact: .agents/skills/development-governance/SKILL.md", result.stdout)
        self.assertIn("Missing required repo skill: .agents/skills/development-governance/SKILL.md", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
