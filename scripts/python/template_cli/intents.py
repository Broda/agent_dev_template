from __future__ import annotations

import json
from pathlib import Path


INTENT_REGISTRY_FILE = "brainstorming/intent_registry.json"
CONVERSATIONAL_DOC = "brainstorming/CONVERSATIONAL_MODE.md"
COMMANDS_DOC = "brainstorming/COMMANDS.md"
CONVERSATIONAL_MARKER_START = "<!-- BEGIN GENERATED INTENT MAP -->"
CONVERSATIONAL_MARKER_END = "<!-- END GENERATED INTENT MAP -->"
COMMANDS_MARKER_START = "<!-- BEGIN GENERATED CONVERSATIONAL INTENT MAPPING -->"
COMMANDS_MARKER_END = "<!-- END GENERATED CONVERSATIONAL INTENT MAPPING -->"
ALLOWED_WRITE_BEHAVIORS = {"write", "no-write", "git"}


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
    return data


def validate_intent_registry(data: dict) -> None:
    if not isinstance(data, dict):
        raise IntentRegistryError("Intent registry root must be an object.")
    if data.get("schemaVersion") != 1:
        raise IntentRegistryError("Intent registry schemaVersion must be 1.")
    if data.get("mode") != "brainstorming":
        raise IntentRegistryError("Intent registry mode must be 'brainstorming'.")
    intents = data.get("intents")
    if not isinstance(intents, list) or not intents:
        raise IntentRegistryError("Intent registry must include a non-empty intents array.")

    seen_commands: set[str] = set()
    required_keys = {"command", "backendIntent", "phrases", "description", "filesTouched", "writeBehavior"}
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


def registry_commands(root: Path) -> set[str]:
    data = load_intent_registry(root)
    return {str(intent["command"]).strip() for intent in data["intents"]}


def _render_phrase_family(phrases: list[str]) -> str:
    return ", ".join(f'"{_trim(str(phrase))}"' for phrase in phrases)


def render_conversational_intent_table(root: Path) -> str:
    data = load_intent_registry(root)
    lines = [
        "| Natural phrase family | Action | Files touched |",
        "|---|---|---|",
    ]
    for intent in data["intents"]:
        lines.append(
            f"| {_render_phrase_family(intent['phrases'])} | "
            f"{_trim(str(intent['description']))} | "
            f"{_trim(str(intent['filesTouched']))} |"
        )
    return "\n".join(lines)


def render_commands_intent_table(root: Path) -> str:
    data = load_intent_registry(root)
    lines = [
        "| Conversational phrase family | Backend intent |",
        "|---|---|",
    ]
    for intent in data["intents"]:
        lines.append(
            f"| {_render_phrase_family(intent['phrases'])} | "
            f"`{_trim(str(intent['backendIntent']))}` |"
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
    print("Rendered brainstorming intent docs from brainstorming/intent_registry.json")
    return 0
