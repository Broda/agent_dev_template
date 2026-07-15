from __future__ import annotations

import shutil

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import REPO_ROOT, run_cmd

OLD_SOURCE_COMMIT = "6afc76667393d73531d52651f1916436e0cf564e"


class ProjectHarnessUpdateSourceOnlyTests(ProjectHarnessUpdateTestCase):
    def test_update_apply_installs_source_only_modules_from_old_source_snapshot(self) -> None:
        old_source = self._git_checkout_source(OLD_SOURCE_COMMIT, "old-source")
        current_source = self._current_worktree_source()
        project = self.tmpdir / "generated-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=old_source)
        (current_source / "README.md").write_text((project / "README.md").read_text(encoding="utf-8"), encoding="utf-8")

        missing_modules = [
            ".harness/runtime/python/template_cli/finalized_contract.py",
            ".harness/runtime/python/template_cli/finalized_contract_tokens.py",
            ".harness/runtime/python/template_cli/render_capabilities.py",
            ".harness/runtime/python/template_cli/render_policy_docs.py",
            ".harness/runtime/python/template_cli/validator_semantics.py",
        ]
        for relative_path in missing_modules:
            with self.subTest(before=relative_path):
                self.assertFalse((project / relative_path).exists())

        backend = ["python3", str(REPO_ROOT / ".harness/runtime/python/cli.py"), "project-harness-update"]
        result = run_cmd(
            [*backend, "--apply", "--source-path", str(current_source), "--yes", "--include-mixed"],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn("validate-governance: 0", result.stdout)
        for relative_path in missing_modules:
            with self.subTest(after=relative_path):
                self.assertIn(relative_path, result.stdout)
                self.assertTrue((project / relative_path).exists())
        validation = run_cmd(["./scripts/validate-governance"], cwd=project)
        self.assertIn("PASS: lean integrity checks completed with no blocking failures.", validation.stdout)

    def _git_checkout_source(self, commit: str, dirname: str):
        result = run_cmd(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=REPO_ROOT, check=False)
        if result.returncode != 0:
            self.skipTest(f"source snapshot commit is unavailable: {commit}")
        source = self.tmpdir / dirname
        run_cmd(["git", "clone", "--quiet", str(REPO_ROOT), str(source)], cwd=self.tmpdir)
        run_cmd(["git", "checkout", "--quiet", commit], cwd=source)
        return source

    def _current_worktree_source(self):
        source = self.tmpdir / "current-source"
        run_cmd(["git", "clone", "--quiet", str(REPO_ROOT), str(source)], cwd=self.tmpdir)
        shutil.copytree(
            REPO_ROOT,
            source,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        return source
