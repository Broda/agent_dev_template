from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from template_cli.finalize_context import load_finalize_context
from template_cli.finalize_helpers import (
    STATE_FILE,
    STATE_SCHEMA_VERSION,
    infer_project_type,
    is_placeholder_value,
    latest_session_path,
    summarize_decisions,
    trim,
    unique_values,
)
from template_cli.io_helpers import IDEA_ROW_RE, ValidationResult, parse_markdown_table_rows, read_text, write_text
from template_cli.render_contract import collect_implementation_contract
from template_cli.state_schema import validate_project_state_data
from template_cli.sync import run_lab_sync
from template_cli.workflow_readiness import resolved_finalize_target


STATE_DEFAULTS = {
    "schemaVersion": STATE_SCHEMA_VERSION,
    "status": "draft",
    "finalizedAt": "",
    "ideaId": "",
    "projectName": "",
    "owner": "",
    "purpose": "",
    "projectType": "",
    "techStack": {"language": "", "runtime": "", "framework": "", "packageTool": ""},
    "persistence": "",
    "authentication": "",
    "determinism": "",
    "packaging": "",
    "constraints": "",
    "commands": {"build": "", "run": "", "test": ""},
    "product": {
        "problemStatement": "",
        "targetUsers": "",
        "whyNow": "",
        "expectedValue": "",
        "solutionSummary": "",
        "mvpScope": "",
        "outOfScope": "",
        "assumptions": "",
        "nonGoals": "",
    },
    "governance": {
        "keyDecisions": "",
        "topRisks": "",
        "mitigationPlans": "",
        "contingencies": "",
        "remainingAcceptedRisks": "",
        "latestReviewOutcome": "",
        "latestReviewSession": "",
    },
    "artifacts": {
        "ideaFiles": [],
        "sessionFiles": [],
        "noteReferences": "",
        "summaryExport": "",
        "finalizationSession": "",
        "adrReferences": [],
    },
}
SCALAR_LABELS = {
    "purpose": ["One-sentence objective", "Problem statement", "Value hypothesis", "Summary rationale", "Situation summary"],
    "projectType": ["Project type"],
    "techStack.language": ["Language"],
    "techStack.runtime": ["Runtime"],
    "techStack.framework": ["Framework"],
    "techStack.packageTool": ["Package manager/build tool", "Package tool", "Build tool"],
    "persistence": ["Persistence"],
    "authentication": ["Authentication"],
    "determinism": ["Determinism/correctness sensitivity", "Determinism"],
    "packaging": ["Packaging/distribution planned", "Packaging"],
    "constraints": ["Constraints"],
    "commands.build": ["Build command"],
    "commands.run": ["Run command"],
    "commands.test": ["Test command"],
    "product.problemStatement": ["Problem statement"],
    "product.targetUsers": ["Affected users/personas", "Target users"],
    "product.whyNow": ["Why now"],
    "product.expectedValue": ["Expected value", "Value hypothesis"],
    "product.solutionSummary": ["Solution summary", "Value hypothesis"],
    "product.mvpScope": ["MVP scope"],
    "product.outOfScope": ["Out of scope"],
    "product.assumptions": ["Assumptions"],
    "product.nonGoals": ["Non-goals"],
    "governance.keyDecisions": ["Key decisions", "Chosen option"],
    "governance.topRisks": ["Top risks", "Top risks (link to risk entries)", "Risk statement"],
    "governance.mitigationPlans": ["Mitigation plans", "Preventive mitigation"],
    "governance.contingencies": ["Contingency plan"],
    "governance.remainingAcceptedRisks": ["Remaining accepted risks"],
    "governance.latestReviewOutcome": ["Latest review outcome", "Result"],
}
CONTRACT_KEY_BY_TITLE = {
    "Workspace / Package Layout": "workspaceLayout",
    "Storage Implementation": "storageImplementation",
    "CLI Command Surface": "cliCommandSurface",
    "Domain Statuses And Rules": "domainRules",
    "Schedule / Event Semantics": "scheduleEventSemantics",
    "MVP Exclusions": "mvpExclusions",
    "Test Baseline": "testBaseline",
    "Post-MVP Decisions": "postMvpDecisions",
}
REQUIRED_PATHS = [
    "purpose",
    "projectType",
    "techStack.language",
    "techStack.runtime",
    "commands.build",
    "commands.run",
    "commands.test",
    "product.problemStatement",
    "product.mvpScope",
]
EMPTY_HANDOFF_VALUES = {"", "_none_", "_n/a_", "_none yet_", "pass | conditional-pass | fail"}


