from __future__ import annotations

import json
import shutil

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class TemplatePluginValidationTests(LabWorkflowTestCase):
    def test_validate_brainstorming_checks_plugin_marketplace_entry(self) -> None:
        marketplace_path = self.repo / ".agents/plugins/marketplace.json"
        marketplace_path.write_text(
            marketplace_path.read_text(encoding="utf-8").replace(
                "./.harness/plugins/project-lifecycle-lab",
                "./.harness/plugins/wrong-plugin",
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin marketplace path is incorrect for project-lifecycle-lab", result.stdout)

    def test_version_alignment_covers_harness_plugin_marketplace_and_docs(self) -> None:
        harness_manifest = json.loads(
            (self.repo / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8")
        )
        plugin_manifest = json.loads(
            (self.repo / ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads((self.repo / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        plugin_entry = next(entry for entry in marketplace["plugins"] if entry["name"] == "project-lifecycle-lab")
        expected_version = harness_manifest["harnessVersion"]

        self.assertEqual(plugin_manifest["version"], expected_version)
        self.assertEqual(plugin_entry["version"], expected_version)
        for relative_path in [
            "README.md",
            ".harness/plugins/project-lifecycle-lab/README.md",
            ".harness/docs/HARNESS_CHANGELOG.md",
        ]:
            self.assertIn(f"`{expected_version}`", (self.repo / relative_path).read_text(encoding="utf-8"))

    def test_validate_brainstorming_checks_plugin_harness_boundary(self) -> None:
        manifest_path = self.repo / ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                "harness runtime stays in the repo", "plugin owns runtime", 1
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Plugin longDescription must preserve harness/plugin boundary phrase: harness runtime stays in the repo",
            result.stdout,
        )

    def test_validate_brainstorming_checks_plugin_version_matches_harness(self) -> None:
        manifest_path = self.repo / ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace('"version": "0.2.0"', '"version": "9.9.9"', 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin manifest version must match harnessVersion 0.2.0", result.stdout)

    def test_validate_brainstorming_checks_plugin_marketplace_version(self) -> None:
        marketplace_path = self.repo / ".agents/plugins/marketplace.json"
        marketplace_path.write_text(
            marketplace_path.read_text(encoding="utf-8").replace('"version": "0.2.0"', '"version": "9.9.9"', 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin marketplace version must match harnessVersion 0.2.0", result.stdout)

    def test_validate_brainstorming_checks_plugin_public_author_metadata(self) -> None:
        manifest_path = self.repo / ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                '"email": "maintainers@example.invalid"',
                '"email": "person@example.com"',
                1,
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin manifest author.email must be maintainers@example.invalid", result.stdout)

    def test_validate_brainstorming_checks_plugin_readme_boundary(self) -> None:
        readme_path = self.repo / ".harness/plugins/project-lifecycle-lab/README.md"
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8").replace(
                "must not replace repo-local scripts", "may replace scripts", 1
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Plugin README must document packaging boundary phrase: must not replace repo-local scripts",
            result.stdout,
        )

    def test_validate_brainstorming_checks_plugin_readme_examples(self) -> None:
        readme_path = self.repo / ".harness/plugins/project-lifecycle-lab/README.md"
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8")
            .replace("`./.harness/plugins/project-lifecycle-lab`", "`./.harness/plugins/wrong-plugin`", 1)
            .replace("- `template-maintenance`", "- `wrong-skill`", 1),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Plugin README must document marketplace source path: ./.harness/plugins/project-lifecycle-lab",
            result.stdout,
        )
        self.assertIn(
            "Plugin README external-use skill list is missing: template-maintenance",
            result.stdout,
        )

    def test_plugin_package_smoke_script_checks_skills_and_metadata(self) -> None:
        result = run_cmd(["python3", "smoke_package.py"], cwd=self.repo / ".harness/plugins/project-lifecycle-lab")

        self.assertIn("Plugin package smoke check passed.", result.stdout)
        self.assertIn("brainstorming-lab", result.stdout)
        self.assertIn("template-maintenance", result.stdout)

    def test_cached_plugin_copy_preserves_packaging_contract(self) -> None:
        source = self.repo / ".harness/plugins/project-lifecycle-lab"
        cached = self.tmpdir / "plugin-cache/project-lifecycle-lab"
        shutil.copytree(source, cached)

        result = run_cmd(["python3", "smoke_package.py"], cwd=cached)

        self.assertIn("Plugin package smoke check passed.", result.stdout)
        self.assertFalse((cached / "scripts").exists())
        self.assertIn(
            "posixExecutablePaths",
            (cached / "skills/template-maintenance/SKILL.md").read_text(encoding="utf-8"),
        )

    def test_validate_brainstorming_checks_plugin_skills_path(self) -> None:
        manifest_path = self.repo / ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                '"skills": "./skills/"', '"skills": "./wrong-skills/"', 1
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Plugin manifest skills path must be ./skills/", result.stdout)

    def test_validate_brainstorming_checks_plugin_skill_mirror_drift(self) -> None:
        plugin_skill_path = self.repo / ".harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md"
        plugin_skill_path.write_text(
            plugin_skill_path.read_text(encoding="utf-8").replace(
                "Keep conversation natural", "Keep conversation scripted", 1
            ),
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Plugin skill mirror drifted from canonical repo skill: "
            ".harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md",
            result.stdout,
        )

    def test_sync_plugin_skills_repairs_mirror_drift(self) -> None:
        source_skill_path = self.repo / ".agents/skills/brainstorming-lab/SKILL.md"
        plugin_skill_path = self.repo / ".harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md"
        plugin_skill_path.write_text("stale plugin copy\n", encoding="utf-8")

        result = run_cmd(["./scripts/sync-plugin-skills"], cwd=self.repo)

        self.assertIn("Synced plugin skill mirrors from canonical repo skills", result.stdout)
        self.assertEqual(source_skill_path.read_text(encoding="utf-8"), plugin_skill_path.read_text(encoding="utf-8"))

    def test_validate_brainstorming_checks_plugin_file_map_rows(self) -> None:
        file_map_path = self.repo / ".harness/brainstorming/FILE_MAP.md"
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
        self.assertIn(
            "FILE_MAP.md missing registry row for plugin artifact: .agents/plugins/marketplace.json", result.stdout
        )
