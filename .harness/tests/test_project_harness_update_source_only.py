from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import PureWindowsPath

from project_harness_update_helpers import ProjectHarnessUpdateTestCase
from workflow_test_helpers import REPO_ROOT, run_cmd

SCRIPT_ROOT = REPO_ROOT / ".harness/runtime/python"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from template_cli.development_doc_migration import _format_repository_path  # noqa: E402

OLD_SOURCE_COMMIT = "6afc76667393d73531d52651f1916436e0cf564e"
PROJECT_OWNED_SCHEMA_COMMIT = "125c8ed84f5249c2fc1e8a22256716d8f8bdb041"
CANONICAL_SCHEMA_PATH = ".harness/schemas/project-init.schema.v2.json"
LEGACY_SCHEMA_PATH = "state/project-init.schema.v2.json"


class DevelopmentDocMigrationFormattingTests(unittest.TestCase):
    def test_repository_path_normalizes_windows_separators(self) -> None:
        self.assertEqual(
            ".github/workflows/ci.yml",
            _format_repository_path(PureWindowsPath(r".github\workflows\ci.yml")),
        )
        self.assertEqual(
            ".harness-update-backups/20260728T120000000000Z-development-contract",
            _format_repository_path(
                PureWindowsPath(r".harness-update-backups\20260728T120000000000Z-development-contract")
            ),
        )


