from __future__ import annotations

import json
from pathlib import Path

from template_cli.json_schema import validate_json_schema_file


INTENT_REGISTRY_FILE = "harness_commands/intent_registry.json"
INTENT_REGISTRY_SCHEMA_FILE = "harness_commands/intent_registry.schema.json"
CONVERSATIONAL_DOC = "harness_commands/CONVERSATIONAL_MODE.md"
COMMANDS_DOC = "harness_commands/COMMANDS.md"
CONVERSATIONAL_MARKER_START = "<!-- BEGIN GENERATED INTENT MAP -->"
CONVERSATIONAL_MARKER_END = "<!-- END GENERATED INTENT MAP -->"
COMMANDS_MARKER_START = "<!-- BEGIN GENERATED CONVERSATIONAL INTENT MAPPING -->"
COMMANDS_MARKER_END = "<!-- END GENERATED CONVERSATIONAL INTENT MAPPING -->"
ALLOWED_WRITE_BEHAVIORS = {"write", "no-write", "git"}
ALLOWED_MODES = {"brainstorming", "development"}
ALLOWED_MUTATION_SCOPES = {"none", "project-files", "git", "external-wiki"}


class IntentRegistryError(Exception):
    pass


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _trim(value: str | None) -> str:
    return (value or "").strip()


