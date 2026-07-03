from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON = SCRIPT_ROOT / "runtime" / "python"
if str(RUNTIME_PYTHON) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PYTHON))

from workflow_test_helpers import LabWorkflowTestCase, run_cmd  # noqa: E402

from template_cli.finalize_state import BackupManager  # noqa: E402
from template_cli.sync import run_lab_sync  # noqa: E402


class LabSyncFailurePathTests(LabWorkflowTestCase):
    def _write_change(self) -> None:
        (self.repo / "IDEA_CATALOG.md").write_text(
            (self.repo / "IDEA_CATALOG.md").read_text(encoding="utf-8") + "\n<!-- sync test -->\n",
            encoding="utf-8",
        )

    def test_sync_without_origin_commits_and_returns_soft_skip(self) -> None:
        self.init_git_repo()
        self._write_change()

        code = run_lab_sync(self.repo, quiet=True)

        self.assertEqual(code, 2)
        log = run_cmd(["git", "log", "--oneline", "-1"], cwd=self.repo)
        self.assertIn("brainstorm: milestone update", log.stdout)

    def test_sync_on_detached_head_commits_and_returns_soft_skip(self) -> None:
        self.init_git_repo()
        run_cmd(["git", "checkout", "--detach"], cwd=self.repo)
        self._write_change()

        code = run_lab_sync(self.repo, quiet=True)

        self.assertEqual(code, 2)

    def test_sync_push_failure_returns_push_code_and_keeps_commit(self) -> None:
        self.init_git_repo()
        run_cmd(["git", "remote", "add", "origin", str(self.tmpdir / "missing-remote.git")], cwd=self.repo)
        self._write_change()

        code = run_lab_sync(self.repo, quiet=True)

        self.assertEqual(code, 3)
        log = run_cmd(["git", "log", "--oneline", "-1"], cwd=self.repo)
        self.assertIn("brainstorm: milestone update", log.stdout)

    def test_sync_push_failure_is_soft_when_warning_suppressed(self) -> None:
        self.init_git_repo()
        run_cmd(["git", "remote", "add", "origin", str(self.tmpdir / "missing-remote.git")], cwd=self.repo)
        self._write_change()

        code = run_lab_sync(self.repo, quiet=True, no_warn_push_failure=True)

        self.assertEqual(code, 0)


class BackupManagerRollbackTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self.root = Path(tempfile.mkdtemp(prefix="backup-manager-tests."))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)

    def test_rollback_restores_backed_up_file_and_removes_created_file(self) -> None:
        original = self.root / "existing.md"
        original.write_text("original content\n", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            with BackupManager(self.root) as backups:
                backups.backup_path("existing.md")
                backups.backup_path("created.md")
                original.write_text("mutated content\n", encoding="utf-8")
                (self.root / "created.md").write_text("new file\n", encoding="utf-8")
                raise RuntimeError("simulated finalize failure")

        self.assertEqual(original.read_text(encoding="utf-8"), "original content\n")
        self.assertFalse((self.root / "created.md").exists())

    def test_commit_keeps_mutations(self) -> None:
        original = self.root / "existing.md"
        original.write_text("original content\n", encoding="utf-8")

        with BackupManager(self.root) as backups:
            backups.backup_path("existing.md")
            original.write_text("mutated content\n", encoding="utf-8")
            backups.commit()

        self.assertEqual(original.read_text(encoding="utf-8"), "mutated content\n")


class MalformedCatalogRowTests(LabWorkflowTestCase):
    def test_status_and_doctor_survive_short_catalog_rows(self) -> None:
        catalog_path = self.repo / "IDEA_CATALOG.md"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8") + "| idea-truncated-row | Only Two Cells |\n",
            encoding="utf-8",
        )

        status = run_cmd(["./scripts/lab", "status", "--json"], cwd=self.repo)
        doctor = run_cmd(["./scripts/lab", "doctor", "--json"], cwd=self.repo, check=False)

        self.assertEqual(json.loads(status.stdout)["mode"], "brainstorming")
        self.assertIn(doctor.returncode, (0, 1))
        json.loads(doctor.stdout)


if __name__ == "__main__":
    unittest.main()
