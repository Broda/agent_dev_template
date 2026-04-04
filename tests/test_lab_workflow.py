from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(
    args: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


class LabWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="codex-template-tests."))
        self.repo = self.tmpdir / "repo"
        shutil.copytree(
            REPO_ROOT,
            self.repo,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def init_git_repo(self) -> None:
        run_cmd(["git", "init", "-b", "main"], cwd=self.repo)
        run_cmd(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run_cmd(["git", "config", "user.email", "test@example.com"], cwd=self.repo)
        run_cmd(["git", "add", "-A"], cwd=self.repo)
        run_cmd(["git", "commit", "-m", "baseline"], cwd=self.repo)

    def write_render_fixture(self, state_fixture: str = "finalized_state_v2.json") -> None:
        fixture_dir = REPO_ROOT / "tests/fixtures"
        fixture_state = json.loads((fixture_dir / state_fixture).read_text(encoding="utf-8"))
        idea_id = fixture_state["ideaId"]
        project_name = fixture_state["projectName"]
        (self.repo / "sessions").mkdir(parents=True, exist_ok=True)
        session_template = (fixture_dir / "finalized_session.md").read_text(encoding="utf-8")
        session_text = (
            session_template.replace("idea-render-fixture", idea_id)
            .replace("Render Fixture", project_name)
        )
        (self.repo / f"sessions/2026-04-03_{idea_id}.md").write_text(session_text, encoding="utf-8")
        (self.repo / f"sessions/2026-04-03_FINALIZATION_SESSION_{idea_id}.md").write_text(
            session_text,
            encoding="utf-8",
        )
        (self.repo / "state/project-init.json").write_text(
            json.dumps(fixture_state, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.repo / "MODE.md").write_text(
            textwrap.dedent(
                """\
                # Repository Mode

                Current mode: development

                Allowed values:

                - brainstorming
                - development

                Switch modes with `./scripts/finalize-project`.
                """
            ),
            encoding="utf-8",
        )

    def write_finalize_fixture(self, idea_id: str = "idea-finalize-smoke") -> None:
        (self.repo / "sessions").mkdir(parents=True, exist_ok=True)
        (self.repo / "exports").mkdir(parents=True, exist_ok=True)
        (self.repo / "ideas/_active.md").write_text(
            textwrap.dedent(
                f"""\
                # Active Ideas

                ---

                ## Idea: Finalize Smoke

                ## Metadata

                - Idea ID: `{idea_id}`
                - Codename (kebab case): finalize-smoke
                - Title: Finalize Smoke
                - Date: 2026-04-03
                - Owner: Test User
                - Status: active
                - Sensitivity: Internal

                ## Problem Definition

                - Problem statement: Keep transitions lossless.
                - Affected users/personas: Template maintainers
                - Why now: Finalize is in place now.
                - Current alternatives: Manual copy/paste

                ## Hypotheses

                - Value hypothesis: State-first finalization reduces drift.
                - Adoption hypothesis:
                - Feasibility hypothesis:

                ## Proposed Scope

                - MVP scope: Record canonical state and switch modes.
                - Out of scope: Cross-template handoff.
                - Assumptions: One repo owns the full lifecycle.
                - Constraints: Preserve markdown readability.

                ## Governance Rationale

                - Why this idea should be pursued: Eliminate transition loss.
                - Strategic alignment:
                - Non-goals: Reintroducing export-first workflows.

                ## Risks and Unknowns

                - Top risks (link to risk entries): Docs/runtime drift.
                - Open questions:
                - Dependency concerns:

                ## Decisions and ADR Links

                - Related decisions:
                - Related ADRs (`docs/adr/ADR-XXXX-*.md`):

                ## Validation Plan

                - Evidence needed:
                - Test plan:
                - Success criteria:
                - Failure criteria:

                ## Review and Export Readiness

                - Latest review outcome: conditional-pass
                - Conditions to finalize:
                - Optional summary export path:

                ## Traceability

                - Session links: `sessions/2026-04-03_{idea_id}.md`
                - Catalog reference: `IDEA_CATALOG.md`
                """
            ),
            encoding="utf-8",
        )
        (self.repo / f"sessions/2026-04-03_{idea_id}.md").write_text(
            textwrap.dedent(
                f"""\
                # Brainstorming Session

                ## Metadata

                - Date: 2026-04-03
                - Idea ID: `{idea_id}`
                - Title: Finalize Smoke
                - Owner: Test User
                - Status: active

                ## Current Focus

                - Preserve continuity through finalize.

                ## Exploration Path Notes

                ## Decisions

                ## Risks

                ## Review Gates
                """
            ),
            encoding="utf-8",
        )
        (self.repo / "IDEA_CATALOG.md").write_text(
            textwrap.dedent(
                f"""\
                # Idea Catalog

                Central index of tracked ideas.

                ## Rules

                - Each idea ID appears once.
                - Status must be one of: `inbox`, `active`, `parked`, `killed`, `finalized`.
                - Finalized ideas may include an optional summary export path.

                ## Registry

                | Idea ID | Title | Status | Owner | Sessions | Summary Export | Notes |
                |---|---|---|---|---|---|---|
                | {idea_id} | Finalize Smoke | active | Test User | `sessions/2026-04-03_{idea_id}.md` | _n/a_ | _none_ |
                """
            ),
            encoding="utf-8",
        )
        (self.repo / "state/project-init.json").write_text(
            textwrap.dedent(
                f"""\
                {{
                  "schemaVersion": 2,
                  "status": "draft",
                  "finalizedAt": "",
                  "ideaId": "{idea_id}",
                  "projectName": "Finalize Smoke",
                  "owner": "Test User",
                  "purpose": "Keep transitions lossless.",
                  "projectType": "CLI",
                  "techStack": {{
                    "language": "Python",
                    "runtime": "Python 3.12",
                    "framework": "None",
                    "packageTool": "None"
                  }},
                  "persistence": "None",
                  "authentication": "None",
                  "determinism": "High",
                  "packaging": "None",
                  "constraints": "Preserve markdown readability",
                  "commands": {{
                    "build": "python3 -m py_compile scripts/python/cli.py scripts/python/template_cli/*.py",
                    "run": "./scripts/validate-governance",
                    "test": "./scripts/validate-brainstorming"
                  }},
                  "product": {{
                    "problemStatement": "Keep transitions lossless.",
                    "targetUsers": "Template maintainers",
                    "whyNow": "Finalize is in place now.",
                    "expectedValue": "No decision loss during mode switch.",
                    "solutionSummary": "Use canonical state and session history as the transition source of truth.",
                    "mvpScope": "Capture canonical state and switch modes.",
                    "outOfScope": "Cross-template handoff.",
                    "assumptions": "One repo owns the full lifecycle.",
                    "nonGoals": "Reintroducing export-first workflows."
                  }},
                  "governance": {{
                    "keyDecisions": "State-first finalization.",
                    "topRisks": "Docs/runtime drift.",
                    "mitigationPlans": "Render from state and validate.",
                    "contingencies": "Fallback to session history.",
                    "remainingAcceptedRisks": "Some docs may need polishing.",
                    "latestReviewOutcome": "conditional-pass",
                    "latestReviewSession": "sessions/2026-04-03_{idea_id}.md"
                  }},
                  "artifacts": {{
                    "ideaFiles": ["ideas/_active.md"],
                    "sessionFiles": ["sessions/2026-04-03_{idea_id}.md"],
                    "noteReferences": "None recorded",
                    "summaryExport": "",
                    "finalizationSession": "",
                    "adrReferences": ["brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md"]
                  }}
                }}
                """
            ),
            encoding="utf-8",
        )

    def test_validate_brainstorming_clean_template(self) -> None:
        run_cmd(["./scripts/validate-brainstorming"], cwd=self.repo)

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

    def test_lab_finalize_wrapper_records_session_and_switches_mode(self) -> None:
        self.write_finalize_fixture()
        result = run_cmd(
            ["./scripts/lab", "finalize", "--idea-id", "idea-finalize-smoke", "--write-export"],
            cwd=self.repo,
            input_text="\n" * 12,
        )
        self.assertIn("successfully finalized", result.stdout.lower())
        self.assertIn("Current mode: development", (self.repo / "MODE.md").read_text(encoding="utf-8"))
        sessions = sorted((self.repo / "sessions").glob("*FINALIZATION_SESSION*.md"))
        self.assertTrue(sessions)
        exports = sorted((self.repo / "exports").glob("*PROJECT_SUMMARY*.md"))
        self.assertTrue(exports)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_lab_finalize_requires_explicit_choice_when_multiple_ideas_active(self) -> None:
        self.write_finalize_fixture("idea-first")
        state_path = self.repo / "state/project-init.json"
        state_text = state_path.read_text(encoding="utf-8").replace('"ideaId": "idea-first"', '"ideaId": ""')
        state_path.write_text(state_text, encoding="utf-8")
        catalog_path = self.repo / "IDEA_CATALOG.md"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8")
            + "| idea-second | Second Idea | active | Test User | `sessions/2026-04-03_idea-second.md` | _n/a_ | _none_ |\n",
            encoding="utf-8",
        )
        (self.repo / "sessions/2026-04-03_idea-second.md").write_text(
            "# Brainstorming Session\n\n- Idea ID: `idea-second`\n",
            encoding="utf-8",
        )
        result = run_cmd(["./scripts/lab", "finalize"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("select idea to finalize", result.stderr.lower() + result.stdout.lower())

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
        self.assertIn("update the active idea/session or prefill state/project-init.json", result.stdout)

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
    unittest.main()