def load_intent_registry(root: Path) -> dict:
    path = root / INTENT_REGISTRY_FILE
    try:
        data = json.loads(_read_text(path))
    except FileNotFoundError as exc:
        raise IntentRegistryError(f"Missing intent registry: {INTENT_REGISTRY_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise IntentRegistryError(f"Invalid JSON in {INTENT_REGISTRY_FILE}: {exc}") from exc
    validate_intent_registry(data)
    try:
        schema_errors = validate_json_schema_file(root, data, INTENT_REGISTRY_SCHEMA_FILE)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise IntentRegistryError(f"Intent registry schema could not be loaded: {exc}") from exc
    if schema_errors:
        raise IntentRegistryError(f"Intent registry schema validation failed: {schema_errors[0]}")
    return data


def validate_intent_registry(data: dict) -> None:
    if not isinstance(data, dict):
        raise IntentRegistryError("Intent registry root must be an object.")
    if data.get("schemaVersion") != 1:
        raise IntentRegistryError("Intent registry schemaVersion must be 1.")
    modes = data.get("modes")
    if not isinstance(modes, list) or not modes:
        raise IntentRegistryError("Intent registry must include a non-empty modes list.")
    invalid_modes = sorted({_trim(str(mode)) for mode in modes} - ALLOWED_MODES)
    if invalid_modes:
        raise IntentRegistryError(f"Intent registry contains invalid modes: {', '.join(invalid_modes)}")
    intents = data.get("intents")
    if not isinstance(intents, list) or not intents:
        raise IntentRegistryError("Intent registry must include a non-empty intents array.")

    seen_commands: set[str] = set()
    required_keys = {
        "command",
        "backendIntent",
        "modes",
        "phrases",
        "description",
        "filesTouched",
        "writeBehavior",
        "requiredArgs",
        "optionalArgs",
        "wrapperPath",
        "readOnlySafe",
        "mutationScope",
        "output",
        "exitCodes",
    }
    for index, intent in enumerate(intents, start=1):
        if not isinstance(intent, dict):
            raise IntentRegistryError(f"Intent entry #{index} must be an object.")
        missing_keys = sorted(required_keys - set(intent.keys()))
        if missing_keys:
            raise IntentRegistryError(f"Intent entry #{index} missing required keys: {', '.join(missing_keys)}")

        command = _trim(str(intent.get("command", "")))
        if not command:
            raise IntentRegistryError(f"Intent entry #{index} has an empty command.")
        if command in seen_commands:
            raise IntentRegistryError(f"Duplicate intent command in registry: {command}")
        seen_commands.add(command)

        backend_intent = _trim(str(intent.get("backendIntent", "")))
        if not backend_intent:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty backendIntent.")

        intent_modes = intent.get("modes")
        if not isinstance(intent_modes, list) or not intent_modes:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty modes list.")
        cleaned_modes = [_trim(str(mode)) for mode in intent_modes]
        invalid_intent_modes = sorted(set(cleaned_modes) - ALLOWED_MODES)
        if invalid_intent_modes:
            raise IntentRegistryError(
                f"Intent '{command}' contains invalid modes: {', '.join(invalid_intent_modes)}"
            )

        phrases = intent.get("phrases")
        if not isinstance(phrases, list) or not phrases:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty phrases list.")
        cleaned_phrases = [_trim(str(phrase)) for phrase in phrases]
        if any(not phrase for phrase in cleaned_phrases):
            raise IntentRegistryError(f"Intent '{command}' contains an empty phrase.")

        description = _trim(str(intent.get("description", "")))
        if not description:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty description.")

        files_touched = _trim(str(intent.get("filesTouched", "")))
        if not files_touched:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty filesTouched field.")

        write_behavior = _trim(str(intent.get("writeBehavior", "")))
        if write_behavior not in ALLOWED_WRITE_BEHAVIORS:
            raise IntentRegistryError(
                f"Intent '{command}' has invalid writeBehavior '{write_behavior}'. "
                f"Expected one of: {', '.join(sorted(ALLOWED_WRITE_BEHAVIORS))}"
            )

        for key in ("requiredArgs", "optionalArgs"):
            values = intent.get(key)
            if not isinstance(values, list):
                raise IntentRegistryError(f"Intent '{command}' must include {key} as an array.")
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise IntentRegistryError(f"Intent '{command}' contains an empty {key} entry.")

        wrapper_path = _trim(str(intent.get("wrapperPath", "")))
        if not wrapper_path:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty wrapperPath.")

        if not isinstance(intent.get("readOnlySafe"), bool):
            raise IntentRegistryError(f"Intent '{command}' must include readOnlySafe as true or false.")

        mutation_scope = intent.get("mutationScope")
        if not isinstance(mutation_scope, list) or not mutation_scope:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty mutationScope array.")
        invalid_scopes = sorted({_trim(str(scope)) for scope in mutation_scope} - ALLOWED_MUTATION_SCOPES)
        if invalid_scopes:
            raise IntentRegistryError(
                f"Intent '{command}' contains invalid mutationScope values: {', '.join(invalid_scopes)}"
            )
        if write_behavior == "no-write" and set(mutation_scope) != {"none"}:
            raise IntentRegistryError(f"Intent '{command}' with no-write behavior must use mutationScope ['none'].")
        if write_behavior == "git" and "git" not in mutation_scope:
            raise IntentRegistryError(f"Intent '{command}' with git behavior must include mutationScope 'git'.")
        if intent["readOnlySafe"] != (write_behavior == "no-write"):
            raise IntentRegistryError(f"Intent '{command}' readOnlySafe must match no-write behavior.")

        output = _trim(str(intent.get("output", "")))
        if not output:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty output field.")

        exit_codes = intent.get("exitCodes")
        if not isinstance(exit_codes, dict) or not exit_codes:
            raise IntentRegistryError(f"Intent '{command}' must include a non-empty exitCodes object.")
        for code, meaning in exit_codes.items():
            if not str(code).isdigit() or not _trim(str(meaning)):
                raise IntentRegistryError(f"Intent '{command}' contains an invalid exitCodes entry.")


def registry_commands(root: Path) -> set[str]:
    data = load_intent_registry(root)
    return {str(intent["command"]).strip() for intent in data["intents"]}


def registry_command_modes(root: Path) -> dict[str, set[str]]:
    data = load_intent_registry(root)
    return {
        _trim(str(intent["command"])): {_trim(str(mode)) for mode in intent["modes"]}
        for intent in data["intents"]
    }


def modes_for_command(root: Path, command: str) -> set[str]:
    return registry_command_modes(root).get(_trim(command), set())


def _render_phrase_family(phrases: list[str]) -> str:
    return ", ".join(f'"{_trim(str(phrase))}"' for phrase in phrases)


def _render_modes(modes: list[str]) -> str:
    return ", ".join(f"`{_trim(str(mode))}`" for mode in modes)


def _render_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(f"`{_trim(str(value))}`" for value in values)


def _render_bool(value: bool) -> str:
    return "`yes`" if value else "`no`"


def render_conversational_intent_table(root: Path) -> str:
    data = load_intent_registry(root)
    lines = [
        "| Natural phrase family | Modes | Action | Read-only safe | Mutation scope | Files touched |",
        "|---|---|---|---|---|---|",
    ]
    for intent in data["intents"]:
        lines.append(
            f"| {_render_phrase_family(intent['phrases'])} | "
            f"{_render_modes(intent['modes'])} | "
            f"{_trim(str(intent['description']))} | "
            f"{_render_bool(bool(intent['readOnlySafe']))} | "
            f"{_render_list(intent['mutationScope'])} | "
            f"{_trim(str(intent['filesTouched']))} |"
        )
    return "\n".join(lines)


def render_commands_intent_table(root: Path) -> str:
    data = load_intent_registry(root)
    lines = [
        "| Command | Modes | Backend intent | Wrapper | Required args | Optional args | Write behavior | Output and exit codes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for intent in data["intents"]:
        exit_codes = ", ".join(
            f"`{_trim(str(code))}` { _trim(str(meaning)) }"
            for code, meaning in intent["exitCodes"].items()
        )
        lines.append(
            f"| `/lab {_trim(str(intent['command']))}` | "
            f"{_render_modes(intent['modes'])} | "
            f"`{_trim(str(intent['backendIntent']))}` | "
            f"`{_trim(str(intent['wrapperPath']))}` | "
            f"{_render_list(intent['requiredArgs'])} | "
            f"{_render_list(intent['optionalArgs'])} | "
            f"`{_trim(str(intent['writeBehavior']))}` | "
            f"{_trim(str(intent['output']))}; {exit_codes} |"
        )
    return "\n".join(lines)


def _replace_generated_section(content: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)
    if start_index < 0 or end_index < 0 or end_index < start_index:
        raise IntentRegistryError(f"Missing or invalid generated section markers: {start_marker} / {end_marker}")
    body_start = start_index + len(start_marker)
    replacement_block = f"{start_marker}\n{replacement}\n{end_marker}"
    return content[:start_index] + replacement_block + content[end_index + len(end_marker) :]


def render_intent_docs_to_memory(root: Path) -> dict[str, str]:
    conversational_path = root / CONVERSATIONAL_DOC
    commands_path = root / COMMANDS_DOC

    conversational_content = _read_text(conversational_path)
    commands_content = _read_text(commands_path)

    rendered_conversational = _replace_generated_section(
        conversational_content,
        CONVERSATIONAL_MARKER_START,
        CONVERSATIONAL_MARKER_END,
        render_conversational_intent_table(root),
    )
    rendered_commands = _replace_generated_section(
        commands_content,
        COMMANDS_MARKER_START,
        COMMANDS_MARKER_END,
        render_commands_intent_table(root),
    )
    return {
        CONVERSATIONAL_DOC: rendered_conversational,
        COMMANDS_DOC: rendered_commands,
    }


def run_render_intent_docs(root: Path) -> int:
    rendered = render_intent_docs_to_memory(root)
    for relative_path, content in rendered.items():
        _write_text(root / relative_path, content)
    print("Rendered harness command docs from harness_commands/intent_registry.json")
    return 0
