from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from template_cli.finalized_contract_tokens import normalize_capabilities
from template_cli.io_helpers import read_text

FINALIZED_CONTRACT_SCHEMA_VERSION = 1


def build_finalized_contract(existing_state: dict, state: dict, hydration_files: list[Path]) -> dict[str, Any]:
    existing = existing_state.get("finalizedContract") if isinstance(existing_state, dict) else None
    if isinstance(existing, dict) and existing:
        return normalize_finalized_contract(existing, state)

    captured = _first_json_contract(hydration_files)
    if captured:
        return normalize_finalized_contract(captured, state)

    return normalize_finalized_contract(_legacy_contract(state, hydration_files), state)


def normalize_finalized_contract(raw_contract: dict[str, Any], state: dict | None = None) -> dict[str, Any]:
    state = state or {}
    contract = dict(raw_contract)
    capabilities = contract.get("capabilities")
    if not isinstance(capabilities, dict):
        capabilities = {}
    normalized = {
        "schemaVersion": FINALIZED_CONTRACT_SCHEMA_VERSION,
        "capabilities": normalize_capabilities(capabilities, state),
        "ownershipBoundaries": _string_list(contract.get("ownershipBoundaries")),
        "invariants": _string_list(contract.get("invariants")),
        "domainConcepts": _string_list(contract.get("domainConcepts")),
        "domainModel": _object_list(contract.get("domainModel"), ["name", "description"]),
        "dataModel": _object_list(contract.get("dataModel"), ["name", "description"]),
        "publicContracts": _object_list(contract.get("publicContracts"), ["name", "contract", "surface", "version"]),
        "versionDomains": _object_list(contract.get("versionDomains"), ["domain", "version", "compatibility"]),
        "milestones": _normalize_milestones(contract.get("milestones")),
        "deferredScope": _string_list(contract.get("deferredScope")),
    }
    return normalized


def _legacy_contract(state: dict, hydration_files: list[Path]) -> dict[str, Any]:
    return {
        "capabilities": {},
        "ownershipBoundaries": _heading_values(hydration_files, ["Ownership Boundaries", "Ownership"]),
        "invariants": _heading_values(hydration_files, ["Invariants", "Core Invariants"]),
        "domainConcepts": _heading_values(hydration_files, ["Domain Concepts"]),
        "domainModel": _heading_values(hydration_files, ["Domain Model"]),
        "dataModel": _heading_values(hydration_files, ["Data Model"]),
        "publicContracts": _heading_values(hydration_files, ["Public Contracts"]),
        "versionDomains": _heading_values(hydration_files, ["Version Domains", "Versioning Domains"]),
        "deferredScope": _heading_values(hydration_files, ["Deferred Scope", "MVP Exclusions", "Out of Scope"]),
        "milestones": [],
    }


def _first_json_contract(files: list[Path]) -> dict[str, Any]:
    for path in files:
        if not path.exists():
            continue
        for block in _json_blocks_after_contract_heading(read_text(path)):
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                contract = data.get("finalizedContract", data)
                if isinstance(contract, dict):
                    return contract
    return {}


def _json_blocks_after_contract_heading(content: str) -> list[str]:
    blocks: list[str] = []
    in_contract_section = False
    in_json_block = False
    current: list[str] = []
    for line in content.splitlines():
        heading = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if heading:
            title = heading.group(1).strip().lower()
            in_contract_section = title in {"finalized contract", "structured finalized contract"}
            in_json_block = False
            current = []
            continue
        if not in_contract_section:
            continue
        if line.strip().startswith("```"):
            if not in_json_block:
                in_json_block = "json" in line.lower()
                current = []
            else:
                blocks.append("\n".join(current))
                in_json_block = False
                current = []
            continue
        if in_json_block:
            current.append(line)
    return blocks


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
            while idx < len(lines) and not re.match(r"^#{1,6}\s+", lines[idx]):
                value = lines[idx].strip()
                if value.startswith("- "):
                    value = value[2:].strip()
                if value:
                    values.append(value)
                idx += 1
    return _unique(values)


def _normalize_milestones(value: Any) -> list[dict[str, Any]]:
    milestones: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return milestones
    for index, item in enumerate(value):
        if isinstance(item, str):
            item = {"id": f"M{index}", "name": item}
        if not isinstance(item, dict):
            continue
        milestone_id = str(item.get("id", "") or f"M{index}").strip()
        name = str(item.get("name", "") or item.get("title", "") or milestone_id).strip()
        if not milestone_id or not name:
            continue
        milestones.append(
            {
                "id": milestone_id,
                "name": name,
                "goal": str(item.get("goal", "") or "").strip(),
                "tasks": _normalize_tasks(item.get("tasks")),
                "gates": _normalize_gates(item.get("gates", item.get("gate"))),
            }
        )
    return milestones


def _normalize_tasks(value: Any) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    if not isinstance(value, list):
        return tasks
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                tasks.append({"area": "", "text": text})
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "") or item.get("task", "") or item.get("description", "") or "").strip()
        if text:
            tasks.append({"area": str(item.get("area", "") or "").strip(), "text": text})
    return tasks


def _normalize_gates(value: Any) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    if not isinstance(value, list):
        value = [value] if value else []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                gates.append({"name": text, "evidence": ""})
            continue
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or item.get("gate", "") or item.get("description", "") or "").strip()
        if name:
            gates.append({"name": name, "evidence": str(item.get("evidence", "") or "").strip()})
    return gates


def _object_list(value: Any, preferred_keys: list[str]) -> list[Any]:
    if not isinstance(value, list):
        return []
    items: list[Any] = []
    for item in value:
        if isinstance(item, dict):
            cleaned = {key: str(item.get(key, "") or "").strip() for key in preferred_keys if str(item.get(key, "") or "").strip()}
            if cleaned:
                items.append(cleaned)
        elif isinstance(item, str) and item.strip():
            key = "name" if "name" in preferred_keys else preferred_keys[0]
            items.append({key: item.strip()})
    return items


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return _unique([str(item).strip() for item in value if str(item).strip()])


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
