from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text, replace_literal, write_text
from template_cli.state_schema import validate_project_state_data


MILESTONE_NAME = "Milestone 0 — Foundation"
STATE_FILE = "state/project-init.json"
DEFAULT_CI_POLICY = (
    "Generated GitHub Actions CI is included as a baseline guardrail; local build, "
    "test, and manual verification remain authoritative."
)
RENDERED_ARTIFACTS = [
    ("README.md", "Python renderer", "Regenerate from state"),
    ("CHANGELOG.md", "Base template plus renderer insert", "Human-editable after initialization"),
    (".gitignore", "Stack-specific gitignore template", "Regenerate when stack or persistence changes"),
    (".github/workflows/ci.yml", "Python renderer", "Regenerate from state commands"),
    ("docs/PROJECT_CONTEXT.md", "Python renderer", "Regenerate from state"),
    ("docs/ROADMAP.md", "Python renderer", "Regenerate from state, then track milestone evidence manually"),
    ("docs/ARCHITECTURE.md", "Python renderer", "Regenerate from state, then update through ADR-backed changes"),
    ("docs/FILE_MAP.md", "Base template", "Human-editable as implementation files are added"),
    ("docs/GOVERNANCE_INDEX.md", "Base template", "Human-editable as governance records grow"),
    ("docs/VERSIONING_AND_RELEASE_POLICY.md", "Base template", "Human-editable by policy decision"),
    ("docs/SECURITY_POLICY.md", "Base template", "Human-editable by policy decision"),
    ("docs/RUNTIME_VERIFICATION_REPORT.md", "Base template plus command replacement", "Human-editable evidence log"),
    ("docs/MIGRATION_POLICY.md", "Base template when persistence is enabled", "Human-editable by policy decision"),
    ("docs/adr/ADR-0001-record-architecture-decisions.md", "Python renderer", "Regenerate from state or supersede with a later ADR"),
    ("docs/adr/ADR-TEMPLATE.md", "Base template", "Human-editable template for future ADRs"),
]


class RenderError(Exception):
    pass


def _trim(value: str | None) -> str:
    return (value or "").strip()


def _load_state(root: Path) -> dict:
    state_path = root / STATE_FILE
    try:
        state = json.loads(read_text(state_path))
    except FileNotFoundError as exc:
        raise RenderError(f"Missing state file: {STATE_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise RenderError(f"Invalid JSON in {STATE_FILE}: {exc}") from exc
    if not isinstance(state, dict):
        raise RenderError("state/project-init.json root must be an object.")
    schema_result = ValidationResult()
    validate_project_state_data(root, schema_result, state, variant="finalized")
    if schema_result.failures:
        raise RenderError(schema_result.failures[0])
    return state


def _extract_value(state: dict, path: str) -> str:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise RenderError(f"Missing required value in {STATE_FILE}: {path}")
        cur = cur[part]
    if cur is None or not str(cur).strip():
        raise RenderError(f"Missing required value in {STATE_FILE}: {path}")
    return str(cur)


def _state_value(state: dict, path: str, default: str = "") -> str:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    if cur is None:
        return default
    value = str(cur).strip()
    return value or default


def _state_list(state: dict, path: str) -> list[str]:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return []
        cur = cur[part]
    if not isinstance(cur, list):
        return []
    values: list[str] = []
    seen: set[str] = set()
    for item in cur:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def _copy_base(root: Path, src: str, dst: str) -> None:
    src_path = root / src
    dst_path = root / dst
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_path, dst_path)


def _copy_base_if_missing(root: Path, src: str, dst: str) -> None:
    dst_path = root / dst
    if dst_path.exists():
        return
    _copy_base(root, src, dst)


def _write_rendered_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, content)


def _render_artifact_source_table(include_migration_policy: bool) -> str:
    rows = [
        artifact
        for artifact in RENDERED_ARTIFACTS
        if include_migration_policy or artifact[0] != "docs/MIGRATION_POLICY.md"
    ]
    lines = [
        "| Artifact | Render Source | Edit Policy |",
        "|---|---|---|",
    ]
    lines.extend(f"| `{path}` | {source} | {policy} |" for path, source, policy in rows)
    return "\n".join(lines)


def _replace_file_literals(path: Path, replacements: list[tuple[str, str]]) -> None:
    content = read_text(path)
    for old, new in replacements:
        content = replace_literal(content, old, new)
    write_text(path, content)


def _append_unique_lines(path: Path, lines_to_add: list[str]) -> None:
    content = read_text(path)
    existing_lines = content.splitlines()
    additions = [line for line in lines_to_add if line not in existing_lines]
    if not additions:
        return
    if content and not content.endswith("\n"):
        content += "\n"
    if content and not content.endswith("\n\n"):
        content += "\n"
    content += "\n".join(additions) + "\n"
    write_text(path, content)


def _replace_readme_command_block(content: str, label: str, value: str) -> str:
    pattern = re.compile(rf"{re.escape(label)}:\r?\n\r?\n\s*<command>")
    return pattern.sub(f"{label}:\n\n    {value}", content)


def _extract_label_value(path: Path, label: str) -> str:
    prefix = f"- {label}:"
    if not path.exists():
        return ""
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return _trim(line[len(prefix):])
    return ""


def _related_hydration_files(root: Path, idea_id: str) -> list[Path]:
    files: list[Path] = []
    for subdir in ["exports", "ideas", "sessions"]:
        base = root / subdir
        if not base.exists():
            continue
        for path in sorted(base.rglob(f"*{idea_id}*.md"), reverse=True):
            if path.is_file():
                files.append(path)
    return files


def _related_hydration_files_from_state(root: Path, state: dict, idea_id: str) -> list[Path]:
    files = _related_hydration_files(root, idea_id)
    for relative_path in _state_list(state, "artifacts.ideaFiles") + _state_list(state, "artifacts.sessionFiles"):
        path = root / relative_path
        if path.is_file() and path not in files:
            files.append(path)
    summary_export = _state_value(state, "artifacts.summaryExport")
    if summary_export:
        export_path = root / summary_export
        if export_path.is_file() and export_path not in files:
            files.append(export_path)
    return files


def _first_value_for_label(files: list[Path], labels: list[str]) -> str:
    for label in labels:
        for path in files:
            value = _extract_label_value(path, label)
            if value and value.lower() not in {"_none_", "_none yet_", "_n/a_"}:
                return value
    return ""


def _infer_domain_concepts(text: str) -> list[str]:
    concepts: list[str] = []
    for chunk in re.split(r"[.;]\s*", text):
        value = _trim(chunk)
        if not value:
            continue
        if len(value) > 90:
            continue
        if value.lower() in {concept.lower() for concept in concepts}:
            continue
        concepts.append(value[:1].upper() + value[1:])
        if len(concepts) >= 4:
            break
    return concepts or ["Core domain entities and rules derived from the finalized product plan"]
