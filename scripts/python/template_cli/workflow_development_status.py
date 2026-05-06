from __future__ import annotations

import json
import re
from pathlib import Path

from template_cli.finalize_helpers import existing_state_value
from template_cli.io_helpers import read_text


DEVELOPMENT_GOVERNANCE_DOCS = [
    "docs/GOVERNANCE_INDEX.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
    "docs/FILE_MAP.md",
    "docs/RUNTIME_VERIFICATION_REPORT.md",
    "docs/adr/ADR-0001-record-architecture-decisions.md",
]


def _read_state(root: Path) -> dict:
    state_path = root / "state/project-init.json"
    if not state_path.exists():
        return {}
    try:
        loaded = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _development_active_milestone(root: Path) -> str:
    project_context = root / "docs/PROJECT_CONTEXT.md"
    if project_context.exists():
        lines = read_text(project_context).splitlines()
        for index, line in enumerate(lines):
            if line.strip() == "Active Milestone:":
                for candidate in lines[index + 1 :]:
                    value = candidate.strip()
                    if value and not value.startswith("#"):
                        return value
            match = re.search(r"Active Milestone:\s*(.+)$", line)
            if match and match.group(1).strip():
                return match.group(1).strip()

    readme = root / "README.md"
    if readme.exists():
        for line in read_text(readme).splitlines():
            match = re.search(r"Active Milestone:\s*(.+)$", line)
            if match and match.group(1).strip():
                return match.group(1).strip()

    roadmap = root / "docs/ROADMAP.md"
    if roadmap.exists():
        for line in read_text(roadmap).splitlines():
            if line.startswith("# Milestone ") and "Template" not in line:
                return line.lstrip("#").strip()
    return "not set"


def _roadmap_task_counts(root: Path) -> tuple[int, int]:
    roadmap = root / "docs/ROADMAP.md"
    if not roadmap.exists():
        return 0, 0
    content = read_text(roadmap)
    completed = len(re.findall(r"(?m)^\s*-\s+\[[xX]\]\s+", content))
    open_tasks = len(re.findall(r"(?m)^\s*-\s+\[\s\]\s+", content))
    return open_tasks, completed


def run_development_status(root: Path) -> int:
    state = _read_state(root)
    idea_id = str(state.get("ideaId") or existing_state_value(root, "ideaId") or "").strip()
    state_status = str(state.get("status") or existing_state_value(root, "status") or "").strip()
    project_name = str(state.get("projectName") or "unnamed project").strip()
    validation_command = str((state.get("commands") or {}).get("test") or "").strip()
    present_docs = [relpath for relpath in DEVELOPMENT_GOVERNANCE_DOCS if (root / relpath).exists()]
    missing_docs = [relpath for relpath in DEVELOPMENT_GOVERNANCE_DOCS if not (root / relpath).exists()]
    open_tasks, completed_tasks = _roadmap_task_counts(root)

    print("Mode: development")
    print(f"Project: {project_name}")
    if idea_id:
        if state_status:
            print(f"Canonical state: {state_status} for {idea_id}")
        else:
            print(f"Canonical state: {idea_id}")
    else:
        print("Canonical state: no finalized idea recorded")
    print(f"Active milestone: {_development_active_milestone(root)}")
    print(f"Governance docs: {len(present_docs)}/{len(DEVELOPMENT_GOVERNANCE_DOCS)} present")
    if missing_docs:
        print("Missing governance docs: " + ", ".join(missing_docs))
    print(f"Roadmap tasks: {open_tasks} open, {completed_tasks} complete")
    if validation_command:
        print(f"Validation command: {validation_command}")
    else:
        print("Validation command: not set")
    print("Next step: align changes with docs/ROADMAP.md and record evidence under completed tasks")
    return 0
