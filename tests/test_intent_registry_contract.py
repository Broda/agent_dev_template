from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(
    args: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


class IntentRegistryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="codex-template-tests."))
        self.repo = self.tmpdir / "repo"
        shutil.copytree(
            REPO_ROOT,
            self.repo,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_render_intent_docs_is_idempotent_on_clean_repo(self) -> None:
        run_cmd(["./scripts/render-intent-docs"], cwd=self.repo)
        first_conv = (self.repo / "harness_commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8")
        first_commands = (self.repo / "harness_commands/COMMANDS.md").read_text(encoding="utf-8")
        run_cmd(["./scripts/render-intent-docs"], cwd=self.repo)
        second_conv = (self.repo / "harness_commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8")
        second_commands = (self.repo / "harness_commands/COMMANDS.md").read_text(encoding="utf-8")
        self.assertEqual(first_conv, second_conv)
        self.assertEqual(first_commands, second_commands)

    def test_validate_governance_fails_on_stale_generated_intent_section(self) -> None:
        conv_path = self.repo / "harness_commands/CONVERSATIONAL_MODE.md"
        conv_text = conv_path.read_text(encoding="utf-8").replace(
            '"capture this idea", "save this idea", "log this idea"',
            '"capture this idea", "stale phrase", "log this idea"',
            1,
        )
        conv_path.write_text(conv_text, encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Generated intent section is stale", result.stdout + result.stderr)
        run_cmd(["./scripts/render-intent-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-governance"], cwd=self.repo)

    def test_validate_governance_fails_on_unknown_registry_command(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["command"] = "unknown-command"
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Intent registry command is not registered in CLI: unknown-command", result.stdout + result.stderr)

    def test_validate_governance_fails_on_backend_intent_command_drift(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["backendIntent"] = "/lab missing <idea-id>"
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("Intent 'capture' backendIntent command mismatch", output)
        self.assertIn("Intent 'capture' backendIntent maps to unsupported lab command: missing", output)

    def test_validate_governance_fails_on_non_lab_backend_intent(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["backendIntent"] = "/scripts/custom-capture <idea-id>"
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Intent 'capture' backendIntent must start with /lab for agent-dispatched workflow commands",
            result.stdout + result.stderr,
        )

    def test_validate_governance_fails_when_ci_sync_step_is_removed(self) -> None:
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_text = ci_path.read_text(encoding="utf-8").replace("          ./scripts/render-intent-docs\n", "", 1)
        ci_path.write_text(ci_text, encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "CI workflow is missing the generated intent sync contract: render step",
            result.stdout + result.stderr,
        )

    def test_validate_governance_fails_when_ci_focused_diff_is_removed(self) -> None:
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_text = ci_path.read_text(encoding="utf-8").replace(
            "            git diff -- harness_commands/CONVERSATIONAL_MODE.md harness_commands/COMMANDS.md\n",
            "",
            1,
        )
        ci_path.write_text(ci_text, encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "CI workflow is missing the generated intent sync contract: focused generated-doc diff",
            result.stdout + result.stderr,
        )

    def test_validate_governance_fails_when_ci_drift_warning_is_removed(self) -> None:
        ci_path = self.repo / ".github/workflows/ci.yml"
        ci_text = ci_path.read_text(encoding="utf-8").replace(
            '            echo "Generated intent docs are out of sync. Run ./scripts/render-intent-docs and commit the result."\n',
            "",
            1,
        )
        ci_path.write_text(ci_text, encoding="utf-8")
        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "CI workflow is missing the generated intent sync contract: drift warning",
            result.stdout + result.stderr,
        )

    def test_validate_governance_checks_non_lab_wrapper_backend_exposure(self) -> None:
        cli_path = self.repo / "scripts/python/cli.py"
        cli_text = cli_path.read_text(encoding="utf-8")
        cli_text = cli_text.replace('    subparsers.add_parser("sync-plugin-skills")\n', "", 1)
        cli_path.write_text(cli_text, encoding="utf-8")

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Stable wrapper backend command is not registered in CLI: sync-plugin-skills "
            "(from scripts/sync-plugin-skills)",
            result.stdout + result.stderr,
        )

    def test_render_intent_docs_fails_on_malformed_registry(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry_path.write_text("{\n", encoding="utf-8")
        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid JSON", result.stdout + result.stderr)

    def test_render_intent_docs_fails_on_duplicate_registry_command(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][1]["command"] = registry["intents"][0]["command"]
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate intent command", result.stdout + result.stderr)

    def test_render_intent_docs_fails_on_missing_phrases(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["phrases"] = []
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty phrases list", result.stdout + result.stderr)

    def test_render_intent_docs_fails_on_missing_modes(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0].pop("modes")
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required keys: modes", result.stdout + result.stderr)

    def test_render_intent_docs_fails_on_invalid_modes(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["modes"] = ["brainstorming", "unsupported"]
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Intent 'capture' contains invalid modes: unsupported", result.stdout + result.stderr)

    def test_render_intent_docs_fails_on_missing_capability_field(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0].pop("readOnlySafe")
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required keys: readOnlySafe", result.stdout + result.stderr)

    def test_render_intent_docs_applies_registry_schema(self) -> None:
        schema_path = self.repo / "harness_commands/intent_registry.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["required"].append("schemaOnlyField")
        schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("Intent registry schema validation failed", output)
        self.assertIn("schemaOnlyField", output)

    def test_render_intent_docs_fails_on_read_only_capability_drift(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["readOnlySafe"] = True
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Intent 'capture' readOnlySafe must match no-write behavior", result.stdout + result.stderr)

    def test_validate_governance_fails_on_missing_wrapper_path(self) -> None:
        registry_path = self.repo / "harness_commands/intent_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["intents"][0]["wrapperPath"] = "scripts/missing-lab"
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        run_cmd(["./scripts/render-intent-docs"], cwd=self.repo)

        result = run_cmd(["./scripts/validate-governance"], cwd=self.repo, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Intent 'capture' wrapperPath does not exist: scripts/missing-lab", result.stdout + result.stderr)

    def test_generated_docs_include_capability_surface(self) -> None:
        commands = (self.repo / "harness_commands/COMMANDS.md").read_text(encoding="utf-8")
        conversational = (self.repo / "harness_commands/CONVERSATIONAL_MODE.md").read_text(encoding="utf-8")

        self.assertIn("| Command | Modes | Backend intent | Wrapper | Required args |", commands)
        self.assertIn("`scripts/lab`", commands)
        self.assertIn("`--idea-id`", commands)
        self.assertIn("Output and exit codes", commands)
        self.assertIn("| Natural phrase family | Modes | Action | Read-only safe | Mutation scope |", conversational)

    def test_render_intent_docs_fails_on_missing_markers(self) -> None:
        commands_path = self.repo / "harness_commands/COMMANDS.md"
        commands_text = commands_path.read_text(encoding="utf-8").replace(
            "<!-- BEGIN GENERATED CONVERSATIONAL INTENT MAPPING -->\n",
            "",
            1,
        )
        commands_path.write_text(commands_text, encoding="utf-8")
        result = run_cmd(["./scripts/render-intent-docs"], cwd=self.repo, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing or invalid generated section markers", result.stdout + result.stderr)

    def test_render_intent_docs_preserves_surrounding_text(self) -> None:
        commands_path = self.repo / "harness_commands/COMMANDS.md"
        original = commands_path.read_text(encoding="utf-8")
        updated = original.replace(
            "## Commands (Backend Contract)",
            "Custom preserved note.\n\n## Commands (Backend Contract)",
            1,
        )
        commands_path.write_text(updated, encoding="utf-8")
        run_cmd(["./scripts/render-intent-docs"], cwd=self.repo)
        rendered = commands_path.read_text(encoding="utf-8")
        self.assertIn("Custom preserved note.", rendered)
        self.assertIn("## Commands (Backend Contract)", rendered)


if __name__ == "__main__":
    unittest.main()
