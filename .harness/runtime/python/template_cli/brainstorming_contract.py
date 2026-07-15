from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from template_cli.io_helpers import read_text

CONTRACT_SCHEMA_VERSION = 1


def compile_brainstorming_contract(
    root: Path,
    session_paths: list[str],
    note_paths: list[str],
) -> dict[str, Any]:
    decisions: list[dict[str, str]] = []
    risks: list[dict[str, str]] = []
    session_sections: list[dict[str, Any]] = []
    for relative_path in sorted(set(session_paths)):
        path = root / relative_path
        if not path.exists():
            continue
        content = read_text(path)
        decisions.extend(_records(content, "Decision", relative_path, _decision_record))
        risks.extend(_records(content, "Risk", relative_path, _risk_record))
        for section in ["Current Focus", "Exploration Path Notes"]:
            session_sections.extend(_session_section_records(content, section, relative_path))

    related_notes: list[dict[str, Any]] = []
    for relative_path in sorted(set(note_paths)):
        path = root / relative_path
        if not path.exists():
            continue
        content = read_text(path)
        related_notes.append(
            {
                "id": _label_value(content, "Note ID"),
                "title": _label_value(content, "Title") or path.stem,
                "path": relative_path,
                "sourceContext": _label_value(content, "Source Context"),
                "tags": _label_value(content, "Tags"),
                "capturedInformation": _section_items(content, "Captured Information"),
                "keyFacts": _section_items(content, "Key Facts / Constraints"),
                "openQuestions": _section_items(content, "Open Questions / Follow-ups"),
                "links": _section_items(content, "Links"),
            }
        )

    return {
        "schemaVersion": CONTRACT_SCHEMA_VERSION,
        "decisions": decisions,
        "risks": risks,
        "relatedNotes": related_notes,
        "sessionSections": session_sections,
    }


def has_substantive_brainstorming_contract(contract: object) -> bool:
    if not isinstance(contract, dict):
        return False
    return any(
        isinstance(contract.get(key), list) and contract[key]
        for key in ["decisions", "risks", "relatedNotes", "sessionSections"]
    )


def semantic_contract_issues(state: dict[str, Any]) -> list[str]:
    contract = state.get("brainstormingContract")
    if not has_substantive_brainstorming_contract(contract):
        return []
    assert isinstance(contract, dict)
    issues: list[str] = []
    for index, decision in enumerate(contract.get("decisions", []), start=1):
        if not isinstance(decision, dict):
            issues.append(f"Decision record {index} is not a structured object.")
            continue
        record_id = str(decision.get("id", "") or f"record {index}")
        missing = [
            label
            for label, key in [("Chosen option", "chosenOption"), ("Rationale", "rationale")]
            if not str(decision.get(key, "") or "").strip()
        ]
        if missing:
            issues.append(f"Decision {record_id} is missing: {', '.join(missing)}.")
    for index, risk in enumerate(contract.get("risks", []), start=1):
        if not isinstance(risk, dict):
            issues.append(f"Risk record {index} is not a structured object.")
            continue
        record_id = str(risk.get("id", "") or f"record {index}")
        missing = [
            label
            for label, key in [
                ("Risk statement", "statement"),
                ("Preventive mitigation", "mitigation"),
                ("Contingency plan", "contingency"),
            ]
            if not str(risk.get(key, "") or "").strip()
        ]
        if missing:
            issues.append(f"Risk {record_id} is missing: {', '.join(missing)}.")
    for index, note in enumerate(contract.get("relatedNotes", []), start=1):
        if not isinstance(note, dict) or not str(note.get("path", "") or "").strip():
            issues.append(f"Related note record {index} is missing its source path.")
    for index, section in enumerate(contract.get("sessionSections", []), start=1):
        if not isinstance(section, dict) or not str(section.get("source", "") or "").strip():
            issues.append(f"Session section record {index} is missing its source path.")
    return issues


