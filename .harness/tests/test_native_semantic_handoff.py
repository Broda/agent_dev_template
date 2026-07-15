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
            "Native Brainstorming Session Context",
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
        self.assertEqual(
            ["The workflow enforces a five-hour exam clock.", "Citations use Chicago Author-Date."],
            contract["relatedNotes"][0]["capturedInformation"],
        )
        self.assertEqual(
            ["The first SMARTCASE score is retained.", "Records use stable UUIDs."],
            contract["relatedNotes"][0]["keyFacts"],
        )
        self.assertEqual(
            ["Should updated_at change during replay?"],
            contract["relatedNotes"][0]["openQuestions"],
        )
        self.assertEqual(["https://example.test/semantic-contract"], contract["relatedNotes"][0]["links"])
        session_items = [item for section_record in contract["sessionSections"] for item in section_record["items"]]
        self.assertIn("Preserve continuity through finalize.", session_items)
        self.assertIn("Keep the share-target route explicit.", session_items)
        self.assertIn("notes/", draft["artifacts"]["noteReferences"])

        run_cmd(["./scripts/finalize-project", "--idea-id", idea_id], cwd=self.repo)
        state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        self.assertEqual(2, len(state["brainstormingContract"]["decisions"]))
        self.assertTrue(state["brainstormingContract"]["relatedNotes"][0]["path"].startswith(".harness/history/notes/"))
        self.assertTrue(
            all(
                record["source"].startswith(".harness/history/sessions/")
                for record in state["brainstormingContract"]["sessionSections"]
            )
        )
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
            "five-hour exam clock",
            "Chicago Author-Date",
            "first SMARTCASE score",
            "stable UUIDs",
            "updated_at",
            "https://example.test/semantic-contract",
            "Preserve continuity through finalize.",
            "share-target route",
            ".harness/history/notes/",
            ".harness/history/sessions/",
            "Cross-template handoff.",
        ]:
            self.assertIn(expected, docs)
        self.assertNotRegex(docs, r"Deferred scope:\s*\n\s*- None recorded\.")

    def test_validation_detects_omitted_compiled_note_semantics(self) -> None:
        idea_id = "idea-native-contract-omission"
        self.write_finalize_fixture(idea_id)
        session = f"sessions/2026-04-03_{idea_id}.md"
        for command in self._native_record_commands(idea_id, session):
            run_cmd(command, cwd=self.repo)
        run_cmd(["./scripts/finalize-project", "--idea-id", idea_id], cwd=self.repo)

        omitted = "Records use stable UUIDs."
        for relative_path in [
            "docs/ARCHITECTURE.md",
            "docs/ROADMAP.md",
            "docs/adr/ADR-0001-record-architecture-decisions.md",
        ]:
            path = self.repo / relative_path
            path.write_text(path.read_text(encoding="utf-8").replace(omitted, "[omitted]"), encoding="utf-8")

        result = run_cmd(["./scripts/validate-development"], cwd=self.repo, check=False)

        self.assertNotEqual(0, result.returncode)
        self.assertIn(
            f"Generated development docs are missing compiled related note key fact / constraint: {omitted}",
            result.stdout,
        )

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
                "path-note",
                "--idea-id",
                idea_id,
                "--title",
                "Route boundary exploration",
                "--summary",
                "Keep the share-target route explicit.",
                "--session",
                session,
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
                "--summary",
                "The workflow enforces a five-hour exam clock.",
                "--detail",
                "Citations use Chicago Author-Date.",
                "--fact",
                "The first SMARTCASE score is retained.",
                "--fact",
                "Records use stable UUIDs.",
                "--question",
                "Should updated_at change during replay?",
                "--link",
                "https://example.test/semantic-contract",
                "--tags",
                "replay,ordering",
                "--no-sync",
            ],
        ]
