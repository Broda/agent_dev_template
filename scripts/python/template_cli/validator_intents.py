from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from template_cli.intents import (
    IntentRegistryError,
    load_intent_registry,
    registry_commands,
    render_intent_docs_to_memory,
)
from template_cli.io_helpers import ValidationResult, read_text
from template_cli.validator_manifest import load_harness_manifest


def documented_lab_commands(root: Path) -> set[str]:
    commands_path = root / "harness_commands/COMMANDS.md"
    if not commands_path.exists():
        return set()
    commands: set[str] = set()
    for match in re.findall(r"### `/lab ([a-z-]+)", read_text(commands_path)):
        commands.add(match.strip())
    return commands


def registered_lab_commands(root: Path) -> set[str]:
    cli_path = root / "scripts/python/cli.py"
    if not cli_path.exists():
        return set()
    result = subprocess.run(
        [sys.executable, str(cli_path), "-h"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    commands: set[str] = set()
    for match in re.findall(r"\blab-([a-z-]+)\b", output):
        commands.add(match.strip())
    return commands


def registered_cli_backend_commands(root: Path) -> set[str]:
    cli_path = root / "scripts/python/cli.py"
    if not cli_path.exists():
        return set()
    result = subprocess.run(
        [sys.executable, str(cli_path), "-h"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return {
        match.strip()
        for match in re.findall(r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+\b", output)
    }


def manifest_stable_wrapper_backends(root: Path) -> dict[str, str]:
    try:
        manifest = load_harness_manifest(root)
    except (FileNotFoundError, ValueError):
        return {}

    backends: dict[str, str] = {}
    stable_wrappers = manifest.get("stableWrappers", [])
    if not isinstance(stable_wrappers, list):
        return backends
    for wrapper in stable_wrappers:
        if not isinstance(wrapper, dict):
            continue
        wrapper_path = str(wrapper.get("path", "")).strip()
        backend_command = str(wrapper.get("backendCommand", "")).strip()
        for raw_backend in backend_command.split("|"):
            backend = raw_backend.strip()
            if not backend or "<" in backend or " " in backend:
                continue
            backends[backend] = wrapper_path
    return backends


def validate_lab_command_parity(root: Path, result: ValidationResult) -> None:
    documented = documented_lab_commands(root)
    registered = registered_lab_commands(root)
    if not documented or not registered:
        return
    missing = sorted(documented - registered)
    for command in missing:
        result.add_failure(f"Documented lab command is not registered in CLI: {command}")


def validate_stable_wrapper_backend_exposure(root: Path, result: ValidationResult) -> None:
    registered = registered_cli_backend_commands(root)
    wrapper_backends = manifest_stable_wrapper_backends(root)
    if not registered or not wrapper_backends:
        return

    for backend, wrapper_path in sorted(wrapper_backends.items()):
        if backend not in registered:
            result.add_failure(
                f"Stable wrapper backend command is not registered in CLI: {backend} "
                f"(from {wrapper_path})"
            )


def validate_intent_registry(root: Path, result: ValidationResult) -> None:
    try:
        registry = load_intent_registry(root)
        registry_command_names = registry_commands(root)
        rendered_docs = render_intent_docs_to_memory(root)
    except IntentRegistryError as exc:
        result.add_failure(str(exc))
        return

    documented = documented_lab_commands(root)
    registered = registered_lab_commands(root)
    validate_stable_wrapper_backend_exposure(root, result)

    missing_doc_sections = sorted(registry_command_names - documented)
    for command in missing_doc_sections:
        result.add_failure(f"Intent registry command is missing a command section in harness_commands/COMMANDS.md: {command}")

    unknown_registry_commands = sorted(registry_command_names - registered)
    for command in unknown_registry_commands:
        result.add_failure(f"Intent registry command is not registered in CLI: {command}")

    for intent in registry["intents"]:
        command = str(intent["command"]).strip()
        backend_intent = str(intent["backendIntent"]).strip()
        wrapper_path = str(intent["wrapperPath"]).strip()
        if not (root / wrapper_path).exists():
            result.add_failure(f"Intent '{command}' wrapperPath does not exist: {wrapper_path}")
        parts = backend_intent.split()
        if not parts or parts[0] != "/lab":
            result.add_failure(
                f"Intent '{command}' backendIntent must start with /lab for agent-dispatched workflow commands: {backend_intent}"
            )
            continue
        if len(parts) < 2:
            result.add_failure(f"Intent '{command}' backendIntent is missing a lab command: {backend_intent}")
            continue
        backend_command = parts[1].strip("[]")
        if backend_command != command:
            result.add_failure(
                f"Intent '{command}' backendIntent command mismatch: expected /lab {command}, found {backend_intent}"
            )
        if backend_command not in registered:
            result.add_failure(
                f"Intent '{command}' backendIntent maps to unsupported lab command: {backend_command}"
            )

    for relative_path, expected_content in rendered_docs.items():
        path = root / relative_path
        if not path.exists():
            result.add_failure(f"Missing generated intent doc target: {relative_path}")
            continue
        if read_text(path) != expected_content:
            result.add_failure(
                f"Generated intent section is stale in {relative_path}. Run ./scripts/render-intent-docs."
            )


def validate_intent_sync_ci(root: Path, result: ValidationResult) -> None:
    ci_path = root / ".github/workflows/ci.yml"
    if not ci_path.exists():
        return

    ci_text = read_text(ci_path)
    required_checks = [
        ("render step", "\n          ./scripts/render-intent-docs\n"),
        (
            "drift warning",
            "Generated intent docs are out of sync. Run ./scripts/render-intent-docs and commit the result.",
        ),
        (
            "focused generated-doc diff",
            "git diff -- harness_commands/CONVERSATIONAL_MODE.md harness_commands/COMMANDS.md",
        ),
    ]
    for label, snippet in required_checks:
        if snippet not in ci_text:
            result.add_failure(f"CI workflow is missing the generated intent sync contract: {label}")
