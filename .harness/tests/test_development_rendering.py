from __future__ import annotations

import hashlib
import json
import textwrap

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentRenderingTests(LabWorkflowTestCase):
    RENDERED_ARTIFACTS_WITH_PERSISTENCE = [
        "README.md",
        "CHANGELOG.md",
        ".gitignore",
        ".github/workflows/ci.yml",
        "docs/PROJECT_CONTEXT.md",
        "docs/ROADMAP.md",
        "docs/ARCHITECTURE.md",
        "docs/FILE_MAP.md",
        "docs/GOVERNANCE_INDEX.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
        "docs/SECURITY_POLICY.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
        "docs/MIGRATION_POLICY.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        "docs/adr/ADR-TEMPLATE.md",
    ]
    RENDERED_ARTIFACT_HASHES_WITH_PERSISTENCE = {
        "README.md": "c2e9cbe27ec3736862d63926b052581b3ccc95aba64e8960b5f508657a10f4a3",
        "CHANGELOG.md": "6b0e43176413e4e809d46f89b5da23c3976050f6c2dc22a774852399963f09a3",
        ".gitignore": "8ed32c34caaa326b71d25ce9835819a720ec3c2a91585b53bf22c75d0bbea2fe",
        ".github/workflows/ci.yml": "906f2350397192fad881369ec876626aa8c76f3bf0343d8c0094dfe3545c2287",
        "docs/PROJECT_CONTEXT.md": "b570c7599f1291ad4895af757c6237204e1785be84dab0a51421628ee2086844",
        "docs/ROADMAP.md": "df15c13faef4234a6a77de7d6bbf50e0cb639afbd14611afb7aec43e4149427a",
        "docs/ARCHITECTURE.md": "a6b49978352cefcdff1c9ece45b705bc557bf3d12b6a1edc551e04af97bd254d",
        "docs/FILE_MAP.md": "7098cf4ce0d6ec3387972ad897e8462f0dd50357253222611e85a6ef7d6ea4bc",
        "docs/GOVERNANCE_INDEX.md": "497048e642436fcce5bf2a274f1c7baff743f0c7ee9b39459cc3fc4afd43cf65",
        "docs/VERSIONING_AND_RELEASE_POLICY.md": "450156f75707fa11d04f78743a91ceec5e9864daad5115bcba4a41734767c1ec",
        "docs/SECURITY_POLICY.md": "62e4fa364aff311b643edb7e9b95143665cb9ed1f8fb993793393e6b78f91de8",
        "docs/RUNTIME_VERIFICATION_REPORT.md": "b4b6d2b644c8caf562a8be76599e07b8ab322c55a006f74f92a2b16d35597569",
        "docs/MIGRATION_POLICY.md": "814a50f3e97822b55759d7ae31d9635b1f0a3d055c9e5ea1b09833fba9abcd87",
        "docs/adr/ADR-0001-record-architecture-decisions.md": "8b9915a8255208b7013a601a8041c165d0a1348c61b75eadc036325a6aaea88d",
        "docs/adr/ADR-TEMPLATE.md": "774f25a2fe377a86b588870ee31e54322568c90707242164ec9075da92472d52",
    }

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
        self.assertIn("- Active Milestone: Milestone 0 — Foundation", readme)
        self.assertIn("Active Milestone: Milestone 0 — Foundation", project_context)
        self.assertTrue(all(line.startswith("- [") for line in roadmap.splitlines() if "[ ]" in line))
        self.assertIn("./scripts/validate-development", roadmap)
        self.assertNotIn("python3 -m unittest discover -s .harness/tests -v", ci)
        self.assertIn(
            "python3 -m py_compile .harness/runtime/python/cli.py .harness/runtime/python/template_cli/*.py", ci
        )
        self.assertIn("./scripts/validate-development", ci)
        self.assertIn("./scripts/validate-governance", ci)
        self.assertIn("uses: actions/checkout@v6", ci)
        self.assertIn("uses: actions/setup-python@v6", ci)
        self.assertNotIn("uses: actions/checkout@v4", ci)
        self.assertNotIn("uses: actions/setup-python@v5", ci)
        self.assertIn("Generated GitHub Actions CI is included as a baseline guardrail", project_context)
        self.assertNotIn("No CI/CD required at this stage.", project_context)

        file_map = (self.repo / "docs/FILE_MAP.md").read_text(encoding="utf-8")
        self.assertIn("# Rendered Source Of Truth", file_map)
        self.assertIn("| `README.md` | Python renderer | Regenerate from state |", file_map)
        self.assertIn(
            "| `docs/FILE_MAP.md` | Base template | Human-editable as implementation files are added |", file_map
        )

        version_policy = (self.repo / "docs/VERSIONING_AND_RELEASE_POLICY.md").read_text(encoding="utf-8")
        runtime_report = (self.repo / "docs/RUNTIME_VERIFICATION_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("does not rely on CI/CD alone", version_policy)
        self.assertIn("Manual verification complements generated CI", runtime_report)
        self.assertNotIn("This project does not require CI/CD", version_policy)
        self.assertNotIn("Manual verification replaces CI", runtime_report)

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
            "playable loop",
            "starter progression",
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
        state["product"]["problemStatement"] = (
            "Players need a short battle loop that teaches movement and resource economy."
        )
        state["product"]["solutionSummary"] = (
            "Render a gameplay-first prototype with onboarding and starter progression."
        )
        state["product"]["mvpScope"] = (
            "Ship one playable loop with player actions, battle feedback, and a small market."
        )
        state["governance"]["keyDecisions"] = (
            "Treat gameplay, player, battle, economy, market, and onboarding as valid game-domain language."
        )
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
        first_snapshot = self._rendered_artifact_snapshot()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        second_snapshot = self._rendered_artifact_snapshot()
        self.assertEqual(first_snapshot, second_snapshot)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_rendered_development_documents_match_snapshots(self) -> None:
        self.write_render_fixture("finalized_state_with_persistence_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        actual_hashes = {
            relative_path: hashlib.sha256(content.encode()).hexdigest()
            for relative_path, content in self._rendered_artifact_snapshot().items()
        }

        self.assertEqual(self.RENDERED_ARTIFACT_HASHES_WITH_PERSISTENCE, actual_hashes)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_rerender_preserves_human_owned_docs_and_refreshes_generated_docs(self) -> None:
        self.write_render_fixture("finalized_state_with_persistence_v2.json")
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        human_markers = {
            "CHANGELOG.md": "\n\n### Changed\n- Human release note survives rerender.\n",
            "docs/FILE_MAP.md": "\n| `src/manual.py` | Human-maintained implementation note |\n",
            "docs/SECURITY_POLICY.md": "\n\n## Project Exception\nHuman security note survives rerender.\n",
            "docs/adr/ADR-TEMPLATE.md": "\n\n## Human Template Note\nKeep this local ADR guidance.\n",
        }
        for relative_path, marker in human_markers.items():
            path = self.repo / relative_path
            path.write_text(path.read_text(encoding="utf-8") + marker, encoding="utf-8")

        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projectName"] = "Updated Render Fixture"
        state["purpose"] = "Refresh generated documents while preserving human-owned policy docs."
        state["commands"]["build"] = "make updated-build"
        state["commands"]["test"] = "make updated-test"
        state["governance"]["keyDecisions"] = "Generated ADR content must refresh from changed canonical state."
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        for relative_path, marker in human_markers.items():
            self.assertIn(marker.strip(), (self.repo / relative_path).read_text(encoding="utf-8"))

        readme = (self.repo / "README.md").read_text(encoding="utf-8")
        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        architecture = (self.repo / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        adr = (self.repo / "docs/adr/ADR-0001-record-architecture-decisions.md").read_text(encoding="utf-8")
        ci = (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("# Updated Render Fixture", readme)
        self.assertIn("preserving human-owned policy docs", project_context)
        self.assertIn("make updated-build", roadmap)
        self.assertIn("Updated Render Fixture", architecture)
        self.assertIn("Generated ADR content must refresh", adr)
        self.assertIn("make updated-test", ci)

    def test_render_uses_state_ci_policy_when_present(self) -> None:
        self.write_render_fixture()
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["documentation"] = {
            "ciPolicy": "Generated CI is advisory; release decisions require local smoke evidence."
        }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        project_context = (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Generated CI is advisory; release decisions require local smoke evidence.", project_context)

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

    def _rendered_artifact_snapshot(self) -> dict[str, str]:
        return {
            relative_path: (self.repo / relative_path).read_text(encoding="utf-8")
            for relative_path in self.RENDERED_ARTIFACTS_WITH_PERSISTENCE
        }


if __name__ == "__main__":
    import unittest

    unittest.main()
