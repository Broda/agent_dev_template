from __future__ import annotations

import json
import textwrap

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabHandoffTests(LabWorkflowTestCase):
    def test_lab_handoff_check_reports_without_writing(self) -> None:
        self.write_handoff_fixture()
        state_before = (self.repo / "state/project-init.json").read_text(encoding="utf-8")
        sessions_before = sorted(path.name for path in (self.repo / "sessions").glob("*.md"))

        result = run_cmd(["./scripts/lab", "handoff", "--check"], cwd=self.repo)

        self.assertIn("Handoff check", result.stdout)
        self.assertIn("Filled fields:", result.stdout)
        self.assertEqual(state_before, (self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        self.assertEqual(sessions_before, sorted(path.name for path in (self.repo / "sessions").glob("*.md")))

    def test_lab_handoff_writes_state_from_multiple_sessions_and_preserves_existing_values(self) -> None:
        self.write_handoff_fixture()

        result = run_cmd(["./scripts/lab", "handoff", "--no-sync"], cwd=self.repo)

        self.assertIn("Handoff state updated: state/project-init.json", result.stdout)
        state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        self.assertEqual(state["ideaId"], "idea-lossless-handoff")
        self.assertEqual(state["techStack"]["language"], "Rust")
        self.assertEqual(state["commands"]["build"], "cargo build --locked")
        self.assertEqual(state["commands"]["test"], "cargo test --all -- --nocapture")
        self.assertEqual(state["product"]["problemStatement"], "Prevent finalization from losing deeply brainstormed implementation details.")
        self.assertEqual(state["product"]["targetUsers"], "Human-agent project owners")
        self.assertEqual(state["governance"]["mitigationPlans"], "Compile source sessions into canonical state before finalize.")
        self.assertIn("sessions/2026-04-04_idea-lossless-handoff.md", state["artifacts"]["sessionFiles"])
        self.assertTrue(any("HANDOFF_SESSION_idea-lossless-handoff" in path for path in state["artifacts"]["sessionFiles"]))
        self.assertIn("workspaceLayout", state["implementation"])
        self.assertIn("CLI crate owns quoted command parsing like `run \"daily sync\"`.", state["implementation"]["cliCommandSurface"])

    def test_lab_handoff_details_survive_finalize_and_render(self) -> None:
        self.write_handoff_fixture()
        run_cmd(["./scripts/lab", "handoff", "--no-sync"], cwd=self.repo)

        run_cmd(["./scripts/finalize-project"], cwd=self.repo)

        architecture = (self.repo / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        roadmap = (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("CLI crate owns quoted command parsing like `run \"daily sync\"`.", architecture)
        self.assertIn("Preserve spaces, apostrophes, and quoted strings in task names.", roadmap)

    def test_lab_handoff_requires_explicit_target_when_multiple_ideas_active(self) -> None:
        self.write_handoff_fixture()
        catalog_path = self.repo / "IDEA_CATALOG.md"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8")
            + "| idea-second | Second | active | Test User | `sessions/2026-04-04_idea-second.md` | _n/a_ | _none_ |\n",
            encoding="utf-8",
        )

        result = run_cmd(["./scripts/lab", "handoff", "--check"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Handoff target is ambiguous", result.stderr + result.stdout)

    def test_lab_handoff_blocks_in_development_mode(self) -> None:
        self.write_handoff_fixture()
        (self.repo / "MODE.md").write_text("Current mode: development\n", encoding="utf-8")

        result = run_cmd(["./scripts/lab", "handoff", "--check"], cwd=self.repo, check=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn("/lab handoff is not available in development mode", result.stderr)

    def write_handoff_fixture(self) -> None:
        idea_id = "idea-lossless-handoff"
        self.write_finalize_fixture(idea_id)
        (self.repo / "state/project-init.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 2,
                    "status": "draft",
                    "ideaId": "",
                    "projectName": "",
                    "owner": "",
                    "techStack": {"language": "Rust", "runtime": "", "framework": "", "packageTool": ""},
                    "commands": {"build": "cargo build --locked", "run": "", "test": ""},
                    "product": {},
                    "governance": {},
                    "artifacts": {},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.repo / f"sessions/2026-04-04_{idea_id}.md").write_text(
            textwrap.dedent(
                f"""\
                # Brainstorming Session

                ## Metadata

                - Date: 2026-04-04
                - Idea ID: `{idea_id}`
                - Title: Lossless Handoff
                - Owner: Test User

                ## Current Focus

                - One-sentence objective: Build a CLI handoff compiler that preserves rich details.
                - Project type: CLI
                - Runtime: Rust stable
                - Framework: None
                - Package tool: Cargo
                - Persistence: File-based (JSON/YAML/etc.)
                - Authentication: None
                - Determinism: High
                - Packaging: None
                - Constraints: Preserve spaces, quotes, apostrophes, and punctuation.
                - Run command: cargo run -- handoff --idea "daily sync"
                - Test command: cargo test --all -- --nocapture
                - Problem statement: Prevent finalization from losing deeply brainstormed implementation details.
                - Affected users/personas: Human-agent project owners
                - Why now: Finalization is the handoff point.
                - Value hypothesis: No lost details during mode switch.
                - Solution summary: Compile source sessions into canonical state.
                - MVP scope: Handoff command, check mode, session note, and finalization carry-forward.
                - Out of scope: Project-harness update.
                - Assumptions: One active idea is the normal path.
                - Non-goals: Replace finalization.
                - Top risks: Quotes/spaces break parsing.
                - Preventive mitigation: Compile source sessions into canonical state before finalize.
                - Contingency plan: Leave gaps visible in handoff check output.
                - Latest review outcome: conditional-pass

                ## CLI command surface

                - CLI crate owns quoted command parsing like `run "daily sync"`.
                - Preserve spaces, apostrophes, and quoted strings in task names.

                ## Workspace layout

                - `crates/handoff-cli` owns command dispatch.
                - `crates/handoff-core` owns state compilation.
                """
            ),
            encoding="utf-8",
        )
        catalog_path = self.repo / "IDEA_CATALOG.md"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8").replace(
                f"`sessions/2026-04-03_{idea_id}.md`",
                f"`sessions/2026-04-03_{idea_id}.md`, `sessions/2026-04-04_{idea_id}.md`",
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