def run_lab_handoff(root: Path, *, idea_id: str = "", check: bool = False, no_sync: bool = False) -> int:
    resolved_idea_id = _resolve_handoff_idea_id(root, idea_id)
    context = load_finalize_context(root, resolved_idea_id)
    source_files = _handoff_source_files(root, context)
    original_state = _load_state(root)
    state = _with_defaults(original_state)
    filled: list[str] = []

    _fill(state, "schemaVersion", STATE_SCHEMA_VERSION, filled)
    _fill(state, "status", "draft", filled)
    _fill(state, "ideaId", context.idea_id, filled)
    _fill(state, "projectName", context.project_name, filled)
    _fill(state, "owner", context.owner, filled)

    for dotted_path, labels in SCALAR_LABELS.items():
        _fill(state, dotted_path, _first_label_value(source_files, labels), filled)

    if not _value_at(state, "projectType"):
        _fill(state, "projectType", infer_project_type(context.project_name, _value_at(state, "purpose")), filled)

    decision_summary = summarize_decisions(
        _value_at(state, "projectType"),
        _value_at(state, "persistence"),
        _value_at(state, "authentication"),
        _value_at(state, "determinism"),
        _value_at(state, "packaging"),
    )
    _fill(state, "governance.keyDecisions", decision_summary, filled)
    _fill(state, "governance.latestReviewSession", latest_session_path(context.session_paths), filled)
    _fill(state, "artifacts.noteReferences", context.notes_col if not is_placeholder_value(context.notes_col) else "None recorded", filled)
    _fill(state, "artifacts.summaryExport", context.existing_export_path, filled)
    _fill_list(state, "artifacts.ideaFiles", context.idea_files, filled)
    _fill_list(state, "artifacts.sessionFiles", context.session_paths, filled)
    _fill_list(state, "artifacts.adrReferences", _existing_adr_references(root), filled)

    contract_sections = _fill_implementation_contract(state, source_files, filled)
    missing = [path for path in REQUIRED_PATHS if not _value_at(state, path)]

    _print_summary(context.idea_id, context.idea_files, context.session_paths, filled, missing, contract_sections, check=check)
    if check:
        return 0

    session_path = _write_handoff_session(root, context.idea_id, context.idea_files, context.session_paths, filled, missing, contract_sections)
    _fill_list(state, "artifacts.sessionFiles", context.session_paths + [session_path], filled)
    schema_result = ValidationResult()
    validate_project_state_data(root, schema_result, state, variant="draft")
    if schema_result.failures:
        raise SystemExit("\n".join(schema_result.failures))
    write_text(root / STATE_FILE, json.dumps(state, indent=2) + "\n")
    sync_code = run_lab_sync(
        root,
        message=f"handoff {context.idea_id}",
        quiet=True,
        no_warn_push_failure=True,
        files=[STATE_FILE, session_path],
    ) if not no_sync else 0
    if sync_code not in {0, 2}:
        raise SystemExit(sync_code)
    print(f"Handoff state updated: {STATE_FILE}")
    print(f"Handoff session log: {session_path}")
    return 0


def _resolve_handoff_idea_id(root: Path, idea_id: str) -> str:
    if idea_id:
        return idea_id
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    row, source = resolved_finalize_target(root, active)
    if row is not None:
        return row["idea_id"]
    if source == "ambiguous":
        raise SystemExit("Handoff target is ambiguous. Rerun with ./scripts/lab handoff --idea-id <idea-id>.")
    raise SystemExit("No handoff target found. Capture and activate an idea first.")


def _handoff_source_files(root: Path, context) -> list[Path]:
    ordered: list[str] = []
    for rel_path in sorted(context.session_paths, reverse=True):
        if rel_path not in ordered:
            ordered.append(rel_path)
    if context.existing_export_path and context.existing_export_path not in ordered:
        ordered.append(context.existing_export_path)
    for rel_path in context.idea_files:
        if rel_path not in ordered:
            ordered.append(rel_path)
    return [root / rel_path for rel_path in ordered]


