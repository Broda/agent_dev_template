from __future__ import annotations

import json
import textwrap

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class FinalizationRegressionTests(LabWorkflowTestCase):
    def test_finalize_carries_multi_session_decisions_into_development_outputs(self) -> None:
        idea_id = "idea-quote-heavy-multisession"
        session_one = f"sessions/2026-04-03_{idea_id}.md"
        session_two = f"sessions/2026-04-04_{idea_id}_review.md"
        custom_adr = "docs/adr/ADR-0099-client-path-preservation.md"
        project_name = 'Quote "Heavy" Scheduler & Planner'
        purpose = 'Preserve "yes, later" commitments across calendars and source paths with spaces.'
        key_decisions = (
            'Adopt "state-first" finalization; split Review Queue UI from Commitment Engine; '
            'store "client docs/final plan.md" source paths literally.'
        )
        top_risks = (
            'Quoted commands or paths with spaces may break render/finalize, especially "tests/integration cases".'
        )
        mitigation = "Use structured JSON, deterministic renderers, and smoke assertions across multiple sessions."
        contingency = "Keep literal command blocks in generated docs if parser support regresses."

        self._write_rich_brainstorming_state(
            idea_id,
            project_name,
            purpose,
            key_decisions,
            top_risks,
            mitigation,
            contingency,
            session_one,
            session_two,
            custom_adr,
        )
        result = run_cmd(
            ["./scripts/lab", "finalize", "--idea-id", idea_id, "--write-export"],
            cwd=self.repo,
            input_text="\n" * 12,
        )

        self.assertIn("successfully finalized", result.stdout.lower())
        finalized_state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        artifacts = finalized_state["artifacts"]
        archived_session_one = f".harness/history/{session_one}"
        archived_session_two = f".harness/history/{session_two}"
        self.assertIn(archived_session_one, artifacts["sessionFiles"])
        self.assertIn(archived_session_two, artifacts["sessionFiles"])
        self.assertTrue(any("FINALIZATION_SESSION" in value for value in artifacts["sessionFiles"]))
        self.assertIn(custom_adr, artifacts["adrReferences"])
        self.assertIn("docs/adr/ADR-0001-record-architecture-decisions.md", artifacts["adrReferences"])

        summary_export = self.repo / artifacts["summaryExport"]
        self.assertTrue(summary_export.is_file())
        outputs = {
            "README": (self.repo / "README.md").read_text(encoding="utf-8"),
            "PROJECT_CONTEXT": (self.repo / "docs/PROJECT_CONTEXT.md").read_text(encoding="utf-8"),
            "ARCHITECTURE": (self.repo / "docs/ARCHITECTURE.md").read_text(encoding="utf-8"),
            "ROADMAP": (self.repo / "docs/ROADMAP.md").read_text(encoding="utf-8"),
            "ADR": (self.repo / "docs/adr/ADR-0001-record-architecture-decisions.md").read_text(encoding="utf-8"),
            "EXPORT": summary_export.read_text(encoding="utf-8"),
            "CI": (self.repo / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        }
        for label, content in outputs.items():
            if label == "CI":
                continue
            self.assertIn(project_name, content)
        self.assertIn(purpose, outputs["README"])
        self.assertIn('python3 -m pytest "tests/integration cases" -k "happy path"', outputs["README"])
        self.assertFalse(any(term in outputs["README"] for term in ["# Research Notes", "# Philosophy"]))
        self.assertIn(key_decisions, outputs["PROJECT_CONTEXT"])
        self.assertIn(mitigation, outputs["PROJECT_CONTEXT"])
        self.assertIn(contingency, outputs["PROJECT_CONTEXT"])
        self.assertIn("conditional-pass", outputs["PROJECT_CONTEXT"])
        self.assertIn('"client docs/final plan.md"', outputs["ARCHITECTURE"])
        self.assertIn("Initial implementation must preserve structured MVP contract details.", outputs["ARCHITECTURE"])
        self.assertIn("quote-scheduler-core", outputs["ROADMAP"])
        self.assertIn(top_risks, outputs["ROADMAP"])
        self.assertIn(key_decisions, outputs["ADR"])
        self.assertIn(top_risks, outputs["ADR"])
        self.assertIn(mitigation, outputs["ADR"])
        self.assertIn(contingency, outputs["ADR"])
        self.assertIn(archived_session_one, outputs["ADR"])
        self.assertIn(archived_session_two, outputs["ADR"])
        self.assertIn(key_decisions, outputs["EXPORT"])
        self.assertIn(custom_adr, outputs["EXPORT"])
        self.assertNotIn("python3 -m unittest discover -s .harness/tests -v", outputs["CI"])
        self.assertIn('pnpm build && python3 -m py_compile "src/app/main.py"', outputs["CI"])
        self.assertIn('python3 -m pytest "tests/integration cases" -k "happy path"', outputs["CI"])
        self.assertIn("./scripts/validate-governance", outputs["CI"])
        self.assertIn("./scripts/validate-development", outputs["CI"])
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def _write_rich_brainstorming_state(
        self,
        idea_id: str,
        project_name: str,
        purpose: str,
        key_decisions: str,
        top_risks: str,
        mitigation: str,
        contingency: str,
        session_one: str,
        session_two: str,
        custom_adr: str,
    ) -> None:
        (self.repo / "sessions").mkdir(parents=True, exist_ok=True)
        (self.repo / "docs/adr").mkdir(parents=True, exist_ok=True)
        (self.repo / custom_adr).write_text(
            '# ADR 0099\n\nPreserve source paths such as "client docs/final plan.md" exactly.\n',
            encoding="utf-8",
        )
        (self.repo / "ideas/_active.md").write_text(
            self._active_idea(idea_id, project_name, key_decisions, top_risks, session_one, session_two, custom_adr),
            encoding="utf-8",
        )
        (self.repo / session_one).write_text(
            self._session_one(idea_id, project_name, top_risks, mitigation, contingency),
            encoding="utf-8",
        )
        (self.repo / session_two).write_text(
            self._session_two(idea_id, project_name),
            encoding="utf-8",
        )
        (self.repo / "IDEA_CATALOG.md").write_text(
            self._catalog(idea_id, project_name, session_one, session_two),
            encoding="utf-8",
        )
        state = self._state(
            idea_id,
            project_name,
            purpose,
            key_decisions,
            top_risks,
            mitigation,
            contingency,
            session_one,
            session_two,
            custom_adr,
        )
        (self.repo / "state/project-init.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def _active_idea(
        self,
        idea_id: str,
        project_name: str,
        key_decisions: str,
        top_risks: str,
        session_one: str,
        session_two: str,
        custom_adr: str,
    ) -> str:
        return textwrap.dedent(
            f"""\
            # Active Ideas

            ---

            ## Idea: {project_name}

            ## Metadata

            - Idea ID: `{idea_id}`
            - Codename (kebab case): quote-heavy-multisession
            - Title: {project_name}
            - Date: 2026-04-03
            - Owner: Test User
            - Status: active
            - Sensitivity: Internal

            ## Problem Definition

            - Problem statement: Teams say "yes, later" but lose follow-ups across calendars and quoted task names.
            - Affected users/personas: Operations leads, project managers, and agents coordinating "follow up next week" work.
            - Why now: Agent-assisted planning produces more generated handoff text that must preserve exact commitments.

            ## Proposed Scope

            - MVP scope: Capture commitments, normalize dates, render a deterministic review queue, and export handoff packets.
            - Out of scope: Enterprise SSO, billing, and external calendar write-back.
            - Assumptions: Users can paste source notes; SQLite is enough for the local-first MVP.
            - Constraints: Preserve quotes, ampersands, and paths with spaces like "client docs/final plan.md".

            ## Risks and Unknowns

            - Top risks (link to risk entries): {top_risks}

            ## Decisions and ADR Links

            - Related decisions: {key_decisions}
            - Related ADRs (`docs/adr/ADR-XXXX-*.md`): `{custom_adr}`

            ## Review and Export Readiness

            - Latest review outcome: conditional-pass

            ## Traceability

            - Session links: `{session_one}`, `{session_two}`
            - Catalog reference: `IDEA_CATALOG.md`
            """
        )

    def _session_one(
        self,
        idea_id: str,
        project_name: str,
        top_risks: str,
        mitigation: str,
        contingency: str,
    ) -> str:
        return textwrap.dedent(
            f"""\
            # Brainstorming Session

            ## Metadata

            - Date: 2026-04-03
            - Idea ID: `{idea_id}`
            - Title: {project_name}
            - Owner: Test User
            - Status: active

            ## Decisions

            - Decision ID: DEC-001
            - Chosen option: Split Review Queue UI from Commitment Engine.
            - Rationale: Keeps interface changes from rewriting deterministic commitment rules.

            ## Risks

            - Risk statement: {top_risks}
            - Preventive mitigation: {mitigation}
            - Contingency plan: {contingency}
            """
        )

    def _session_two(self, idea_id: str, project_name: str) -> str:
        return textwrap.dedent(
            f"""\
            # Brainstorming Session

            ## Metadata

            - Date: 2026-04-04
            - Idea ID: `{idea_id}`
            - Title: {project_name}
            - Owner: Test User
            - Status: active

            ## Decisions

            - Decision ID: DEC-002
            - Chosen option: Store "client docs/final plan.md" source paths literally.
            - Rationale: Exact path preservation keeps generated handoffs auditable.

            ## Review Gates

            - Result: conditional-pass
            - Summary: Ready if decisions, risks, commands, and both sessions reach development docs and ADRs.
            """
        )

    def _catalog(self, idea_id: str, project_name: str, session_one: str, session_two: str) -> str:
        return textwrap.dedent(
            f"""\
            # Idea Catalog

            ## Registry

            | Idea ID | Title | Status | Owner | Sessions | Summary Export | Notes |
            |---|---|---|---|---|---|---|
            | {idea_id} | {project_name} | active | Test User | `{session_one}`, `{session_two}` | _n/a_ | _none_ |
            """
        )

    def _state(
        self,
        idea_id: str,
        project_name: str,
        purpose: str,
        key_decisions: str,
        top_risks: str,
        mitigation: str,
        contingency: str,
        session_one: str,
        session_two: str,
        custom_adr: str,
    ) -> dict:
        return {
            "schemaVersion": 2,
            "status": "draft",
            "finalizedAt": "",
            "ideaId": idea_id,
            "projectName": project_name,
            "owner": "Test User",
            "purpose": purpose,
            "projectType": "Web App",
            "techStack": {
                "language": "Python + TypeScript",
                "runtime": "Python 3.12 / Node 22",
                "framework": "FastAPI + React",
                "packageTool": "uv + pnpm",
            },
            "persistence": "SQLite",
            "authentication": "Local users",
            "determinism": 'High - stable ordering for "quoted" commitment exports.',
            "packaging": "Container image later; local dev first.",
            "constraints": 'Preserve quotes, ampersands, and paths with spaces like "client docs/final plan.md".',
            "commands": {
                "build": 'pnpm build && python3 -m py_compile "src/app/main.py"',
                "run": 'python3 -m uvicorn "quote_scheduler.main:app" --reload',
                "test": 'python3 -m pytest "tests/integration cases" -k "happy path"',
            },
            "product": {
                "problemStatement": 'Teams say "yes, later" but commitments disappear across calendars.',
                "targetUsers": 'Operations leads and agents coordinating "follow up next week" work.',
                "whyNow": "Agent-assisted planning produces more generated handoff text.",
                "expectedValue": "A deterministic review queue that keeps wording intact.",
                "solutionSummary": "Capture commitments, normalize dates, render a deterministic review queue.",
                "mvpScope": "Capture commitments, support SQLite persistence, and export Markdown handoff packets.",
                "outOfScope": "Enterprise SSO, billing, and external calendar write-back.",
                "assumptions": "Users can paste source notes; SQLite is enough for a local-first MVP.",
                "nonGoals": "Do not silently rewrite user-provided quoted text.",
            },
            "governance": {
                "keyDecisions": key_decisions,
                "topRisks": top_risks,
                "mitigationPlans": mitigation,
                "contingencies": contingency,
                "remainingAcceptedRisks": "External calendar integrations remain undefined.",
                "latestReviewOutcome": "conditional-pass",
                "latestReviewSession": session_two,
            },
            "artifacts": {
                "ideaFiles": ["ideas/_active.md"],
                "sessionFiles": [session_one, session_two],
                "noteReferences": 'notes/2026-04-04_quote-heavy "review".md',
                "summaryExport": "",
                "finalizationSession": "",
                "adrReferences": [custom_adr],
            },
            "implementation": {
                "workspaceLayout": ["quote-scheduler-core", "quote-scheduler-web"],
                "storageImplementation": ["Initial implementation must preserve structured MVP contract details."],
            },
        }
