from __future__ import annotations

import json

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

    def test_validate_brainstorming_checks_shell_launcher_macos_portability(self) -> None:
        launcher_path = self.repo / "scripts/render-intent-docs.sh"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8") + "\nreadlink -f \"$0\" >/dev/null\n",
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Shell launcher scripts/render-intent-docs.sh uses non-portable macOS pattern: GNU readlink -f",
            result.stdout,
        )

    def test_validate_brainstorming_checks_project_harness_help_parser_parity(self) -> None:
        launcher_path = self.repo / "scripts/project-harness.sh"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8").replace(" [--include-mixed]", ""),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Launcher scripts/project-harness.sh help for project-harness update "
            "is missing CLI parser option: --include-mixed",
            result.stdout,
        )

    def test_validate_brainstorming_checks_powershell_launcher_delegation(self) -> None:
        launcher_path = self.repo / "scripts/lab.ps1"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8").replace('py -3 "$scriptDir/python/cli.py"', "py -3 legacy.ps1"),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PowerShell launcher scripts/lab.ps1 is missing expected snippet", result.stdout)

    def test_validate_brainstorming_checks_windows_ci_launcher_coverage(self) -> None:
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8").replace("runs-on: windows-latest", "runs-on: ubuntu-latest", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CI workflow is missing Windows PowerShell launcher coverage: Windows runner", result.stdout)

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

    def test_validate_brainstorming_checks_finalization_overwrite_policy_paths(self) -> None:
        policy_path = self.repo / "harness_commands/finalization_overwrite_policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        del policy["paths"]["README.md"]
        policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Finalization overwrite policy missing path: README.md", result.stdout)

    def test_validate_brainstorming_checks_finalization_overwrite_policy_patterns(self) -> None:
        policy_path = self.repo / "harness_commands/finalization_overwrite_policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        del policy["patterns"]["sessions/*FINALIZATION_SESSION*.md"]
        policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Finalization overwrite policy missing pattern: sessions/*FINALIZATION_SESSION*.md",
            result.stdout,
        )

    def test_validate_brainstorming_checks_note_metadata_matches_catalog(self) -> None:
        note_path = self.repo / "notes/2026-05-07_note-0001-harness-runtime-versioning-and-binary-migration.md"
        note_path.write_text(
            note_path.read_text(encoding="utf-8")
            .replace("- Note ID: note-0001", "- Note ID: note-9999", 1)
            .replace(
                "- Title: Harness runtime versioning and binary migration",
                "- Title: Wrong note title",
                1,
            )
            .replace("- Date: 2026-05-07", "- Date: 2026-05-08", 1)
            .replace(
                "- Tags: harness,versioning,binary,rust,external-adapters,public-template",
                "- Tags: wrong-tag",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Note metadata mismatch for 'note-0001'", result.stdout)
        self.assertIn("Note ID is 'note-9999', expected 'note-0001'", result.stdout)
        self.assertIn("Title is 'Wrong note title'", result.stdout)
        self.assertIn("Date is '2026-05-08', expected '2026-05-07'", result.stdout)
        self.assertIn("Tags is 'wrong-tag'", result.stdout)

    def test_validate_brainstorming_checks_python_file_size(self) -> None:
        oversized_path = self.repo / "tests/oversized_fixture.py"
        oversized_path.write_text("\n".join("x = 1" for _ in range(351)) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python code file exceeds 350 lines: tests/oversized_fixture.py (351)", result.stdout)

    def test_validate_brainstorming_checks_python_tool_config(self) -> None:
        pyproject_path = self.repo / "pyproject.toml"
        pyproject_path.write_text(
            pyproject_path.read_text(encoding="utf-8").replace("[tool.ruff.lint]\n", "", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pyproject.toml missing required section: [tool.ruff.lint]", result.stdout)

    def test_validate_brainstorming_checks_workflow_finalize_helper_imports(self) -> None:
        workflow_path = self.repo / "scripts/python/template_cli/workflow.py"
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                "from template_cli.finalize import run_finalize_project",
                "from template_cli.finalize import run_finalize_project, _required_value",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Workflow module must import finalize helper '_required_value' from a helper module",
            result.stdout,
        )

    def test_validate_brainstorming_checks_update_source_helper_boundary(self) -> None:
        helper_path = self.repo / "scripts/python/template_cli/bootstrap_update_source.py"
        helper_path.write_text(
            helper_path.read_text(encoding="utf-8")
            + "\nif False:\n    from template_cli.bootstrap_update import _build_update_plan\n",
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Module boundary violation: scripts/python/template_cli/bootstrap_update_source.py "
            "must not import template_cli.bootstrap_update.",
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
