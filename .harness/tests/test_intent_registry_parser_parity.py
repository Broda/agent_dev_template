from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = REPO_ROOT / ".harness" / "runtime" / "python"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from template_cli.lab_cli_parsers import LAB_COMMAND_ARGUMENTS  # noqa: E402

REGISTRY_PATH = REPO_ROOT / ".harness" / "commands" / "intent_registry.json"


def load_registry_intents() -> list[dict]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return registry["intents"]


class IntentRegistryParserParityTests(unittest.TestCase):
    """The registry is the machine-readable command surface external tools rely on.

    Every flag the lab CLI parser accepts must be declared in the registry so
    adapters mapping from the registry can express the full command surface.
    """

    def test_registry_declares_every_parser_flag(self) -> None:
        for intent in load_registry_intents():
            parser_key = f"lab-{intent['command']}"
            if parser_key not in LAB_COMMAND_ARGUMENTS:
                continue
            parser_flags = {spec.flags[0] for spec in LAB_COMMAND_ARGUMENTS[parser_key]}
            registry_flags = set(intent.get("requiredArgs", [])) | set(intent.get("optionalArgs", []))
            missing = parser_flags - registry_flags
            self.assertFalse(
                missing,
                f"Intent '{intent['command']}' registry args are missing CLI parser flags: {sorted(missing)}",
            )

    def test_registry_flag_entries_exist_in_parser(self) -> None:
        for intent in load_registry_intents():
            parser_key = f"lab-{intent['command']}"
            if parser_key not in LAB_COMMAND_ARGUMENTS:
                continue
            parser_flags = {spec.flags[0] for spec in LAB_COMMAND_ARGUMENTS[parser_key]}
            registry_flags = set(intent.get("requiredArgs", [])) | set(intent.get("optionalArgs", []))
            stale = {flag for flag in registry_flags if flag.startswith("--")} - parser_flags
            self.assertFalse(
                stale,
                f"Intent '{intent['command']}' registry declares flags the CLI parser does not accept: {sorted(stale)}",
            )

    def test_registry_required_args_match_parser_required_flags(self) -> None:
        for intent in load_registry_intents():
            parser_key = f"lab-{intent['command']}"
            if parser_key not in LAB_COMMAND_ARGUMENTS:
                continue
            parser_required = {
                spec.flags[0] for spec in LAB_COMMAND_ARGUMENTS[parser_key] if spec.kwargs.get("required")
            }
            registry_required = set(intent.get("requiredArgs", []))
            self.assertEqual(
                registry_required,
                parser_required,
                f"Intent '{intent['command']}' requiredArgs disagree with the CLI parser",
            )


if __name__ == "__main__":
    unittest.main()
