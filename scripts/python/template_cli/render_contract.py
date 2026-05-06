from __future__ import annotations

import re
from pathlib import Path

from template_cli.render_helpers import _state_list, _state_value
from template_cli.io_helpers import read_text


CONTRACT_SECTIONS = [
    (
        "Workspace / Package Layout",
        ["implementation.workspaceCrates", "implementation.workspaceLayout", "mvpContract.workspaceCrates"],
        ["Workspace/crate layout", "Workspace layout", "Package layout"],
    ),
    (
        "Storage Implementation",
        ["implementation.storage", "implementation.storageImplementation", "mvpContract.storageImplementation"],
        ["Storage implementation", "Persistence implementation", "Database implementation"],
    ),
    (
        "CLI Command Surface",
        ["implementation.cliCommandSurface", "implementation.commands", "mvpContract.cliCommandSurface"],
        ["CLI command surface", "Command surface", "Commands"],
    ),
    (
        "Domain Statuses And Rules",
        ["implementation.domainStatuses", "implementation.domainRules", "mvpContract.domainStatuses"],
        ["Domain statuses", "Domain rules", "Statuses and rules"],
    ),
    (
        "Schedule / Event Semantics",
        ["implementation.scheduleEventSemantics", "mvpContract.scheduleEventSemantics"],
        ["Schedule/event semantics", "Schedule semantics", "Event semantics"],
    ),
    (
        "MVP Exclusions",
        ["implementation.mvpExclusions", "mvpContract.mvpExclusions", "product.nonGoals", "product.outOfScope"],
        ["MVP exclusions", "Out of scope", "Non-goals"],
    ),
    (
        "Test Baseline",
        ["implementation.testBaseline", "mvpContract.testBaseline"],
        ["Test baseline", "Testing baseline", "Verification baseline"],
    ),
    (
        "Post-MVP Decisions",
        ["implementation.postMvpDecisions", "mvpContract.postMvpDecisions"],
        ["Post-MVP decisions", "Deferred decisions", "Later decisions"],
    ),
]


def _split_detail_value(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    lines = [line.strip(" -\t") for line in value.splitlines() if line.strip(" -\t")]
    if len(lines) > 1:
        return lines
    return [value]


def _state_details(state: dict, paths: list[str]) -> list[str]:
    values: list[str] = []
    for path in paths:
        listed = _state_list(state, path)
        if listed:
            values.extend(listed)
            continue
        value = _state_value(state, path)
        values.extend(_split_detail_value(value))
    return values


def _line_label_values(files: list[Path], labels: list[str]) -> list[str]:
    values: list[str] = []
    prefixes = [(label, f"- {label}:") for label in labels]
    for path in files:
        if not path.exists():
            continue
        for line in read_text(path).splitlines():
            stripped = line.strip()
            for _, prefix in prefixes:
                if stripped.startswith(prefix):
                    values.extend(_split_detail_value(stripped[len(prefix):]))
    return values


def _heading_values(files: list[Path], labels: list[str]) -> list[str]:
    values: list[str] = []
    normalized_labels = {label.lower().strip() for label in labels}
    for path in files:
        if not path.exists():
            continue
        lines = read_text(path).splitlines()
        idx = 0
        while idx < len(lines):
            heading = re.match(r"^#{2,6}\s+(.+?)\s*$", lines[idx])
            if not heading or heading.group(1).strip().lower() not in normalized_labels:
                idx += 1
                continue
            idx += 1
            collected: list[str] = []
            while idx < len(lines) and not re.match(r"^#{1,6}\s+", lines[idx]):
                stripped = lines[idx].strip()
                if stripped.startswith("- "):
                    collected.append(stripped[2:].strip())
                elif stripped and collected:
                    collected[-1] = f"{collected[-1]} {stripped}"
                elif stripped:
                    collected.append(stripped)
                idx += 1
            values.extend(collected)
    return values


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def collect_implementation_contract(state: dict, hydration_files: list[Path]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    for title, state_paths, labels in CONTRACT_SECTIONS:
        details = _unique(
            _state_details(state, state_paths)
            + _line_label_values(hydration_files, labels)
            + _heading_values(hydration_files, labels)
        )
        if details:
            sections.append((title, details))
    return sections


def format_contract_sections(sections: list[tuple[str, list[str]]], *, heading_level: int = 2) -> str:
    if not sections:
        return "No detailed implementation contract was captured in the finalized state or session artifacts."
    heading_prefix = "#" * heading_level
    rendered: list[str] = []
    for title, details in sections:
        rendered.append(f"{heading_prefix} {title}")
        rendered.append("")
        for detail in details:
            if re.fullmatch(r"[^`]*<[^>]+>[^`]*", detail):
                detail = f"`{detail}`"
            rendered.append(f"- {detail}")
        rendered.append("")
    return "\n".join(rendered).rstrip()
