from __future__ import annotations

import textwrap

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


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
