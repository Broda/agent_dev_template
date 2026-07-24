from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

from template_cli.intent_registry import (
    IntentRegistryError,
    load_intent_registry,
    registry_commands,
)
from template_cli.intents import (
    render_intent_docs_to_memory,
)
from template_cli.io_helpers import ValidationResult, read_text
from template_cli.lab_cli_parsers import LAB_COMMAND_ARGUMENTS
from template_cli.validator_manifest import load_harness_manifest


def documented_lab_commands(root: Path) -> set[str]:
    commands_path = root / ".harness/commands/COMMANDS.md"
    if not commands_path.exists():
        return set()
    commands: set[str] = set()
    for match in re.findall(r"### `/lab ([a-z-]+)", read_text(commands_path)):
        commands.add(match.strip())
    return commands


def registered_lab_commands(root: Path) -> set[str]:
    cli_path = root / ".harness/runtime/python/cli.py"
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
    cli_path = root / ".harness/runtime/python/cli.py"
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
    return {match.strip() for match in re.findall(r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+\b", output)}


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
                f"Stable wrapper backend command is not registered in CLI: {backend} (from {wrapper_path})"
            )


def lab_cli_dispatch_commands(root: Path) -> set[str]:
    dispatch_path = root / ".harness/runtime/python/template_cli/lab_cli_dispatch.py"
    if not dispatch_path.exists():
        return set()
    try:
        tree = ast.parse(read_text(dispatch_path), filename=str(dispatch_path))
    except SyntaxError:
        return set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            is_dispatch_table = any(
                isinstance(target, ast.Name) and target.id == "LAB_COMMAND_DISPATCHERS" for target in node.targets
            )
            value: ast.expr | None = node.value
        elif isinstance(node, ast.AnnAssign):
            is_dispatch_table = isinstance(node.target, ast.Name) and node.target.id == "LAB_COMMAND_DISPATCHERS"
            value = node.value
        else:
            continue
        if not is_dispatch_table:
            continue
        if not isinstance(value, ast.Dict):
            return set()
        return {key.value for key in value.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)}
    return set()


def validate_lab_cli_table_parity(root: Path, result: ValidationResult) -> None:
    dispatch_commands = lab_cli_dispatch_commands(root)
    parser_only = sorted(set(LAB_COMMAND_ARGUMENTS) - dispatch_commands)
    for command in parser_only:
        result.add_failure(f"Lab command parser has no dispatch handler: {command}")

    dispatch_only = sorted(dispatch_commands - set(LAB_COMMAND_ARGUMENTS))
    for command in dispatch_only:
        result.add_failure(f"Lab command dispatch handler has no parser registration: {command}")


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
    validate_lab_cli_table_parity(root, result)

    missing_doc_sections = sorted(registry_command_names - documented)
    for command in missing_doc_sections:
        result.add_failure(
            f"Intent registry command is missing a command section in .harness/commands/COMMANDS.md: {command}"
        )

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
            result.add_failure(f"Intent '{command}' backendIntent maps to unsupported lab command: {backend_command}")

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
        ("plugin mirror sync step", "\n          ./scripts/sync-plugin-skills\n"),
        (
            "drift warning",
            "Generated artifacts are out of sync. Run ./scripts/render-intent-docs and ./scripts/sync-plugin-skills, then commit the result.",
        ),
        (
            "focused generated-doc diff",
            'git diff --binary -- "${generated_paths[@]}" > .ci/generated-drift/generated-artifacts.patch',
        ),
        (
            "changed generated-file capture",
            'cp "$path" ".ci/generated-drift/files/$path"',
        ),
        (
            "drift artifact upload",
            "uses: actions/upload-artifact@v4",
        ),
    ]
    for label, snippet in required_checks:
        if snippet not in ci_text:
            result.add_failure(f"CI workflow is missing the generated intent sync contract: {label}")
