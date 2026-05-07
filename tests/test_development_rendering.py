from __future__ import annotations

import json
import textwrap

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentRenderingTests(LabWorkflowTestCase):
    def test_render_and_validate_development_from_checked_in_fixture(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)
        readme = (self.repo / "README.md").read_text(encoding="utf-8")
        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        ci = (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("# Render Fixture", readme)
        self.assertIn("Render development docs from a finalized canonical state fixture.", readme)
        self.assertIn("Development-mode rendering needs a stable, reusable finalized-state fixture.", project_context)
        self.assertIn("Rendered docs drift from the state schema or validation contract.", project_context)
        self.assertIn("./scripts/validate-development", roadmap)
        self.assertNotIn("python3 -m unittest discover -s tests -v", ci)
        self.assertIn("python3 -m py_compile scripts/python/cli.py scripts/python/template_cli/*.py", ci)
        self.assertIn("./scripts/validate-development", ci)
        self.assertIn("./scripts/validate-governance", ci)
        self.assertIn("uses: actions/checkout@v6", ci)
        self.assertIn("uses: actions/setup-python@v6", ci)
        self.assertNotIn("uses: actions/checkout@v4", ci)
        self.assertNotIn("uses: actions/setup-python@v5", ci)

    def test_render_and_validate_development_with_non_game_web_app_fixture(self) -> None:
        self.write_render_fixture("finalized_state_web_app_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)
        readme = (self.repo / "README.md").read_text(encoding="utf-8").lower()
        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8").lower()
        architecture = (self.repo / "docs/ARCHITECTURE.md").read_text(encoding="utf-8").lower()
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8").lower()
        ci = (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
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
        self.assertIn("cargo fmt --check", ci)

    def test_render_and_validate_development_allows_game_domain_terms_for_game_projects(self) -> None:
        self.write_render_fixture("finalized_state_v2.json")
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projectType"] = "Game"
        state["purpose"] = "Build a playable tactical game prototype."
        state["product"]["problemStatement"] = "Players need a short battle loop that teaches movement and resource economy."
        state["product"]["solutionSummary"] = "Render a gameplay-first prototype with onboarding and starter progression."
        state["product"]["mvpScope"] = "Ship one playable loop with player actions, battle feedback, and a small market."
        state["governance"]["keyDecisions"] = "Treat gameplay, player, battle, economy, market, and onboarding as valid game-domain language."
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        readme = (self.repo / "README.md").read_text(encoding="utf-8").lower()
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8").lower()
        self.assertIn("playable tactical game prototype", readme)
        self.assertIn("gameplay-first prototype", roadmap)

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
            ".github/workflows/ci.yml": (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        }
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        second_snapshot = {
            "README.md": (self.repo / "README.md").read_text(encoding="utf-8"),
            ".gitignore": (self.repo / ".gitignore").read_text(encoding="utf-8"),
            "docs/PROJECT_CONTEXT.md": (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8"),
            "docs/ROADMAP.md": (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8"),
            "docs/MIGRATION_POLICY.md": (self.repo / "docs/MIGRATION_POLICY.md").read_text(encoding="utf-8"),
            ".github/workflows/ci.yml": (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        }
        self.assertEqual(first_snapshot, second_snapshot)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_command_metavariables_and_tbd_text_do_not_trip_placeholder_validation(self) -> None:
        self.write_render_fixture()
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["techStack"]["framework"] = "future TypeScript web/Discord framework TBD"
        state["commands"]["run"] = "cargo run -p devos-cli -- <command>"
        state["implementation"] = {
            "cliCommandSurface": ["cargo run -p devos-cli -- <command>"],
            "postMvpDecisions": ["future TypeScript web/Discord framework TBD"],
        }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("`cargo run -p devos-cli -- <command>`", roadmap)
        self.assertIn("future TypeScript web/Discord framework TBD", roadmap)

    def test_validate_development_reports_precise_placeholder_location(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        roadmap_path = self.repo / "docs/ROADMAP.md"
        roadmap_path.write_text(
            roadmap_path.read_text(encoding="utf-8") + "\n- Bad generated value: <Project Name>\n",
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unresolved placeholder in docs/ROADMAP.md:", result.stdout)
        self.assertIn("<Project Name>", result.stdout)
        self.assertIn("source:", result.stdout)

    def test_render_includes_detailed_mvp_contract_in_roadmap_and_architecture(self) -> None:
        self.write_render_fixture()
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projectName"] = "DevOS"
        state["purpose"] = "Build a local-first command center for project execution."
        state["techStack"]["language"] = "Rust"
        state["techStack"]["runtime"] = "Rust stable"
        state["persistence"] = "SQLite with rusqlite"
        state["commands"]["run"] = "cargo run -p devos-cli -- <command>"
        state["product"]["mvpScope"] = "Ship the Rust CLI MVP with deterministic local storage."
        state["implementation"] = {
            "workspaceCrates": ["devos-core", "devos-storage", "devos-storage-sqlite", "devos-cli"],
            "storageImplementation": [
                "SQLite via rusqlite",
                "SQL migrations embedded with include_str!",
            ],
            "cliCommandSurface": [
                "devos init",
                "project, item, schedule, and event commands",
            ],
            "domainStatuses": ["active, blocked, done, archived"],
            "scheduleEventSemantics": ["timestamps are normalized before storage"],
            "mvpExclusions": ["no hard delete"],
            "testBaseline": ["cargo test across workspace crates"],
        }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        session_path = self.repo / "sessions/2026-04-03_idea-render-fixture.md"
        session_path.write_text(
            textwrap.dedent(
                """\
                # Brainstorming Session

                ## CLI command surface

                - devos.toml configuration
                - slug rules are deterministic and lowercase
                """
            ),
            encoding="utf-8",
        )

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        architecture = (self.repo / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        adr = (self.repo / "docs/adr/ADR-0001-record-architecture-decisions.md").read_text(encoding="utf-8")
        ci = (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("## Milestone 1 MVP Contract", roadmap)
        self.assertIn("devos-core", roadmap)
        self.assertIn("SQL migrations embedded with include_str!", roadmap)
        self.assertIn("devos.toml configuration", roadmap)
        self.assertIn("# 6. Concrete Implementation Boundaries", architecture)
        self.assertIn("devos-storage-sqlite", architecture)
        self.assertIn("timestamps are normalized before storage", architecture)
        self.assertIn("### Finalized Implementation Contract", adr)
        self.assertIn("cargo test across workspace crates", adr)
        self.assertIn("cargo fmt --check", ci)


if __name__ == "__main__":
    import unittest

    unittest.main()
