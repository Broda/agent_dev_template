from __future__ import annotations

import textwrap

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabLifecycleTests(LabWorkflowTestCase):
    def test_lab_wrapper_capture_activate_export_flow(self) -> None:
        run_cmd(
            [
                "./scripts/lab",
                "capture",
                "--idea-id",
                "idea-wrapper-flow",
                "--title",
                "Wrapper Flow",
                "--problem",
                "Need an executable shell workflow",
                "--summary",
                "Back the docs with real commands",
                "--scope",
                "Capture and activate ideas",
                "--constraints",
                "Keep markdown readable",
                "--no-sync",
            ],
            cwd=self.repo,
        )
        run_cmd(["./scripts/lab", "activate", "--idea-id", "idea-wrapper-flow", "--no-sync"], cwd=self.repo)
        run_cmd(["./scripts/lab", "export", "--idea-id", "idea-wrapper-flow", "--no-sync"], cwd=self.repo)
        run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo)

    def test_lab_export_missing_idea_fails(self) -> None:
        result = run_cmd(
            ["./scripts/lab", "export", "--idea-id", "idea-does-not-exist", "--no-sync"],
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr.lower() + result.stdout.lower())

    def test_lab_blocks_brainstorming_only_commands_in_development_mode(self) -> None:
        self.write_render_fixture()
        result = run_cmd(
            [
                "./scripts/lab",
                "capture",
                "--idea-id",
                "idea-dev-blocked",
                "--title",
                "Should Not Write",
            ],
            cwd=self.repo,
            check=False,
        )
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("/lab capture is not available in development mode", combined)
        self.assertIn("allowed: brainstorming", combined)
        self.assertNotIn("idea-dev-blocked", (self.repo / "IDEA_CATALOG.md").read_text(encoding="utf-8"))

    def test_lab_allows_shared_commands_in_development_mode(self) -> None:
        self.write_render_fixture()
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Mode: development", result.stdout)

    def test_lab_status_reports_development_context_after_finalize(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertIn("Mode: development", result.stdout)
        self.assertIn("Project: Render Fixture", result.stdout)
        self.assertIn("Canonical state: finalized for idea-render-fixture", result.stdout)
        self.assertIn("Active milestone: Milestone 0", result.stdout)
        self.assertIn("Governance docs:", result.stdout)
        self.assertIn("Roadmap tasks:", result.stdout)
        self.assertIn("Validation command:", result.stdout)
        self.assertNotIn("Finalize readiness:", result.stdout)
        self.assertNotIn("Finalize target:", result.stdout)

    def test_lab_status_reports_ready_target_context(self) -> None:
        self.write_finalize_fixture("idea-status-ready")
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertIn("Mode: brainstorming", result.stdout)
        self.assertIn("Ideas tracked: 1 (inbox 0, active 1, parked 0, killed 0, finalized 0)", result.stdout)
        self.assertIn("Canonical state: draft for idea-status-ready", result.stdout)
        self.assertIn("Finalize target: idea-status-ready (from canonical state)", result.stdout)
        self.assertIn("Target title: Finalize Smoke", result.stdout)
        self.assertIn("Related sessions: 1", result.stdout)
        self.assertIn("Finalize readiness: ready", result.stdout)

    def test_lab_status_reports_ambiguous_multiple_active_ideas(self) -> None:
        self.write_finalize_fixture("idea-status-first")
        state_path = self.repo / "state/project-init.json"
        state_text = state_path.read_text(encoding="utf-8").replace('"ideaId": "idea-status-first"', '"ideaId": ""')
        state_path.write_text(state_text, encoding="utf-8")
        catalog_path = self.repo / "IDEA_CATALOG.md"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8")
            + "| idea-status-second | Second Idea | active | Test User | `sessions/2026-04-03_idea-status-second.md` | _n/a_ | _none_ |\n",
            encoding="utf-8",
        )
        (self.repo / "sessions/2026-04-03_idea-status-second.md").write_text(
            "# Brainstorming Session\n\n- Idea ID: `idea-status-second`\n",
            encoding="utf-8",
        )
        result = run_cmd(["./scripts/lab", "status"], cwd=self.repo)
        self.assertIn("Active ideas:", result.stdout)
        self.assertIn("- idea-status-first (Finalize Smoke)", result.stdout)
        self.assertIn("- idea-status-second (Second Idea)", result.stdout)
        self.assertIn("Finalize target: ambiguous", result.stdout)
        self.assertIn("Finalize readiness: blocked", result.stdout)
        self.assertIn("Missing before finalize: explicit --idea-id or a single active idea", result.stdout)

    def test_lab_doctor_reports_missing_finalize_fields(self) -> None:
        run_cmd(
            [
                "./scripts/lab",
                "capture",
                "--idea-id",
                "idea-doctor-blocked",
                "--title",
                "Doctor Blocked",
                "--no-sync",
            ],
            cwd=self.repo,
        )
        run_cmd(["./scripts/lab", "activate", "--idea-id", "idea-doctor-blocked", "--no-sync"], cwd=self.repo)
        result = run_cmd(["./scripts/lab", "doctor"], cwd=self.repo)
        self.assertIn("Finalize doctor", result.stdout)
        self.assertIn("Finalize target: idea-doctor-blocked (from single active idea)", result.stdout)
        self.assertIn("Finalize readiness: needs-input", result.stdout)
        self.assertIn("- session history: OK via sessions/", result.stdout)
        self.assertIn("- problem statement: MISSING", result.stdout)
        self.assertIn("- MVP scope: MISSING", result.stdout)
        self.assertIn("- build command: MISSING", result.stdout)
        self.assertIn("Blocked on:", result.stdout)
        self.assertIn("./scripts/lab handoff --idea-id idea-doctor-blocked --check", result.stdout)
        self.assertIn("update the active idea/session or state/project-init.json", result.stdout)

    def test_lab_doctor_reports_sources_for_ready_target(self) -> None:
        self.write_finalize_fixture("idea-doctor-ready")
        result = run_cmd(["./scripts/lab", "doctor"], cwd=self.repo)
        self.assertIn("Finalize target: idea-doctor-ready (from canonical state)", result.stdout)
        self.assertIn("Finalize readiness: ready", result.stdout)
        self.assertIn("- problem statement: OK via state.product.problemStatement", result.stdout)
        self.assertIn("- build command: OK via state.commands.build", result.stdout)
        self.assertIn("- top risks: OK via state.governance.topRisks", result.stdout)
        self.assertIn("Next step: finalize can run now with ./scripts/finalize-project --idea-id idea-doctor-ready", result.stdout)

    def test_lab_commit_and_push_wrappers(self) -> None:
        self.init_git_repo()
        remote_path = self.tmpdir / "remote.git"
        run_cmd(["git", "init", "--bare", str(remote_path)], cwd=self.repo)
        run_cmd(["git", "remote", "add", "origin", str(remote_path)], cwd=self.repo)
        readme = self.repo / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nworkflow test\n", encoding="utf-8")
        run_cmd(
            ["./scripts/lab", "commit", "--message", "brainstorm: wrapper commit test"],
            cwd=self.repo,
        )
        run_cmd(["./scripts/lab", "push"], cwd=self.repo)
        remote_head = run_cmd(
            ["git", "--git-dir", str(remote_path), "rev-parse", "refs/heads/main"],
            cwd=self.repo,
        )
        self.assertTrue(remote_head.stdout.strip())

    def test_lab_decide_appends_to_last_matching_session_section(self) -> None:
        self.write_finalize_fixture("idea-duplicate-decisions")
        session_path = self.repo / "sessions/2026-04-03_idea-duplicate-decisions.md"
        session_path.write_text(
            textwrap.dedent(
                """\
                # Brainstorming Session

                ## Metadata

                - Date: 2026-04-03
                - Idea ID: `idea-duplicate-decisions`
                - Title: Finalize Smoke
                - Owner: Test User
                - Status: active

                ## Risks

                - Existing risk note.

                ## Decisions

                - Historical decision placeholder.

                ## Exploration Path Notes

                - Explored a first approach.

                ## Decisions

                - Current decision log lives here.

                ## Review Gates
                """
            ),
            encoding="utf-8",
        )

        run_cmd(
            [
                "./scripts/lab",
                "decide",
                "--idea-id",
                "idea-duplicate-decisions",
                "--chosen-option",
                "Append to the latest canonical decision section",
                "--rationale",
                "Keep hand-edited session ordering intact",
                "--no-sync",
            ],
            cwd=self.repo,
        )

        content = session_path.read_text(encoding="utf-8")
        decision_sections = content.split("## Decisions")
        self.assertEqual(len(decision_sections), 3)
        self.assertNotIn("Decision ID: decision-001", decision_sections[1])
        self.assertIn("Decision ID: decision-001", decision_sections[2])
        self.assertIn("## Review Gates", decision_sections[2])

    def test_lab_review_preserves_noncanonical_idea_bullets(self) -> None:
        self.write_finalize_fixture("idea-weird-bullets")
        (self.repo / "ideas/_active.md").write_text(
            textwrap.dedent(
                """\
                # Active Ideas

                ---

                ## Idea: Weird Bullets

                ## Metadata

                  - Idea ID: `idea-weird-bullets`
                  * Codename (kebab case): weird-bullets
                  - Title: Weird Bullets
                  - Date: 2026-04-03
                  - Owner: Test User
                  - Status: active
                  - Sensitivity: Internal

                ## Problem Definition

                  * Problem statement: Preserve important values during rewrites.
                  - Affected users/personas: Template maintainers
                  - Why now: Hand-edited markdown should stay durable.
                  - Current alternatives: Manually fix dropped fields

                ## Hypotheses

                  - Value hypothesis: More resilient markdown mutation reduces maintenance churn.
                  - Adoption hypothesis:
                  - Feasibility hypothesis:

                ## Proposed Scope

                  - MVP scope: Tolerate mild formatting drift.
                  - Out of scope: Arbitrary markdown parsing.
                  * Assumptions: Core headings still exist.
                  - Constraints: Preserve markdown readability.

                ## Governance Rationale

                  - Why this idea should be pursued: Avoid silent data loss.
                  - Strategic alignment: Improve template reliability.
                  * Non-goals: Enforce one exact bullet style.

                ## Risks and Unknowns

                  - Top risks (link to risk entries): Regex-only rewrites can drop fields.
                  - Open questions:
                  - Dependency concerns:

                ## Decisions and ADR Links

                  - Related decisions:
                  - Related ADRs (`docs/adr/ADR-XXXX-*.md`):

                ## Validation Plan

                  - Evidence needed: Regression coverage for hand-edited markdown.
                  - Test plan: Add session and idea rewrite tests.
                  - Success criteria: Key fields survive rewrites.
                  - Failure criteria: Rewrites blank existing fields.

                ## Review and Export Readiness

                  - Latest review outcome: conditional-pass
                  - Conditions to finalize:
                  - Optional summary export path:

                ## Traceability

                  - Session links: `sessions/2026-04-03_idea-weird-bullets.md`
                  - Catalog reference: `IDEA_CATALOG.md`
                """
            ),
            encoding="utf-8",
        )

        run_cmd(
            [
                "./scripts/lab",
                "review",
                "--idea-id",
                "idea-weird-bullets",
                "--result",
                "pass",
                "--summary",
                "Core fields survived the rewrite path",
                "--outcome",
                "revise",
                "--next-action",
                "Finalize after test coverage lands",
                "--no-sync",
            ],
            cwd=self.repo,
        )

        updated_idea = (self.repo / "ideas/_active.md").read_text(encoding="utf-8")
        self.assertIn("- Problem statement: Preserve important values during rewrites.", updated_idea)
        self.assertIn("- Constraints: Preserve markdown readability.", updated_idea)
        self.assertIn("- Non-goals: Enforce one exact bullet style.", updated_idea)
        self.assertIn("- Latest review outcome: pass", updated_idea)

if __name__ == "__main__":
    import unittest

    unittest.main()
