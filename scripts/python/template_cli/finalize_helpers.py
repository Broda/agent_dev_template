from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from template_cli.io_helpers import clean_backticks, parse_markdown_table_rows, path_exists, read_text, write_text


STATE_FILE = "state/project-init.json"
STATE_SCHEMA_VERSION = 2


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def trim(value: str | None) -> str:
    return (value or "").strip()


def join_by(sep: str, values: list[str]) -> str:
    return sep.join(v for v in values if trim(v))


def join_lines(values: list[str]) -> str:
    return "\n".join(v for v in values if trim(v))


def replace_line_prefix(path: Path, prefix: str, value: str) -> None:
    normalized = value.replace("\n", " ").replace("\r", " ")
    lines = read_text(path).splitlines()
    updated = []
    for line in lines:
        if line.startswith(prefix):
            updated.append(f"{prefix} {normalized}".rstrip())
        else:
            updated.append(line)
    write_text(path, "\n".join(updated) + ("\n" if read_text(path).endswith("\n") else ""))


def existing_state_value(root: Path, dotted_path: str) -> str:
    state_path = root / STATE_FILE
    if not state_path.exists():
        return ""
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return ""
    cur = state
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return ""
        cur = cur[part]
    return "" if cur is None else str(cur)


def infer_project_type(project_name: str, objective: str) -> str:
    text = f"{project_name} {objective}".lower()
    if any(token in text for token in ("game", "gameplay", "player", "playable")):
        return "Game"
    if "cli" in text or "command line" in text:
        return "CLI"
    if "desktop" in text or "electron" in text:
        return "Desktop"
    if any(token in text for token in ("web", "frontend", "browser")):
        return "Web App"
    if any(token in text for token in ("api", "service", "backend")):
        return "API"
    if any(token in text for token in ("library", "sdk", "package")):
        return "Library"
    return ""


def prompt_eof_error(field: str) -> None:
    raise SystemExit(
        f"Cannot finalize non-interactively without a value for '{field}'.\n"
        "Populate state/project-init.json first or rerun with stdin/TTY answers."
    )


def ask_non_empty(prompt: str, current: str = "") -> str:
    current = trim(current)
    if current:
        try:
            response = input(f"{prompt} [{current}]: ")
        except EOFError:
            return current
        response = trim(response)
        return response or current

    while True:
        try:
            response = input(f"{prompt}: ")
        except EOFError:
            prompt_eof_error(prompt)
        response = trim(response)
        if response:
            return response


def choose_project_type(current: str) -> str:
    options = ["Game", "CLI", "Desktop", "Web App", "API", "Library"]
    eprint("Project type options:")
    for idx, option in enumerate(options, start=1):
        eprint(f"{idx}) {option}")
    if current:
        eprint(f"Detected: {current}")

    while True:
        try:
            response = input(
                f"Select project type [1-{len(options)}]{f' (current: {current})' if current else ''}: "
            )
        except EOFError:
            if current:
                return current
            prompt_eof_error("project type")
        response = trim(response)
        if not response and current:
            return current
        if response.isdigit():
            idx = int(response)
            if 1 <= idx <= len(options):
                return options[idx - 1]


def choose_from_list(prompt: str, current: str, options: list[str]) -> str:
    for idx, option in enumerate(options, start=1):
        eprint(f"{idx}) {option}")

    while True:
        try:
            response = input(
                f"{prompt} [1-{len(options)}]{f' (current: {current})' if current else ''}: "
            )
        except EOFError:
            if current:
                return current
            prompt_eof_error(prompt)
        response = trim(response)
        if not response and current:
            return current
        if response.isdigit():
            idx = int(response)
            if 1 <= idx <= len(options):
                return options[idx - 1]


def choose_idea_to_finalize(candidates: list[tuple[str, str, str]]) -> str:
    eprint("Multiple ideas are available to finalize:")
    for idx, (idea_id, title, status) in enumerate(candidates, start=1):
        display_title = title or idea_id
        eprint(f"{idx}) {display_title} [{idea_id}] ({status})")

    while True:
        try:
            response = input(f"Select idea to finalize [1-{len(candidates)}]: ")
        except EOFError:
            raise SystemExit(
                "Cannot infer which idea to finalize non-interactively.\n"
                "Rerun with stdin/TTY answers or pass --idea-id explicitly."
            )
        response = trim(response)
        if response.isdigit():
            idx = int(response)
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1][0]


def extract_label_value(path: Path, label: str) -> str:
    prefix = f"- {label}:"
    if not path.exists():
        return ""
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return trim(line[len(prefix):])
    return ""


def is_placeholder_value(value: str) -> bool:
    value = trim(value)
    return value in {"", "None", "_none_", "_n/a_", "_none yet_", "pass | conditional-pass | fail"}


def first_value_for_label(files: list[Path], label: str) -> str:
    for file_path in files:
        value = trim(extract_label_value(file_path, label))
        if value and not is_placeholder_value(value):
            return value
    return ""


def latest_session_path(session_paths: list[str]) -> str:
    return max(session_paths) if session_paths else ""


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = trim(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def split_linkish_values(value: str, prefixes: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for prefix in prefixes:
        matches.extend(re.findall(rf"{re.escape(prefix)}/[^`,\s]+\.md", value))
    return unique_values(matches)


def summarize_decisions(project_type: str, persistence: str, authentication: str, determinism: str, packaging: str) -> str:
    parts = []
    if project_type:
        parts.append(f"Project type: {project_type}.")
    if persistence:
        parts.append(f"Persistence: {persistence}.")
    if authentication:
        parts.append(f"Authentication: {authentication}.")
    if determinism:
        parts.append(f"Correctness sensitivity: {determinism}.")
    if packaging:
        parts.append(f"Packaging: {packaging}.")
    return " ".join(parts).strip()


def summarize_dependencies(language: str, runtime: str, framework: str, package_tool: str) -> str:
    return f"Language: {language}; Runtime: {runtime}; Framework: {framework or 'None'}; Tooling: {package_tool or 'None'}"


def files_containing(root: Path, subdir: str, needle: str) -> list[str]:
    base = root / subdir
    if not base.exists():
        return []
    matches: list[str] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        try:
            if needle in read_text(path):
                matches.append(path.relative_to(root).as_posix())
        except UnicodeDecodeError:
            continue
    return matches
