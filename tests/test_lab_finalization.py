from __future__ import annotations

import json

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabFinalizationTests(LabWorkflowTestCase):
    def test_lab_finalize_wrapper_records_session_and_switches_mode(self) -> None:
        self.write_finalize_fixture()
        result = run_cmd(
            ["./scripts/lab", "finalize", "--idea-id", "idea-finalize-smoke", "--write-export"],
            cwd=self.repo,
            input_text="\n" * 12,
        )
        self.assertIn("successfully finalized", result.stdout.lower())
        self.assertNotIn("One-sentence objective", result.stdout)
        self.assertIn("Current mode: development", (self.repo / "MODE.md").read_text(encoding="utf-8"))
        sessions = sorted((self.repo / "sessions").glob("*FINALIZATION_SESSION*.md"))
        self.assertTrue(sessions)
        exports = sorted((self.repo / "exports").glob("*PROJECT_SUMMARY*.md"))
        self.assertTrue(exports)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_lab_finalize_defaults_to_single_active_idea_without_prompts(self) -> None:
        self.write_finalize_fixture("idea-default-finalize")
        result = run_cmd(["./scripts/lab", "finalize"], cwd=self.repo)
        self.assertIn("successfully finalized", result.stdout.lower())
        self.assertNotIn("One-sentence objective", result.stdout)
        state = json.loads((self.repo / "state/project-init.json").read_text(encoding="utf-8"))
        self.assertEqual(state["ideaId"], "idea-default-finalize")
        self.assertEqual(state["status"], "finalized")
        self.assertEqual(
            state["documentation"]["wiki"],
            {
                "enabled": False,
                "pathEnv": "PROJECT_HARNESS_WIKI_DIR",
                "defaultCheckout": "../repo.wiki",
                "remote": "",
            },
        )
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_lab_finalize_interactive_preserves_prompt_fill_flow(self) -> None:
        self.write_finalize_fixture("idea-interactive-finalize")
        result = run_cmd(
            ["./scripts/lab", "finalize", "--idea-id", "idea-interactive-finalize", "--interactive"],
            cwd=self.repo,
            input_text="\n" * 12,
        )
        self.assertIn("successfully finalized", result.stdout.lower())
        self.assertIn("One-sentence objective", result.stdout)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

    def test_lab_finalize_missing_fields_fail_without_prompting(self) -> None:
        run_cmd(
            [
                "./scripts/lab",
                "capture",
                "--idea-id",
                "idea-incomplete-finalize",
                "--title",
                "Incomplete Finalize",
                "--no-sync",
            ],
            cwd=self.repo,
        )
        run_cmd(["./scripts/lab", "activate", "--idea-id", "idea-incomplete-finalize", "--no-sync"], cwd=self.repo)
        result = run_cmd(["./scripts/lab", "finalize"], cwd=self.repo, check=False)
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cannot finalize non-interactively because required fields are missing.", combined)
        self.assertIn("- language", combined)
        self.assertIn("- build command", combined)
        self.assertIn("- MVP scope", combined)
        self.assertNotIn("One-sentence objective", combined)

    def test_lab_finalize_preserves_curated_artifact_references(self) -> None:
        self.write_finalize_fixture("idea-finalize-preserve")
        custom_adr = self.repo / "docs/adr/ADR-0099-custom-preserved-reference.md"
        custom_adr.parent.mkdir(parents=True, exist_ok=True)
        custom_adr.write_text("# ADR 0099\n\nPreserved custom ADR reference.\n", encoding="utf-8")
        preserved_export = self.repo / "exports/2026-04-03_PROJECT_SUMMARY_idea-finalize-preserve.md"
        preserved_export.parent.mkdir(parents=True, exist_ok=True)
        preserved_export.write_text("# Summary Export\n\nPreserved export.\n", encoding="utf-8")
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["artifacts"]["noteReferences"] = "notes/2026-04-03_note-0001-preserved-reference.md"
        state["artifacts"]["summaryExport"] = "exports/2026-04-03_PROJECT_SUMMARY_idea-finalize-preserve.md"
        state["artifacts"]["adrReferences"] = [
            "docs/adr/ADR-0099-custom-preserved-reference.md",
        ]
        state["documentation"] = {
            "wiki": {
                "enabled": True,
                "pathEnv": "CUSTOM_WIKI_DIR",
                "defaultCheckout": "../custom.wiki",
                "remote": "git@example.com:owner/custom.wiki.git",
            }
        }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(
            ["./scripts/lab", "finalize", "--idea-id", "idea-finalize-preserve"],
            cwd=self.repo,
            input_text="\n" * 12,
        )

        self.assertIn("successfully finalized", result.stdout.lower())
        finalized_state = json.loads(state_path.read_text(encoding="utf-8"))
        artifacts = finalized_state["artifacts"]
        self.assertEqual(
            artifacts["noteReferences"],
            "notes/2026-04-03_note-0001-preserved-reference.md",
        )
        self.assertEqual(
            artifacts["summaryExport"],
            "exports/2026-04-03_PROJECT_SUMMARY_idea-finalize-preserve.md",
        )
        self.assertIn("docs/adr/ADR-0099-custom-preserved-reference.md", artifacts["adrReferences"])
        self.assertIn(
            "docs/adr/ADR-0001-record-architecture-decisions.md",
            artifacts["adrReferences"],
        )
        self.assertEqual(finalized_state["documentation"]["wiki"]["enabled"], True)
        self.assertEqual(finalized_state["documentation"]["wiki"]["pathEnv"], "CUSTOM_WIKI_DIR")
        self.assertEqual(finalized_state["documentation"]["wiki"]["defaultCheckout"], "../custom.wiki")
        self.assertEqual(finalized_state["documentation"]["wiki"]["remote"], "git@example.com:owner/custom.wiki.git")
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
        self.assertIn("multiple active ideas found", result.stderr.lower() + result.stdout.lower())
        self.assertIn("pass --idea-id explicitly", result.stderr.lower() + result.stdout.lower())


if __name__ == "__main__":
    import unittest

    unittest.main()
