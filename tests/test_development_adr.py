from __future__ import annotations

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentAdrTests(LabWorkflowTestCase):
    def test_lab_adr_creates_next_sequential_adr_in_development_mode(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        result = run_cmd(
            [
                "./scripts/lab",
                "adr",
                "--title",
                'Adopt "Agent Harness" command routing / defaults',
                "--context",
                "Agents need a durable way to record implementation decisions.",
                "--decision",
                "Use deterministic development-mode ADR capture.",
                "--consequence",
                "Decision history stays in docs/adr instead of chat only.",
                "--alternative",
                "Rely on free-form notes.",
                "--deciders",
                "Template maintainer",
                "--date",
                "2026-05-05",
            ],
            cwd=self.repo,
        )

        expected_path = self.repo / "docs/adr/ADR-0003-adopt-agent-harness-command-routing-defaults.md"
        self.assertTrue(expected_path.exists())
        adr = expected_path.read_text(encoding="utf-8")
        self.assertIn("Created docs/adr/ADR-0003-adopt-agent-harness-command-routing-defaults.md", result.stdout)
        self.assertIn('# ADR-0003: Adopt "Agent Harness" command routing / defaults', adr)
        self.assertIn("- Date: 2026-05-05", adr)
        self.assertIn("- Deciders: Template maintainer", adr)
        self.assertIn("- Use deterministic development-mode ADR capture.", adr)
        self.assertIn("- Decision history stays in docs/adr instead of chat only.", adr)
        self.assertIn("- Rely on free-form notes.", adr)

    def test_lab_adr_blocks_in_brainstorming_mode(self) -> None:
        result = run_cmd(
            [
                "./scripts/lab",
                "adr",
                "--title",
                "Should not write",
                "--decision",
                "Do not create ADRs before finalization.",
            ],
            cwd=self.repo,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("/lab adr is not available in brainstorming mode", result.stderr)
        self.assertFalse((self.repo / "docs/adr/ADR-0002-should-not-write.md").exists())

    def test_lab_adr_requires_decision_text(self) -> None:
        self.write_render_fixture()
        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)

        result = run_cmd(
            ["./scripts/lab", "adr", "--title", "Missing decision"],
            cwd=self.repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the following arguments are required: --decision", result.stderr)


if __name__ == "__main__":
    import unittest

    unittest.main()
