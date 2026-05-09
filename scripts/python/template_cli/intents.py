from __future__ import annotations

from pathlib import Path

from template_cli.intent_registry import (
    COMMANDS_DOC,
    COMMANDS_MARKER_END,
    COMMANDS_MARKER_START,
    CONVERSATIONAL_DOC,
    CONVERSATIONAL_MARKER_END,
    CONVERSATIONAL_MARKER_START,
    INTENT_REGISTRY_FILE,
    INTENT_REGISTRY_SCHEMA_FILE,
    ALLOWED_MODES,
    ALLOWED_MUTATION_SCOPES,
    ALLOWED_WRITE_BEHAVIORS,
    IntentRegistryError,
    _read_text,
    _trim,
    _write_text,
    load_intent_registry,
    modes_for_command,
    registry_command_modes,
    registry_commands,
    validate_intent_registry,
)


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
