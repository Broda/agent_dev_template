from __future__ import annotations

import json
import shutil

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import REPO_ROOT, run_cmd

OLD_SOURCE_COMMIT = "6afc76667393d73531d52651f1916436e0cf564e"
PROJECT_OWNED_SCHEMA_COMMIT = "125c8ed84f5249c2fc1e8a22256716d8f8bdb041"
CANONICAL_SCHEMA_PATH = ".harness/schemas/project-init.schema.v2.json"
LEGACY_SCHEMA_PATH = "state/project-init.schema.v2.json"


class ProjectHarnessUpdateSourceOnlyTests(ProjectHarnessUpdateTestCase):
    def test_old_downstream_updater_installs_new_schema_path_in_one_pass(self) -> None:
        old_source = self._git_checkout_source(PROJECT_OWNED_SCHEMA_COMMIT, "project-owned-schema-source")
        current_source = self._current_worktree_source()
        project = self.tmpdir / "project-owned-schema-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=old_source)
        state_path = project / "state/project-init.json"
        state_before = state_path.read_bytes()
        legacy_schema_before = (project / LEGACY_SCHEMA_PATH).read_bytes()
        self.assertFalse((project / CANONICAL_SCHEMA_PATH).exists())

        dry_run = run_cmd(
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", str(current_source)],
            cwd=project,
        )

        missing_section = dry_run.stdout.split("missing:", 1)[1].split("removed:", 1)[0]
        preserved_section = dry_run.stdout.split("project-owned-preserved:", 1)[1].split("unchanged:", 1)[0]
        self.assertIn(CANONICAL_SCHEMA_PATH, missing_section)
        self.assertIn(LEGACY_SCHEMA_PATH, preserved_section)
        self.assertIn("state/project-init.json", preserved_section)

        result = run_cmd(
            [
                "./scripts/project-harness",
                "update",
                "--apply",
                "--source-path",
                str(current_source),
                "--yes",
                "--include-mixed",
            ],
            cwd=project,
        )

        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn(CANONICAL_SCHEMA_PATH, result.stdout)
        self.assertEqual(state_before, state_path.read_bytes())
        self.assertEqual(legacy_schema_before, (project / LEGACY_SCHEMA_PATH).read_bytes())
        self.assertEqual(
            (current_source / CANONICAL_SCHEMA_PATH).read_bytes(), (project / CANONICAL_SCHEMA_PATH).read_bytes()
        )
        manifest = json.loads((project / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(CANONICAL_SCHEMA_PATH, manifest["compatibility"]["stateSchemaPath"])
        validation = run_cmd(["./scripts/validate-governance"], cwd=project)
        self.assertIn("PASS: lean integrity checks completed with no blocking failures.", validation.stdout)

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
