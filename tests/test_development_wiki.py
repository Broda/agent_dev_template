from __future__ import annotations

import json
import os

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentWikiTests(LabWorkflowTestCase):
    def test_lab_wiki_render_noops_when_disabled(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        result = run_cmd(["./scripts/lab", "wiki-render"], cwd=self.repo)

        self.assertIn("Wiki tooling is disabled", result.stdout)
        self.assertFalse((self.tmpdir / "repo.wiki").exists())

    def test_lab_wiki_render_creates_curated_pages_in_existing_checkout(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        self.enable_wiki()
        wiki_dir = self.tmpdir / "repo.wiki"
        wiki_dir.mkdir()
        run_cmd(["git", "init"], cwd=wiki_dir)

        result = run_cmd(["./scripts/lab", "wiki-render"], cwd=self.repo)

        self.assertIn("Rendered 8 wiki pages", result.stdout)
        for name in [
            "Home.md",
            "Getting-Started.md",
            "Architecture.md",
            "Roadmap.md",
            "Decisions.md",
            "Verification.md",
            "Release-Notes.md",
            "_Sidebar.md",
        ]:
            self.assertTrue((wiki_dir / name).exists(), name)
        home = (wiki_dir / "Home.md").read_text(encoding="utf-8")
        architecture = (wiki_dir / "Architecture.md").read_text(encoding="utf-8")
        decisions = (wiki_dir / "Decisions.md").read_text(encoding="utf-8")
        self.assertIn("# Render Fixture", home)
        self.assertIn("[[Getting Started]]", home)
        self.assertIn("Source: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)", architecture)
        self.assertIn("docs/adr/ADR-0001-record-architecture-decisions.md", decisions)

    def test_lab_wiki_render_clones_missing_checkout(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        self.enable_wiki()
        self.init_git_repo()
        run_cmd(["git", "init", "--bare", str(self.tmpdir / "origin.wiki.git")], cwd=self.tmpdir)
        run_cmd(["git", "remote", "add", "origin", str(self.tmpdir / "origin.git")], cwd=self.repo)

        result = run_cmd(["./scripts/lab", "wiki-render"], cwd=self.repo)

        self.assertIn("Cloning wiki remote:", result.stdout)
        self.assertTrue((self.tmpdir / "repo.wiki/.git").is_dir())
        self.assertTrue((self.tmpdir / "repo.wiki/Home.md").exists())

    def test_lab_wiki_render_reports_clone_failure(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        self.enable_wiki()
        self.init_git_repo()
        run_cmd(["git", "remote", "add", "origin", str(self.tmpdir / "missing.git")], cwd=self.repo)

        result = run_cmd(["./scripts/lab", "wiki-render"], cwd=self.repo, check=False)

        self.assertEqual(result.returncode, 1)
        self.assertIn("Could not clone the GitHub Wiki repository.", result.stdout)
        self.assertIn("first page created on GitHub", result.stdout)

    def test_lab_wiki_render_honors_env_override(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        self.enable_wiki()
        wiki_dir = self.tmpdir / "custom.wiki"
        wiki_dir.mkdir()
        run_cmd(["git", "init"], cwd=wiki_dir)
        env = {**os.environ, "PROJECT_HARNESS_WIKI_DIR": str(wiki_dir)}

        run_cmd(["./scripts/lab", "wiki-render"], cwd=self.repo, env=env)

        self.assertTrue((wiki_dir / "Home.md").exists())
        self.assertFalse((self.tmpdir / "repo.wiki/Home.md").exists())

    def test_lab_wiki_check_detects_clean_and_dirty_wiki_checkout(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        self.enable_wiki()
        self.init_git_repo()
        wiki_dir = self.tmpdir / "repo.wiki"
        wiki_dir.mkdir()
        run_cmd(["git", "init"], cwd=wiki_dir)
        (self.repo / "README.md").write_text("# Changed public docs\n", encoding="utf-8")

        clean_result = run_cmd(["./scripts/lab", "wiki-check"], cwd=self.repo, check=False)
        self.assertEqual(clean_result.returncode, 1)
        self.assertIn("wiki check failed", clean_result.stdout)

        (wiki_dir / "Home.md").write_text("# Dirty wiki\n", encoding="utf-8")
        dirty_result = run_cmd(["./scripts/lab", "wiki-check"], cwd=self.repo)
        self.assertIn("wiki check ok", dirty_result.stdout)

    def test_lab_wiki_commands_block_in_brainstorming_mode(self) -> None:
        result = run_cmd(["./scripts/lab", "wiki-render"], cwd=self.repo, check=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn("/lab wiki-render is not available in brainstorming mode", result.stderr)

    def enable_wiki(self) -> None:
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["documentation"] = {
            "wiki": {
                "enabled": True,
                "pathEnv": "PROJECT_HARNESS_WIKI_DIR",
                "defaultCheckout": "../repo.wiki",
                "remote": "",
            }
        }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import unittest

    unittest.main()
