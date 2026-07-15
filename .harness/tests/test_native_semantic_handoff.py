from __future__ import annotations

import json

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class NativeSemanticHandoffTests(LabWorkflowTestCase):
    def test_native_lab_records_compile_and_survive_finalization(self) -> None:
        idea_id = "idea-native-contract"
        self.write_finalize_fixture(idea_id)
        session = f"sessions/2026-04-03_{idea_id}.md"
        for command in self._native_record_commands(idea_id, session):
            run_cmd(command, cwd=self.repo)

        catalog = (self.repo / "IDEA_CATALOG.md").read_text(encoding="utf-8")
        self.assertIn(f"| {idea_id} | Finalize Smoke | active | Test User |", catalog)
        self.assertIn("| _none_ |", catalog)

        check = run_cmd(["./scripts/lab", "handoff", "--idea-id", idea_id, "--check"], cwd=self.repo)
        for section in [
            "Native Brainstorming Decisions",
            "Native Brainstorming Risks",
            "Related Brainstorming Notes",
        ]:
            self.assertIn(section, check.stdout)

        run_cmd(["./scripts/lab", "handoff", "--idea-id", idea_id, "--no-sync"], cwd=self.repo)
        draft = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        contract = draft["brainstormingContract"]
        self.assertEqual(["decision-0041", "decision-0042"], [item["id"] for item in contract["decisions"]])
        self.assertEqual(
            ["Preserve caller-provided identifiers exactly.", "Do not depend on wall-clock ordering."],
            [item["constraints"] for item in contract["decisions"]],
        )
        self.assertEqual("risk-0017", contract["risks"][0]["id"])
        self.assertEqual("note-0001", contract["relatedNotes"][0]["id"])
        self.assertIn("notes/", draft["artifacts"]["noteReferences"])

        run_cmd(["./scripts/finalize-project", "--idea-id", idea_id], cwd=self.repo)
        state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        self.assertEqual(2, len(state["brainstormingContract"]["decisions"]))
        self.assertTrue(state["brainstormingContract"]["relatedNotes"][0]["path"].startswith(".harness/history/notes/"))
        self.assertIn("Cross-template handoff.", state["finalizedContract"]["deferredScope"])

        docs = "\n".join(
            (self.repo / path).read_text(encoding="utf-8")
            for path in [
                "docs/PROJECT_CONTEXT.md",
                "docs/ARCHITECTURE.md",
                "docs/ROADMAP.md",
                "docs/adr/ADR-0001-record-architecture-decisions.md",
            ]
        )
        for expected in [
            "Use an append-only canonical event stream.",
            "Append-only events preserve auditability.",
            "Do not depend on wall-clock ordering.",
            "A partial write could leave replay state inconsistent.",
            "Commit each event and sequence update atomically.",
            "Rebuild projections from the last verified sequence.",
            ".harness/history/notes/",
            "Cross-template handoff.",
        ]:
            self.assertIn(expected, docs)
        self.assertNotRegex(docs, r"Deferred scope:\s*\n\s*- None recorded\.")

    def test_handoff_blocks_incomplete_native_decision_with_guidance(self) -> None:
        idea_id = "idea-incomplete-native-contract"
        self.write_finalize_fixture(idea_id)
        state_before = (self.repo / "state/project-init.json").read_text(encoding="utf-8")
        run_cmd(
            [
                "./scripts/lab",
                "decide",
                "--idea-id",
                idea_id,
                "--decision-id",
                "decision-0099",
                "--session",
                f"sessions/2026-04-03_{idea_id}.md",
                "--chosen-option",
                "Keep the native record.",
                "--no-sync",
            ],
            cwd=self.repo,
        )

        result = run_cmd(
            ["./scripts/lab", "handoff", "--idea-id", idea_id, "--check"],
            cwd=self.repo,
            check=False,
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("Decision decision-0099 is missing: Rationale.", result.stdout)
        self.assertIn(f"./scripts/lab handoff --idea-id {idea_id} --check", result.stdout)
        self.assertEqual(state_before, (self.repo / "state/project-init.json").read_text(encoding="utf-8"))

    def test_finalization_blocks_incomplete_native_risk_without_prior_handoff(self) -> None:
        idea_id = "idea-incomplete-native-risk"
        self.write_finalize_fixture(idea_id)
        run_cmd(
            [
                "./scripts/lab",
                "risk",
                "--idea-id",
                idea_id,
                "--risk-id",
                "risk-0088",
                "--session",
                f"sessions/2026-04-03_{idea_id}.md",
                "--statement",
                "Recovery semantics are undefined.",
                "--no-sync",
            ],
            cwd=self.repo,
        )

        result = run_cmd(
            ["./scripts/finalize-project", "--idea-id", idea_id],
            cwd=self.repo,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("Risk risk-0088 is missing: Preventive mitigation, Contingency plan.", result.stderr)
        self.assertIn("Current mode: brainstorming", (self.repo / "MODE.md").read_text(encoding="utf-8"))

    @staticmethod
    def _native_record_commands(idea_id: str, session: str) -> list[list[str]]:
        return [
            [
                "./scripts/lab",
                "decide",
                "--idea-id",
                idea_id,
                "--decision-id",
                "decision-0041",
                "--session",
                session,
                "--situation",
                "The import boundary must remain deterministic.",
                "--constraints",
                "Preserve caller-provided identifiers exactly.",
                "--chosen-option",
                "Use an append-only canonical event stream.",
                "--rationale",
                "Append-only events preserve auditability.",
                "--no-sync",
            ],
            [
                "./scripts/lab",
                "decide",
                "--idea-id",
                idea_id,
                "--decision-id",
                "decision-0042",
                "--session",
                session,
                "--situation",
                "Consumers need stable replay behavior.",
                "--constraints",
                "Do not depend on wall-clock ordering.",
                "--chosen-option",
                "Sort replay by canonical sequence number.",
                "--rationale",
                "Sequence numbers make replay reproducible.",
                "--no-sync",
            ],
            [
                "./scripts/lab",
                "risk",
                "--idea-id",
                idea_id,
                "--risk-id",
                "risk-0017",
                "--session",
                session,
                "--statement",
                "A partial write could leave replay state inconsistent.",
                "--mitigation",
                "Commit each event and sequence update atomically.",
                "--contingency",
                "Rebuild projections from the last verified sequence.",
                "--probability",
                "low",
                "--impact",
                "high",
                "--no-sync",
            ],
            [
                "./scripts/lab",
                "note",
                "--idea-id",
                idea_id,
                "--topic",
                "Replay ordering evidence",
                "--source",
                "architecture review",
                "--fact",
                "Sequence ordering is independent of wall-clock precision.",
                "--tags",
                "replay,ordering",
                "--no-sync",
            ],
        ]
