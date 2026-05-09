from __future__ import annotations

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class LabNoteTests(LabWorkflowTestCase):
    def test_lab_note_records_structured_details(self) -> None:
        result = run_cmd(
            [
                "./scripts/lab-note",
                "--topic",
                "Service identity boundary",
                "--source",
                "Unit test discussion",
                "--idea-id",
                "idea-devos",
                "--tags",
                "identity,security",
                "--summary",
                "Dedicated service identities may be useful later.",
                "--detail",
                "GitHub App is preferred over a broad bot account.",
                "--fact",
                "Secrets must not be committed.",
                "--question",
                "Should email ingestion be read-only at first?",
                "--link",
                "Related future ADR topic: service identity boundary.",
                "--no-sync",
            ],
            cwd=self.repo,
        )

        note_path = self.repo / result.stdout.strip().split(": ", maxsplit=1)[1]
        note = note_path.read_text(encoding="utf-8")

        self.assertIn("- Dedicated service identities may be useful later.", note)
        self.assertIn("- GitHub App is preferred over a broad bot account.", note)
        self.assertIn("- Secrets must not be committed.", note)
        self.assertIn("- Should email ingestion be read-only at first?", note)
        self.assertIn("- Related future ADR topic: service identity boundary.", note)

    def test_lab_note_reads_detail_files(self) -> None:
        details_file = self.repo / "details.txt"
        details_file.write_text(
            "- First captured detail\nSecond captured detail\n",
            encoding="utf-8",
        )

        result = run_cmd(
            [
                "./scripts/lab-note",
                "--topic",
                "File-backed note",
                "--details-file",
                str(details_file),
                "--facts-file",
                str(details_file),
                "--no-sync",
            ],
            cwd=self.repo,
        )

        note_path = self.repo / result.stdout.strip().split(": ", maxsplit=1)[1]
        note = note_path.read_text(encoding="utf-8")

        self.assertIn("- First captured detail", note)
        self.assertIn("- Second captured detail", note)


if __name__ == "__main__":
    import unittest

    unittest.main()
