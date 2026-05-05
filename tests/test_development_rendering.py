from __future__ import annotations

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentRenderingTests(LabWorkflowTestCase):
    def test_render_and_validate_development_from_checked_in_fixture(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)
        readme = (self.repo / "README.md").read_text(encoding="utf-8")
        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("# Render Fixture", readme)
        self.assertIn("Render development docs from a finalized canonical state fixture.", readme)
        self.assertIn("Development-mode rendering needs a stable, reusable finalized-state fixture.", project_context)
        self.assertIn("Rendered docs drift from the state schema or validation contract.", project_context)
        self.assertIn("./scripts/validate-development", roadmap)

    def test_render_and_validate_development_with_non_game_web_app_fixture(self) -> None:
        self.write_render_fixture("finalized_state_web_app_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)
        readme = (self.repo / "README.md").read_text(encoding="utf-8").lower()
        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8").lower()
        architecture = (self.repo / "docs/ARCHITECTURE.md").read_text(encoding="utf-8").lower()
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8").lower()
        for banned_term in [
            "gameplay",
            "player",
            "battle",
            "economy",
            "market",
            "playable loop",
            "starter progression",
            "onboarding",
        ]:
            self.assertNotIn(banned_term, readme)
            self.assertNotIn(banned_term, project_context)
            self.assertNotIn(banned_term, architecture)
            self.assertNotIn(banned_term, roadmap)
        self.assertIn("operations teams need one internal system for location and contact data", project_context)
        self.assertIn("editor-first internal web platform", readme)
        self.assertIn("shared postgresql", architecture)
        self.assertIn("pnpm build", roadmap)

    def test_render_and_validate_development_with_persistence_fixture(self) -> None:
        self.write_render_fixture("finalized_state_with_persistence_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)
        migration_policy = self.repo / "docs/MIGRATION_POLICY.md"
        gitignore_lines = (self.repo / ".gitignore").read_text(encoding="utf-8").splitlines()
        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        self.assertTrue(migration_policy.exists())
        self.assertIn("SQLite", project_context)
        self.assertEqual(gitignore_lines.count("*.db"), 1)
        self.assertEqual(gitignore_lines.count("*.sqlite"), 1)
        self.assertEqual(gitignore_lines.count("*.sqlite3"), 1)

    def test_render_development_docs_is_idempotent_with_persistence_fixture(self) -> None:
        self.write_render_fixture("finalized_state_with_persistence_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        first_snapshot = {
            "README.md": (self.repo / "README.md").read_text(encoding="utf-8"),
            ".gitignore": (self.repo / ".gitignore").read_text(encoding="utf-8"),
            "docs/PROJECT_CONTEXT.md": (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8"),
            "docs/ROADMAP.md": (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8"),
            "docs/MIGRATION_POLICY.md": (self.repo / "docs/MIGRATION_POLICY.md").read_text(encoding="utf-8"),
        }
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        second_snapshot = {
            "README.md": (self.repo / "README.md").read_text(encoding="utf-8"),
            ".gitignore": (self.repo / ".gitignore").read_text(encoding="utf-8"),
            "docs/PROJECT_CONTEXT.md": (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8"),
            "docs/ROADMAP.md": (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8"),
            "docs/MIGRATION_POLICY.md": (self.repo / "docs/MIGRATION_POLICY.md").read_text(encoding="utf-8"),
        }
        self.assertEqual(first_snapshot, second_snapshot)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)


if __name__ == "__main__":
    import unittest

    unittest.main()
