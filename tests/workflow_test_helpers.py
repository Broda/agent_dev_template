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
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
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


class LabWorkflowTestCase(unittest.TestCase):
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
        summary_export = fixture_state.get("artifacts", {}).get("summaryExport", "")
        if summary_export:
            summary_export_path = self.repo / summary_export
            summary_export_path.parent.mkdir(parents=True, exist_ok=True)
            summary_export_path.write_text(
                f"# Summary Export\n\n- Idea ID: `{idea_id}`\n- Title: {project_name}\n",
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