def _load_state(root: Path) -> dict:
    try:
        data = json.loads(read_text(root / STATE_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _with_defaults(state: dict) -> dict:
    merged = json.loads(json.dumps(STATE_DEFAULTS))
    _merge_dicts(merged, state)
    return merged


def _merge_dicts(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value


def _first_label_value(files: list[Path], labels: list[str]) -> str:
    for label in labels:
        value = _first_value_for_label(files, label)
        if value:
            return value
    return ""


def _first_value_for_label(files: list[Path], label: str) -> str:
    prefix = f"- {label}:"
    for file_path in files:
        if not file_path.exists():
            continue
        for line in read_text(file_path).splitlines():
            stripped = line.strip()
            if stripped.startswith(prefix):
                value = trim(stripped[len(prefix):])
                if not _is_empty_handoff_value(value):
                    return value
    return ""


def _is_empty_handoff_value(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    return trim(value) in EMPTY_HANDOFF_VALUES


def _fill(state: dict, dotted_path: str, value: object, filled: list[str]) -> None:
    if _is_empty_handoff_value(value):
        return
    if _value_at(state, dotted_path):
        return
    _set_value(state, dotted_path, value)
    filled.append(dotted_path)


def _fill_list(state: dict, dotted_path: str, values: list[str], filled: list[str]) -> None:
    existing = _raw_value_at(state, dotted_path)
    merged = unique_values((existing if isinstance(existing, list) else []) + values)
    if merged != existing:
        _set_value(state, dotted_path, merged)
        filled.append(dotted_path)


def _value_at(state: dict, dotted_path: str) -> str:
    value = _raw_value_at(state, dotted_path)
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if str(item).strip())
    if isinstance(value, dict):
        return ""
    text = "" if value is None else str(value).strip()
    return "" if _is_empty_handoff_value(text) else text


def _raw_value_at(state: dict, dotted_path: str) -> object:
    cur: object = state
    for part in dotted_path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _set_value(state: dict, dotted_path: str, value: object) -> None:
    cur = state
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def _fill_implementation_contract(state: dict, hydration_files: list[Path], filled: list[str]) -> list[tuple[str, list[str]]]:
    sections = collect_implementation_contract(state, hydration_files)
    if not sections:
        return []
    implementation = state.setdefault("implementation", {})
    for title, details in sections:
        key = CONTRACT_KEY_BY_TITLE.get(title)
        if not key or implementation.get(key):
            continue
        implementation[key] = details
        filled.append(f"implementation.{key}")
    return sections


def _existing_adr_references(root: Path) -> list[str]:
    candidates = [
        "docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        "brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
    ]
    return [candidate for candidate in candidates if (root / candidate).exists()]


def _write_handoff_session(
    root: Path,
    idea_id: str,
    idea_files: list[str],
    session_paths: list[str],
    filled: list[str],
    missing: list[str],
    contract_sections: list[tuple[str, list[str]]],
) -> str:
    session_path = f"sessions/{date.today().isoformat()}_HANDOFF_SESSION_{idea_id}.md"
    lines = _summary_lines(idea_id, idea_files, session_paths, filled, missing, contract_sections)
    write_text(root / session_path, "\n".join(["# Handoff Session", "", *lines]) + "\n")
    return session_path


def _print_summary(
    idea_id: str,
    idea_files: list[str],
    session_paths: list[str],
    filled: list[str],
    missing: list[str],
    contract_sections: list[tuple[str, list[str]]],
    *,
    check: bool,
) -> None:
    print("Handoff check" if check else "Handoff compile")
    for line in _summary_lines(idea_id, idea_files, session_paths, filled, missing, contract_sections):
        print(line)


def _summary_lines(
    idea_id: str,
    idea_files: list[str],
    session_paths: list[str],
    filled: list[str],
    missing: list[str],
    contract_sections: list[tuple[str, list[str]]],
) -> list[str]:
    lines = [
        f"- Idea ID: {idea_id}",
        "- Source idea files: " + (", ".join(idea_files) if idea_files else "none"),
        "- Source session files: " + (", ".join(session_paths) if session_paths else "none"),
        "- Filled fields: " + (", ".join(filled) if filled else "none"),
        "- Missing fields: " + (", ".join(missing) if missing else "none"),
        "- Implementation contract sections: "
        + (", ".join(title for title, _ in contract_sections) if contract_sections else "none"),
    ]
    return lines