def semantic_contract_failure(idea_id: str, issues: list[str]) -> str:
    lines = [
        "Cannot continue because native brainstorming records are semantically incomplete.",
        f"Idea ID: {idea_id}",
        "Contract issues:",
        *(f"- {issue}" for issue in issues),
        "Next step: complete the cited Decision/Risk fields in the source session",
        f"and rerun ./scripts/lab handoff --idea-id {idea_id} --check.",
    ]
    return "\n".join(lines)


def _records(content: str, kind: str, source: str, builder: Any) -> list[dict[str, str]]:
    lines = content.splitlines()
    heading_re = re.compile(rf"^###\s+{re.escape(kind)}:\s*(.*?)\s*$", re.IGNORECASE)
    records: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        match = heading_re.match(lines[index].strip())
        if not match:
            index += 1
            continue
        heading_id = match.group(1).strip()
        index += 1
        block: list[str] = []
        while index < len(lines) and not re.match(r"^#{1,3}\s+", lines[index].strip()):
            block.append(lines[index])
            index += 1
        records.append(builder("\n".join(block), heading_id, source))
    return records


def _decision_record(block: str, heading_id: str, source: str) -> dict[str, str]:
    return {
        "id": _label_value(block, "Decision ID") or heading_id,
        "level": _label_value(block, "Decision level"),
        "situation": _label_value(block, "Situation summary"),
        "constraints": _label_value(block, "Constraints"),
        "chosenOption": _label_value(block, "Chosen option"),
        "rationale": _label_value(block, "Rationale"),
        "source": source,
    }


def _risk_record(block: str, heading_id: str, source: str) -> dict[str, str]:
    return {
        "id": _label_value(block, "Risk ID") or heading_id,
        "statement": _label_value(block, "Risk statement"),
        "probability": _label_value(block, "Probability"),
        "impact": _label_value(block, "Impact"),
        "mitigation": _label_value(block, "Preventive mitigation"),
        "contingency": _label_value(block, "Contingency plan"),
        "source": source,
    }


def _session_section_records(content: str, section: str, source: str) -> list[dict[str, Any]]:
    groups = _section_groups(content, section)
    return [
        {"section": section, "heading": heading, "items": items, "source": source} for heading, items in groups if items
    ]


def _section_items(content: str, section: str) -> list[str]:
    return [item for _, items in _section_groups(content, section) for item in items]


def _section_groups(content: str, section: str) -> list[tuple[str, list[str]]]:
    lines = content.splitlines()
    section_re = re.compile(rf"^##\s+{re.escape(section)}\s*$", re.IGNORECASE)
    index = next((idx for idx, line in enumerate(lines) if section_re.match(line.strip())), -1)
    if index < 0:
        return []
    groups: list[tuple[str, list[str]]] = []
    heading = ""
    body: list[str] = []
    index += 1
    while index < len(lines):
        stripped = lines[index].strip()
        if re.match(r"^#{1,2}\s+", stripped):
            break
        subheading = re.match(r"^###\s+(.+?)\s*$", stripped)
        if subheading:
            _append_group(groups, heading, body)
            heading = subheading.group(1).strip()
            body = []
        else:
            body.append(lines[index])
        index += 1
    _append_group(groups, heading, body)
    return groups


def _append_group(groups: list[tuple[str, list[str]]], heading: str, lines: list[str]) -> None:
    items = _content_items(lines)
    if items:
        groups.append((heading, items))


def _content_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped in {"-", "*", "+"}:
            continue
        bullet = re.match(r"^[-*+]\s+(.+?)\s*$", stripped)
        if bullet:
            items.append(bullet.group(1).strip())
        elif items:
            items[-1] = f"{items[-1]} {stripped}"
        else:
            items.append(stripped)
    placeholders = {
        "none recorded.",
        "none recorded",
        "summary pending: fill in captured research details.",
    }
    return [item for item in items if item.casefold() not in placeholders]


def _label_value(content: str, label: str) -> str:
    prefix = f"- {label}:"
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return ""
