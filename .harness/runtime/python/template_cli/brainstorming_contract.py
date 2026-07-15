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
    for relative_path in sorted(set(session_paths)):
        path = root / relative_path
        if not path.exists():
            continue
        content = read_text(path)
        decisions.extend(_records(content, "Decision", relative_path, _decision_record))
        risks.extend(_records(content, "Risk", relative_path, _risk_record))

    related_notes: list[dict[str, str]] = []
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
            }
        )

    return {
        "schemaVersion": CONTRACT_SCHEMA_VERSION,
        "decisions": decisions,
        "risks": risks,
        "relatedNotes": related_notes,
    }


def has_substantive_brainstorming_contract(contract: object) -> bool:
    if not isinstance(contract, dict):
        return False
    return any(isinstance(contract.get(key), list) and contract[key] for key in ["decisions", "risks", "relatedNotes"])


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


def _label_value(content: str, label: str) -> str:
    prefix = f"- {label}:"
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return ""
