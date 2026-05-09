from __future__ import annotations

import json

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class HarnessManifestTests(LabWorkflowTestCase):
    def test_validate_governance_checks_required_manifest_fields(self) -> None:
        manifest_path = self.repo / "harness_commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["compatibility"]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Harness manifest missing required fields: compatibility", result.stdout)
        self.assertIn("Harness manifest compatibility must be an object.", result.stdout)

    def test_validate_governance_checks_manifest_versions(self) -> None:
        manifest_path = self.repo / "harness_commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schemaVersion"] = 99
        manifest["compatibility"]["stateSchemaVersion"] = 99
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Harness manifest schemaVersion must be 1.", result.stdout)
        self.assertIn("Harness manifest compatibility.stateSchemaVersion must be 2.", result.stdout)

    def test_manifest_inventory_has_update_dry_run_ownership_classes(self) -> None:
        manifest_path = self.repo / "harness_commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        inventory = manifest["artifactInventory"]

        self.assertIn("scripts/", inventory["harnessOwned"])
        self.assertIn("harness_commands/harness_manifest.schema.json", inventory["harnessOwned"])
        self.assertIn("harness_commands/intent_registry.json", inventory["harnessOwned"])
        self.assertIn("harness_commands/intent_registry.schema.json", inventory["harnessOwned"])
        self.assertIn("state/project-init.json", inventory["projectOwned"])
        self.assertIn("README.md", inventory["mixedGenerated"])
        self.assertIn("harness_commands/harness_manifest.json", inventory["mixedGenerated"])
        self.assertIn("docs/adr/", inventory["archival"])

    def test_harness_command_schema_files_are_valid_json_contracts(self) -> None:
        manifest_schema = json.loads(
            (self.repo / "harness_commands/harness_manifest.schema.json").read_text(encoding="utf-8")
        )
        intent_schema = json.loads(
            (self.repo / "harness_commands/intent_registry.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(manifest_schema["properties"]["schemaVersion"]["const"], 1)
        self.assertIn("artifactInventory", manifest_schema["required"])
        self.assertEqual(intent_schema["properties"]["schemaVersion"]["const"], 1)
        self.assertIn("intents", intent_schema["required"])

    def test_validate_governance_checks_stable_wrapper_backend_commands(self) -> None:
        manifest_path = self.repo / "harness_commands/harness_manifest.json"
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
        manifest = json.loads((target / "harness_commands/harness_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["sourceCommit"], source_commit)
        self.assertEqual(manifest["sourceCommitType"], "git")
        self.assertFalse(manifest["sourceWorktreeDirty"])
        self.assertEqual(manifest["harnessVersion"], "0.1.0")
        run_cmd(["./scripts/validate-governance"], cwd=target)
