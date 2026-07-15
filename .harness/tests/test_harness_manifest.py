from __future__ import annotations

import json
import os
import stat
import unittest

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class HarnessManifestTests(LabWorkflowTestCase):
    @unittest.skipIf(os.name == "nt", "POSIX file modes are not represented by the Windows filesystem")
    def test_validate_governance_rejects_non_executable_posix_launcher(self) -> None:
        launcher = self.repo / "scripts/lab"
        launcher.chmod(0o644)

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSIX launcher must have the owner execute bit set: scripts/lab", result.stdout)

    @unittest.skipIf(os.name == "nt", "POSIX file modes are not represented by the Windows filesystem")
    def test_validate_governance_accepts_umask_widened_launcher_mode(self) -> None:
        # A fresh clone under umask 002 checks launchers out as 0775; that must
        # not fail validation even though the index contract stays 100755.
        (self.repo / "scripts/lab").chmod(0o775)

        run_cmd(["./scripts/validate-governance"], cwd=self.repo)

    @unittest.skipIf(os.name == "nt", "POSIX file modes are not represented by the Windows filesystem")
    def test_manifest_posix_launcher_inventory_is_executable(self) -> None:
        manifest = json.loads((self.repo / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))

        for relative_path in manifest["posixExecutablePaths"]:
            with self.subTest(relative_path=relative_path):
                mode = stat.S_IMODE((self.repo / relative_path).stat().st_mode)
                self.assertTrue(mode & stat.S_IXUSR)

    def test_validate_governance_checks_required_manifest_fields(self) -> None:
        manifest_path = self.repo / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["compatibility"]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Harness manifest missing required fields: compatibility", result.stdout)
        self.assertIn("Harness manifest compatibility must be an object.", result.stdout)

    def test_validate_governance_checks_inventory_retained_artifact_coverage(self) -> None:
        manifest_path = self.repo / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifactInventoryExclusions"].remove("pyproject.toml")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Harness manifest artifact inventory does not classify retained artifact: pyproject.toml",
            result.stdout,
        )

    def test_validate_governance_checks_broad_inventory_policy_coverage(self) -> None:
        manifest_path = self.repo / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifactInventorySnapshotPolicy"]["broadEntries"].remove("scripts/")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Harness manifest broad artifactInventory entry must be documented in "
            "artifactInventorySnapshotPolicy.broadEntries: harnessOwned.scripts/",
            result.stdout,
        )

    def test_validate_governance_checks_manifest_versions(self) -> None:
        manifest_path = self.repo / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schemaVersion"] = 99
        manifest["compatibility"]["stateSchemaVersion"] = 99
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Harness manifest schemaVersion must be 2.", result.stdout)
        self.assertIn("Harness manifest compatibility.stateSchemaVersion must be 2.", result.stdout)

    def test_manifest_inventory_has_update_dry_run_ownership_classes(self) -> None:
        manifest_path = self.repo / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        inventory = manifest["artifactInventory"]

        self.assertIn("scripts/", inventory["harnessOwned"])
        self.assertIn(".harness/commands/harness_manifest.schema.json", inventory["harnessOwned"])
        self.assertIn(".harness/commands/intent_registry.json", inventory["harnessOwned"])
        self.assertIn(".harness/commands/intent_registry.schema.json", inventory["harnessOwned"])
        self.assertIn(".harness/schemas/", inventory["harnessOwned"])
        self.assertIn("state/project-init.json", inventory["projectOwned"])
        self.assertIn("state/project-init.schema.v2.json", inventory["projectOwned"])
        self.assertIn("README.md", inventory["mixedGenerated"])
        self.assertIn(".harness/commands/harness_manifest.json", inventory["mixedGenerated"])
        self.assertIn("IDEA_CATALOG.md", inventory["archival"])
        self.assertIn("pyproject.toml", manifest["artifactInventoryExclusions"])
        self.assertEqual(
            manifest["artifactInventorySnapshotPolicy"]["decision"],
            "keep-broad-directory-entries",
        )
        self.assertIn("scripts/", manifest["artifactInventorySnapshotPolicy"]["broadEntries"])

    def test_harness_command_schema_files_are_valid_json_contracts(self) -> None:
        manifest_schema = json.loads(
            (self.repo / ".harness/commands/harness_manifest.schema.json").read_text(encoding="utf-8")
        )
        intent_schema = json.loads(
            (self.repo / ".harness/commands/intent_registry.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(manifest_schema["properties"]["schemaVersion"]["const"], 2)
        self.assertIn("posixExecutablePaths", manifest_schema["required"])
        self.assertIn("artifactInventory", manifest_schema["required"])
        self.assertEqual(intent_schema["properties"]["schemaVersion"]["const"], 1)
        self.assertIn("intents", intent_schema["required"])

    def test_validate_governance_applies_harness_manifest_schema(self) -> None:
        schema_path = self.repo / ".harness/commands/harness_manifest.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["required"].append("schemaOnlyField")
        schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Harness manifest schema validation failed", result.stdout)
        self.assertIn("schemaOnlyField", result.stdout)

    def test_validate_governance_checks_stable_wrapper_backend_commands(self) -> None:
        manifest_path = self.repo / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for wrapper in manifest["stableWrappers"]:
            if wrapper["path"] == "scripts/project-harness":
                wrapper["backendCommand"] = "project-harness-new | project-harness-validate"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Harness manifest stable wrapper backendCommand for scripts/project-harness must be "
            "project-harness-new | project-harness-update | project-harness-validate.",
            result.stdout,
        )

    def test_project_harness_new_stamps_git_source_commit(self) -> None:
        self.init_git_repo()
        source_commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()
        target = self.tmpdir / "stamped-project"

        result = run_cmd(["./scripts/project-harness", "new", str(target), "--no-git"], cwd=self.repo)

        self.assertIn("Created project harness:", result.stdout)
        manifest = json.loads((target / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["sourceCommit"], source_commit)
        self.assertEqual(manifest["sourceCommitType"], "git")
        self.assertFalse(manifest["sourceWorktreeDirty"])
        self.assertEqual(manifest["harnessVersion"], "0.1.1")
        run_cmd(["./scripts/validate-governance"], cwd=target)
