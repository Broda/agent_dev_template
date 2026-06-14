from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON = SCRIPT_ROOT / "runtime" / "python"
if str(RUNTIME_PYTHON) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PYTHON))

from workflow_test_helpers import LabWorkflowTestCase, run_cmd  # noqa: E402

from template_cli.external_idea import ExternalIdeaImportResult, ExternalIdeaPayload  # noqa: E402


class ExternalIdeaPayloadTests(LabWorkflowTestCase):
    def test_payload_normalizes_idea_id(self) -> None:
        payload = ExternalIdeaPayload(
            idea_id="example-web-app",
            title="Example Web App",
            summary="Small web application for demonstration.",
            source="external-system",
            source_id="example-source-id-123",
        )

        self.assertEqual(payload.normalized_idea_id, "idea-example-web-app")

    def test_result_json_uses_relative_paths(self) -> None:
        result = ExternalIdeaImportResult(
            ok=True,
            idea_id="idea-example-web-app",
            title="Example Web App",
            status="active",
            source="external-system",
            source_id="example-source-id-123",
            session_path="sessions/2026-06-14_idea-example-web-app.md",
            changed_files=["IDEA_CATALOG.md", "ideas/_active.md"],
            readiness="needs-input",
        )

        data = result.to_json_dict()

        self.assertEqual(data["session_path"], "sessions/2026-06-14_idea-example-web-app.md")
        self.assertTrue(all(not Path(path).is_absolute() for path in data["changed_files"]))

    def test_lab_import_idea_json_is_idempotent_and_public_safe(self) -> None:
        result = run_cmd(
            [
                "./scripts/lab",
                "import-idea",
                "--idea-id",
                "example-web-app",
                "--title",
                "Example Web App",
                "--summary",
                "Small web application for demonstration.",
                "--source",
                "external-system",
                "--source-id",
                "example-source-id-123",
                "--activate",
                "--create-session",
                "--path-note",
                "Imported from an external idea source.",
                "--no-sync",
                "--json",
            ],
            cwd=self.repo,
        )
        second = run_cmd(
            [
                "./scripts/lab",
                "import-idea",
                "--idea-id",
                "example-web-app",
                "--title",
                "Example Web App",
                "--summary",
                "Small web application for demonstration.",
                "--source",
                "external-system",
                "--source-id",
                "example-source-id-123",
                "--activate",
                "--create-session",
                "--path-note",
                "Imported from an external idea source.",
                "--no-sync",
                "--json",
            ],
            cwd=self.repo,
        )

        data = json.loads(result.stdout)
        second_data = json.loads(second.stdout)
        self.assertEqual(data["idea_id"], "idea-example-web-app")
        self.assertEqual(data["source"], "external-system")
        self.assertTrue(data["session_path"].startswith("sessions/"))
        self.assertTrue(all(not Path(path).is_absolute() for path in data["changed_files"]))
        self.assertEqual(second_data["idea_id"], data["idea_id"])
        catalog_lines = (self.repo / "IDEA_CATALOG.md").read_text(encoding="utf-8").splitlines()
        catalog_rows = [line for line in catalog_lines if line.startswith("| idea-example-web-app |")]
        self.assertEqual(len(catalog_rows), 1)
        self.assertFalse(list(self.repo.glob("**/*devos-idea*")))

    def test_lab_import_idea_accepts_payload_file(self) -> None:
        payload_path = self.tmpdir / "payload.json"
        payload_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "idea_id": "example-web-app",
                    "title": "Example Web App",
                    "summary": "Small web application for demonstration.",
                    "source": "external-system",
                    "source_id": "example-source-id-123",
                    "tags": ["web", "demo"],
                }
            ),
            encoding="utf-8",
        )

        result = run_cmd(
            [
                "./scripts/lab",
                "import-idea",
                "--payload-file",
                str(payload_path),
                "--activate",
                "--create-session",
                "--no-sync",
                "--json",
            ],
            cwd=self.repo,
        )

        data = json.loads(result.stdout)
        self.assertEqual(data["idea_id"], "idea-example-web-app")
        self.assertEqual(data["source_id"], "example-source-id-123")

    def test_lab_root_flag_works_from_different_cwd(self) -> None:
        result = run_cmd(
            [str(self.repo / "scripts/lab"), "--root", str(self.repo), "status", "--json"],
            cwd=self.tmpdir,
        )

        data = json.loads(result.stdout)
        self.assertEqual(data["mode"], "brainstorming")

    def test_project_harness_new_from_idea_creates_seeded_project(self) -> None:
        target = self.tmpdir / "example-project"

        result = run_cmd(
            [
                str(self.repo / "scripts/project-harness"),
                "--template-root",
                str(self.repo),
                "new-from-idea",
                str(target),
                "--idea-id",
                "example-web-app",
                "--title",
                "Example Web App",
                "--summary",
                "Small web application for demonstration.",
                "--source",
                "external-system",
                "--source-id",
                "example-source-id-123",
                "--activate",
                "--commit",
                "--json",
            ],
            cwd=self.tmpdir,
        )

        data = json.loads(result.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["idea_id"], "idea-example-web-app")
        self.assertTrue((target / "sessions").exists())
        status = run_cmd(["./scripts/lab", "status", "--json"], cwd=target)
        status_data = json.loads(status.stdout)
        self.assertEqual(status_data["mode"], "brainstorming")
        self.assertIn("idea-example-web-app", (target / "IDEA_CATALOG.md").read_text(encoding="utf-8"))
        self.assertFalse(list(target.glob("**/*devos-idea*")))
        log = run_cmd(["git", "log", "--oneline", "-1"], cwd=target)
        self.assertIn("import external idea idea-example-web-app", log.stdout)

    def test_project_harness_new_from_idea_accepts_payload_file(self) -> None:
        target = self.tmpdir / "payload-project"
        payload_path = self.tmpdir / "payload.json"
        payload_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "idea_id": "payload-web-app",
                    "title": "Payload Web App",
                    "summary": "Payload file import example.",
                    "source": "external-system",
                    "source_id": "example-source-id-456",
                }
            ),
            encoding="utf-8",
        )

        result = run_cmd(
            [
                str(self.repo / "scripts/project-harness"),
                "--template-root",
                str(self.repo),
                "new-from-idea",
                str(target),
                "--payload-file",
                str(payload_path),
                "--json",
            ],
            cwd=self.tmpdir,
        )

        data = json.loads(result.stdout)
        self.assertEqual(data["idea_id"], "idea-payload-web-app")

    def test_lab_import_idea_reports_payload_errors_as_json(self) -> None:
        payload_path = self.tmpdir / "bad-payload.json"
        payload_path.write_text(json.dumps({"schema_version": 2, "idea_id": "x", "title": "Bad"}), encoding="utf-8")

        result = run_cmd(
            [
                "./scripts/lab",
                "import-idea",
                "--payload-file",
                str(payload_path),
                "--json",
                "--no-sync",
            ],
            cwd=self.repo,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertFalse(result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["code"], "unsupported_schema")
        self.assertIn("schema_version", data["error"])

    def test_project_harness_new_from_idea_reports_payload_errors_as_json(self) -> None:
        target = self.tmpdir / "bad-project"
        payload_path = self.tmpdir / "bad-payload.json"
        payload_path.write_text("{not-json", encoding="utf-8")

        result = run_cmd(
            [
                str(self.repo / "scripts/project-harness"),
                "--template-root",
                str(self.repo),
                "new-from-idea",
                str(target),
                "--payload-file",
                str(payload_path),
                "--json",
            ],
            cwd=self.tmpdir,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertFalse(result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["code"], "invalid_json")
        self.assertFalse(target.exists())


if __name__ == "__main__":
    import unittest

    unittest.main()
