from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabSyncBatchingTests(LabWorkflowTestCase):
    def test_no_sync_note_is_folded_into_next_lab_commit(self) -> None:
        self.write_finalize_fixture("idea-batched-sync")
        self.init_git_repo()
        remote_path = self.tmpdir / "remote.git"
        run_cmd(["git", "init", "--bare", str(remote_path)], cwd=self.repo)
        run_cmd(["git", "remote", "add", "origin", str(remote_path)], cwd=self.repo)
        before_head = run_cmd(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()

        note = run_cmd(
            [
                "./scripts/lab-note",
                "--topic",
                "Decision source note",
                "--idea-id",
                "idea-batched-sync",
                "--summary",
                "This note should commit with the next decision.",
                "--no-sync",
            ],
            cwd=self.repo,
        )
        note_path = note.stdout.strip().split(": ", maxsplit=1)[1]
        after_note_head = run_cmd(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()
        self.assertEqual(before_head, after_note_head)

        run_cmd(
            [
                "./scripts/lab",
                "decide",
                "--idea-id",
                "idea-batched-sync",
                "--chosen-option",
                "Batch skipped note files into the final command commit",
                "--rationale",
                "One combined milestone commit is easier to review and push.",
            ],
            cwd=self.repo,
        )

        committed_files = run_cmd(["git", "show", "--name-only", "--format=", "HEAD"], cwd=self.repo).stdout
        self.assertIn(note_path, committed_files)
        self.assertIn("NOTES_CATALOG.md", committed_files)
        self.assertIn("sessions/2026-04-03_idea-batched-sync.md", committed_files)


if __name__ == "__main__":
    import unittest

    unittest.main()