class ProjectHarnessUpdateSourceOnlyTests(ProjectHarnessUpdateTestCase):
    def test_target_planner_migrates_old_development_contract_atomically(self) -> None:
        old_source = self._git_checkout_source(PROJECT_OWNED_SCHEMA_COMMIT, "old-development-source")
        current_source = self._current_worktree_source()
        project = self.tmpdir / "old-development-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=old_source)
        self.install_finalized_cli_project(project)
        self._make_legacy_stale_deferred_docs(project)
        state_path = project / "state/project-init.json"
        state_before = state_path.read_bytes()
        authored_markers = {
            "README.md": "Project-authored README migration marker.",
            "docs/ARCHITECTURE.md": "Project-authored architecture migration marker.",
            "docs/ROADMAP.md": "Project-authored roadmap migration marker.",
            "docs/SECURITY_POLICY.md": "Project-authored security migration marker.",
        }
        for relative_path, marker in authored_markers.items():
            path = project / relative_path
            path.write_text(path.read_text(encoding="utf-8") + f"\n{marker}\n", encoding="utf-8")
        self._align_target_generated_docs(current_source, project)
        docs_before = self._migration_doc_bytes(project)
        ci_before = (project / ".github/workflows/ci.yml").read_bytes()
        combined_before = "\n".join(value.decode() for value in docs_before.values())
        self.assertRegex(combined_before, r"(?im)Deferred scope:\s*\n\s*- None recorded\.")

        result = run_cmd(
            [
                *self._target_backend(current_source),
                "--apply",
                "--source-path",
                str(current_source),
                "--yes",
                "--include-mixed",
            ],
            cwd=project,
        )

        self.assertIn("Migrated recognized legacy generated development surfaces:", result.stdout)
        self.assertIn("- .github/workflows/ci.yml", result.stdout)
        self.assertIn("Applied harness update.", result.stdout)
        self.assertIn("validate-development: 0", result.stdout)
        self.assertEqual(state_before, state_path.read_bytes())
        combined_after = "\n".join(
            (project / relative_path).read_text(encoding="utf-8") for relative_path in docs_before
        )
        self.assertNotRegex(combined_after, r"(?im)Deferred scope:\s*\n\s*- None recorded\.")
        self.assertIn("[harness-development-doc-contract]: # (version-2)", combined_after)
        self.assertIn("Harness-Managed Semantic Contract", combined_after)
        self.assertIn("Collectors", combined_after)
        self.assertIn("Report runs are append-only.", combined_after)
        for marker in authored_markers.values():
            self.assertIn(marker, combined_after)
        migration_backups = list(
            (project / ".harness-update-backups").glob("*-development-contract/docs/PROJECT_CONTEXT.md")
        )
        self.assertTrue(migration_backups)
        migrated_ci = (project / ".github/workflows/ci.yml").read_bytes()
        self.assertNotEqual(ci_before, migrated_ci)
        self.assertIn(b"cancel-in-progress: ${{ github.event_name == 'pull_request' }}", migrated_ci)
        self.assertIn(b"timeout-minutes: 60", migrated_ci)
        self.assertIn(b"retention-days: 3", migrated_ci)
        validation = run_cmd(["./scripts/validate-development"], cwd=project)
        self.assertIn("PASS: development integrity checks completed with no blocking failures.", validation.stdout)

    def test_target_planner_restores_old_migrated_docs_when_validation_fails(self) -> None:
        old_source = self._git_checkout_source(PROJECT_OWNED_SCHEMA_COMMIT, "rollback-development-source")
        current_source = self._current_worktree_source()
        project = self.tmpdir / "rollback-development-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=old_source)
        self.install_finalized_cli_project(project)
        self._make_legacy_stale_deferred_docs(project)
        roadmap_path = project / "docs/ROADMAP.md"
        roadmap_path.write_text(
            roadmap_path.read_text(encoding="utf-8") + "\n- [ ] Build web ui (forced validation failure).\n",
            encoding="utf-8",
        )
        self._align_target_generated_docs(current_source, project)
        state_path = project / "state/project-init.json"
        state_before = state_path.read_bytes()
        docs_before = self._migration_doc_bytes(project)
        ci_before = (project / ".github/workflows/ci.yml").read_bytes()
        runtime_path = project / ".harness/runtime/python/template_cli/plugin_sync.py"
        runtime_before = runtime_path.read_bytes()

        result = run_cmd(
            [
                *self._target_backend(current_source),
                "--apply",
                "--source-path",
                str(current_source),
                "--yes",
                "--include-mixed",
            ],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Rolled back generated development-surface migration after validation failure.", result.stdout)
        self.assertIn("Post-update hook failed. Rolled back copied files from backup:", result.stdout)
        self.assertEqual(state_before, state_path.read_bytes())
        self.assertEqual(docs_before, self._migration_doc_bytes(project))
        self.assertEqual(ci_before, (project / ".github/workflows/ci.yml").read_bytes())
        self.assertEqual(runtime_before, runtime_path.read_bytes())

    def test_target_planner_preserves_old_customized_ci_and_fails_closed(self) -> None:
        old_source = self._git_checkout_source(PROJECT_OWNED_SCHEMA_COMMIT, "custom-ci-source")
        current_source = self._current_worktree_source()
        project = self.tmpdir / "custom-ci-project"
        run_cmd(["./scripts/project-harness", "new", str(project), "--no-git"], cwd=old_source)
        self.install_finalized_cli_project(project)
        self._align_target_generated_docs(current_source, project)
        ci_path = project / ".github/workflows/ci.yml"
        ci_path.write_text(
            ci_path.read_text(encoding="utf-8") + "\n# Project-owned CI customization.\n", encoding="utf-8"
        )
        ci_before = ci_path.read_bytes()
        runtime_path = project / ".harness/runtime/python/template_cli/plugin_sync.py"
        runtime_before = runtime_path.read_bytes()

        result = run_cmd(
            [
                *self._target_backend(current_source),
                "--apply",
                "--source-path",
                str(current_source),
                "--yes",
                "--include-mixed",
            ],
            cwd=project,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing CI-efficiency contract", result.stdout)
        self.assertIn("Post-update hook failed. Rolled back copied files from backup:", result.stdout)
        self.assertEqual(ci_before, ci_path.read_bytes())
        self.assertEqual(runtime_before, runtime_path.read_bytes())

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
        for relative_path in [
            ".github/workflows/governance-audit.yml",
            ".github/workflows/release-readiness.yml",
        ]:
            shutil.copy2(current_source / relative_path, project / relative_path)

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

    @staticmethod
    def _target_backend(current_source):
        return [
            "python3",
            str(current_source / ".harness/runtime/python/cli.py"),
            "project-harness-update",
        ]

    @staticmethod
    def _migration_doc_bytes(project):
        paths = [
            "README.md",
            "docs/PROJECT_CONTEXT.md",
            "docs/ARCHITECTURE.md",
            "docs/ROADMAP.md",
            "docs/adr/ADR-0001-record-architecture-decisions.md",
            "docs/SECURITY_POLICY.md",
        ]
        return {relative_path: (project / relative_path).read_bytes() for relative_path in paths}

    @staticmethod
    def _make_legacy_stale_deferred_docs(project):
        replacements = {
            "docs/PROJECT_CONTEXT.md": (
                "Deferred scope:\n\n- Collectors\n- Remote APIs\n- Browser UI\n- Authentication",
                "Deferred scope:\n\n- None recorded.",
            ),
            "docs/ARCHITECTURE.md": (
                "Deferred scope:\n\n- Collectors\n- Remote APIs\n- Browser UI\n- Authentication",
                "Deferred scope: None recorded.",
            ),
        }
        for relative_path, (populated, stale) in replacements.items():
            path = project / relative_path
            content = path.read_text(encoding="utf-8")
            if populated not in content:
                raise AssertionError(f"fixture cannot create legacy stale deferred block in {relative_path}")
            path.write_text(content.replace(populated, stale, 1), encoding="utf-8")

    @staticmethod
    def _align_target_generated_docs(current_source, project):
        for relative_path in ProjectHarnessUpdateSourceOnlyTests._migration_doc_bytes(project):
            target = current_source / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(project / relative_path, target)
