from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from unittest import mock

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import REPO_ROOT, run_cmd

SCRIPT_ROOT = REPO_ROOT / ".harness/runtime/python"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from template_cli.bootstrap import update_apply  # noqa: E402
from template_cli.bootstrap.update_source import UpdateSource  # noqa: E402
from template_cli.validator_manifest import MANIFEST_PATH, load_harness_manifest  # noqa: E402


class ProjectHarnessUpdateManifestRollbackTests(ProjectHarnessUpdateTestCase):
    def test_update_apply_restores_manifest_when_provenance_validation_fails(self) -> None:
        source, project = self._project_with_source_update("# final validation rollback marker")
        project_wrapper = project / "scripts/lab.sh"
        original_wrapper = project_wrapper.read_text(encoding="utf-8")
        project_manifest = project / MANIFEST_PATH
        original_manifest = project_manifest.read_text(encoding="utf-8")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), mock.patch.object(
            update_apply, "_run", side_effect=[0, 1, 0, 0]
        ):
            result = update_apply._apply_update_source(
                project,
                self._update_source(source, project),
                yes=True,
                include_mixed=False,
            )

        self.assertEqual(1, result)
        self.assertIn("Provenance validation failed after update apply.", stdout.getvalue())
        self.assertEqual(original_manifest, project_manifest.read_text(encoding="utf-8"))
        self.assertEqual(original_wrapper, project_wrapper.read_text(encoding="utf-8"))

    def test_update_apply_restores_manifest_when_stamping_raises_after_mutation(self) -> None:
        source, project = self._project_with_source_update("# stamping rollback marker")
        project_manifest = project / MANIFEST_PATH
        original_manifest = project_manifest.read_text(encoding="utf-8")

        def stamp_then_raise(root, _source_root) -> None:
            manifest_path = root / MANIFEST_PATH
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sourceWorktreeDirty"] = True
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError("simulated stamping failure")

        stdout = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            mock.patch.object(update_apply, "_run", side_effect=[0, 0, 0]),
            mock.patch.object(update_apply, "stamp_harness_manifest", side_effect=stamp_then_raise),
        ):
            result = update_apply._apply_update_source(
                project,
                self._update_source(source, project),
                yes=True,
                include_mixed=False,
            )

        self.assertEqual(1, result)
        self.assertIn("Manifest stamping failed after update apply.", stdout.getvalue())
        self.assertEqual(original_manifest, project_manifest.read_text(encoding="utf-8"))

    def _project_with_source_update(self, marker: str):
        source = self.copy_source()
        self.init_git_source(source)
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=source)
        source_wrapper = source / "scripts/lab.sh"
        source_wrapper.write_text(
            source_wrapper.read_text(encoding="utf-8") + f"\n{marker}\n",
            encoding="utf-8",
        )
        return source, project

    def _update_source(self, source, project) -> UpdateSource:
        return UpdateSource(source, load_harness_manifest(project), load_harness_manifest(source))


if __name__ == "__main__":
    unittest.main()
