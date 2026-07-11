from __future__ import annotations

import re
from pathlib import Path

from template_cli.io_helpers import read_text
from template_cli.render_capabilities import contract_milestones, finalized_contract
from template_cli.render_helpers import _state_list, _state_value

CONTRACT_SECTIONS = [
    (
        "Ownership Boundaries",
        ["finalizedContract.ownershipBoundaries"],
        ["Ownership boundaries", "Ownership"],
    ),
    (
        "Invariants",
        ["finalizedContract.invariants"],
        ["Invariants", "Core invariants"],
    ),
    (
        "Domain And Data Model",
        ["finalizedContract.domainModel", "finalizedContract.dataModel"],
        ["Domain model", "Data model"],
    ),
    (
        "Public Contracts",
        ["finalizedContract.publicContracts"],
        ["Public contracts"],
    ),
    (
        "Version Domains",
        ["finalizedContract.versionDomains"],
        ["Version domains", "Versioning domains"],
    ),
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
    (
        "Deferred Scope",
        ["finalizedContract.deferredScope"],
        ["Deferred scope"],
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
        if path.startswith("finalizedContract."):
            continue
        listed = _state_list(state, path)
        if listed:
            values.extend(listed)
            continue
        value = _state_value(state, path)
        values.extend(_split_detail_value(value))
    return values


def _value_at(state: dict, path: str) -> object:
    cur: object = state
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _structured_details(value: object) -> list[str]:
    if isinstance(value, list):
        details: list[str] = []
        for item in value:
            details.extend(_structured_details(item))
        return details
    if isinstance(value, dict):
        preferred = [
            "name",
            "contract",
            "boundary",
            "invariant",
            "format",
            "domain",
            "description",
            "summary",
            "owner",
        ]
        parts = [str(value.get(key, "") or "").strip() for key in preferred]
        rendered = " - ".join(part for part in parts if part)
        if rendered:
            return [rendered]
        return [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
    if isinstance(value, str):
        return _split_detail_value(value)
    return []


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
                    values.extend(_split_detail_value(stripped[len(prefix) :]))
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
        structured = []
        for path in state_paths:
            if path.startswith("finalizedContract."):
                structured.extend(_structured_details(_value_at(state, path)))
        details = _unique(
            structured
            + _state_details(state, state_paths)
            + _line_label_values(hydration_files, labels)
            + _heading_values(hydration_files, labels)
        )
        if details:
            sections.append((title, details))
    milestone_details = _milestone_details(state)
    if milestone_details:
        sections.append(("Ordered Milestones", milestone_details))
    return sections


def _milestone_details(state: dict) -> list[str]:
    if not finalized_contract(state):
        return []
    details: list[str] = []
    for milestone in contract_milestones(state):
        goal = milestone.get("goal", "")
        suffix = f" - {goal}" if goal else ""
        details.append(f"{milestone['id']}: {milestone['name']}{suffix}")
    return details


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
