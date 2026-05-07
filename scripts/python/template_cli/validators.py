from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from template_cli.validator_artifacts import BRAINSTORMING_CORE_ARTIFACTS, DEVELOPMENT_REQUIRED_ARTIFACTS
from template_cli.validator_code_size import validate_python_file_sizes
from template_cli.validator_intents import (
    validate_intent_registry,
    validate_intent_sync_ci,
    validate_lab_command_parity,
)
from template_cli.validator_launchers import validate_python_launchers
from template_cli.validator_module_boundaries import validate_module_boundaries
from template_cli.validator_plugins import validate_repo_plugins
from template_cli.validator_skills import validate_repo_skills
from template_cli.io_helpers import (
    ADR_LINK_RE,
    DEVELOPMENT_SEMANTIC_DOCS,
    FORBIDDEN_DEVELOPMENT_TEMPLATE_TERMS,
    IDEA_ROW_RE,
    NOTE_DATE_RE,
    NOTE_ID_RE,
    ValidationResult,
    clean_backticks,
    find_markdown_files,
    is_noneish,
    parse_markdown_table_rows,
    path_exists,
    print_brainstorming_summary,
    print_development_summary,
    read_mode,
    read_text,
)
from template_cli.validator_placeholders import find_unresolved_placeholders

def validate_notes_catalog(root: Path, result: ValidationResult) -> None:
    notes_catalog_path = root / "NOTES_CATALOG.md"
    if not notes_catalog_path.exists():
        result.add_failure("Missing NOTES_CATALOG.md")
        return

    seen_note_ids: set[str] = set()
    for cells in parse_markdown_table_rows(notes_catalog_path, re.compile(r"^\|\s*note-\d{4}\s*\|")):
        note_id = cells[0].strip() if len(cells) > 0 else ""
        note_date = cells[2].strip() if len(cells) > 2 else ""
        note_path = cells[5].strip() if len(cells) > 5 else ""

        if not NOTE_ID_RE.fullmatch(note_id):
            result.add_failure(f"Invalid note id format in NOTES_CATALOG.md: {note_id}")
            continue

        if note_id in seen_note_ids:
            result.add_failure(f"Duplicate note id in NOTES_CATALOG.md: {note_id}")
        else:
            seen_note_ids.add(note_id)

        if not NOTE_DATE_RE.fullmatch(note_date):
            result.add_failure(f"Invalid note date format for '{note_id}': {note_date}")

        clean_note_path = clean_backticks(note_path)
        if not clean_note_path.startswith("notes/"):
            result.add_failure(f"Note path for '{note_id}' must be under notes/: {clean_note_path}")
        elif not path_exists(root, clean_note_path):
            result.add_failure(f"Missing note file for '{note_id}': {clean_note_path}")


def validate_template_cli_file_map(root: Path, result: ValidationResult) -> None:
    file_map_path = root / "brainstorming/FILE_MAP.md"
    module_root = root / "scripts/python/template_cli"
    if not file_map_path.exists() or not module_root.exists():
        return

    file_map_contents = read_text(file_map_path)
    for path in sorted(module_root.glob("*.py")):
        if path.name == "__init__.py":
            continue
        relative_path = path.relative_to(root).as_posix()
        if f"`{relative_path}`" not in file_map_contents:
            result.add_failure(f"FILE_MAP.md missing registry row for template CLI module: {relative_path}")


def run_validate_brainstorming(root: Path) -> int:
    result = ValidationResult()

    for artifact in BRAINSTORMING_CORE_ARTIFACTS:
        if not path_exists(root, artifact):
            result.add_failure(f"Missing required artifact: {artifact}")

    for mdfile in find_markdown_files(root):
        rel_mdfile = mdfile.relative_to(root).as_posix()
        for match in ADR_LINK_RE.findall(read_text(mdfile)):
            if not path_exists(root, match):
                result.add_failure(f"Missing ADR link target: '{match}' referenced in '{rel_mdfile}'.")

    catalog_path = root / "IDEA_CATALOG.md"
    if not catalog_path.exists():
        result.add_failure("Missing IDEA_CATALOG.md")
    else:
        for cells in parse_markdown_table_rows(catalog_path, IDEA_ROW_RE):
            idea_id = cells[0].strip() if len(cells) > 0 else ""
            status = cells[2].strip() if len(cells) > 2 else ""
            sessions = cells[4].strip() if len(cells) > 4 else ""
            export_path = cells[5].strip() if len(cells) > 5 else ""

            if not idea_id or not status:
                result.add_failure(f"Malformed catalog row: {' | '.join(cells)}")
                continue

            state_file_by_status = {
                "inbox": "ideas/_inbox.md",
                "active": "ideas/_active.md",
                "parked": "ideas/_parked.md",
                "killed": "ideas/_killed.md",
                "exported": "ideas/_active.md",
                "finalized": "ideas/_active.md",
            }
            state_file = state_file_by_status.get(status)
            if state_file is None:
                result.add_failure(f"Unknown status '{status}' for '{idea_id}'.")
                continue

            if not path_exists(root, state_file):
                result.add_failure(f"Required state file '{state_file}' missing for status '{status}'.")

            if status == "active" and is_noneish(sessions):
                result.add_warning(f"Active idea '{idea_id}' has no session link yet.")

            if status in {"exported", "finalized"} and export_path and not is_noneish(export_path):
                clean_export_path = clean_backticks(export_path)
                if not path_exists(root, clean_export_path):
                    result.add_failure(f"Catalog export path missing for '{idea_id}': {clean_export_path}")

    validate_notes_catalog(root, result)
    validate_lab_command_parity(root, result)
    validate_intent_registry(root, result)
    validate_intent_sync_ci(root, result)
    validate_template_cli_file_map(root, result)
    validate_module_boundaries(root, result)
    validate_python_file_sizes(root, result)
    validate_python_launchers(root, result)
    validate_repo_plugins(root, result)
    validate_repo_skills(root, result)

    if read_mode(root) != "brainstorming":
        result.add_failure(
            "MODE.md must remain in brainstorming mode while using brainstorming validation."
        )

    file_map_path = root / "brainstorming/FILE_MAP.md"
    if file_map_path.exists():
        file_map_contents = read_text(file_map_path)
        for artifact in BRAINSTORMING_CORE_ARTIFACTS:
            if f"`{artifact}`" not in file_map_contents:
                result.add_warning(f"FILE_MAP.md missing registry row for: {artifact}")

    return print_brainstorming_summary(result)


def run_validate_development(root: Path) -> int:
    result = ValidationResult()

    for artifact in DEVELOPMENT_REQUIRED_ARTIFACTS:
        if not path_exists(root, artifact):
            result.add_failure(f"Missing required artifact: {artifact}")

    if read_mode(root) != "development":
        result.add_failure("MODE.md must be switched to development.")

    placeholder_files = [root / "README.md", root / "CHANGELOG.md"]
    docs_dir = root / "docs"
    if docs_dir.exists():
        placeholder_files.extend(sorted(docs_dir.rglob("*.md")))
    for finding in find_unresolved_placeholders(root, placeholder_files):
        result.add_failure(
            "Unresolved placeholder in "
            f"{finding.relative_path}:{finding.line_number}: {finding.token} "
            f"(source: {finding.source}; line: {finding.line})"
        )

    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists() or "## [Unreleased]" not in read_text(changelog_path):
        result.add_failure("CHANGELOG.md is missing the [Unreleased] section.")

    state: dict = {}
    state_path = root / "state/project-init.json"
    if state_path.exists():
        try:
            state = json.loads(read_text(state_path))
        except json.JSONDecodeError:
            state = {}

        if state.get("status") != "finalized":
            result.add_failure("state/project-init.json must be marked finalized.")
        if not str(state.get("ideaId", "")).strip():
            result.add_failure("state/project-init.json must include a non-empty ideaId.")
        if not str(state.get("projectType", "")).strip():
            result.add_failure("state/project-init.json must include a non-empty projectType.")
        schema_version = state.get("schemaVersion")
        if schema_version:
            if schema_version != 2:
                result.add_failure("state/project-init.json schemaVersion must be 2.")
            product = state.get("product", {})
            governance = state.get("governance", {})
            artifacts = state.get("artifacts", {})
            if not str(product.get("problemStatement", "")).strip():
                result.add_failure("state/project-init.json must include product.problemStatement.")
            if not str(product.get("solutionSummary", "")).strip():
                result.add_failure("state/project-init.json must include product.solutionSummary.")
            if not str(governance.get("topRisks", "")).strip():
                result.add_failure("state/project-init.json must include governance.topRisks.")
            session_files = artifacts.get("sessionFiles", [])
            if not isinstance(session_files, list) or not session_files:
                result.add_failure("state/project-init.json must include artifacts.sessionFiles.")
            adr_references = artifacts.get("adrReferences", [])
            if not isinstance(adr_references, list) or not adr_references:
                result.add_failure("state/project-init.json must include artifacts.adrReferences.")
            else:
                for adr_reference in adr_references:
                    if not isinstance(adr_reference, str) or not adr_reference.strip():
                        result.add_failure(
                            "state/project-init.json contains an empty artifacts.adrReferences entry."
                        )
                        continue
                    if not path_exists(root, adr_reference):
                        result.add_failure(
                            f"state/project-init.json references a missing ADR file: {adr_reference}"
                        )
            summary_export = str(artifacts.get("summaryExport", "")).strip()
            if summary_export and not path_exists(root, summary_export):
                result.add_failure(
                    f"state/project-init.json references a missing summary export: {summary_export}"
                )

    if not _state_allows_game_terms(state):
        for relative_path in DEVELOPMENT_SEMANTIC_DOCS:
            path = root / relative_path
            if not path.exists():
                continue
            text = read_text(path).lower()
            for term in FORBIDDEN_DEVELOPMENT_TEMPLATE_TERMS:
                if term in text:
                    result.add_failure(
                        f"Generated development docs contain template-specific language '{term}' in {relative_path}."
                    )
                    break

    validate_notes_catalog(root, result)
    validate_module_boundaries(root, result)
    validate_python_file_sizes(root, result)
    validate_python_launchers(root, result)
    validate_repo_plugins(root, result)
    validate_repo_skills(root, result)
    return print_development_summary(result)


def _state_allows_game_terms(state: dict) -> bool:
    if not isinstance(state, dict):
        return False
    project_type = str(state.get("projectType", "")).strip().lower()
    if "game" in project_type:
        return True
    text = _state_text(state).lower()
    text = re.sub(r"\b(?:non-game|not a game|not game|game-template|game template)\b", "", text)
    return bool(re.search(r"\b(game|gameplay|player|playable|battle)\b", text))


def _state_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(_state_text(child) for child in value.values())
    if isinstance(value, list):
        return " ".join(_state_text(child) for child in value)
    if value is None:
        return ""
    return str(value)


def run_validate_governance(root: Path) -> int:
    mode = read_mode(root)
    if mode == "brainstorming":
        return run_validate_brainstorming(root)
    if mode == "development":
        return run_validate_development(root)

    print(f"Unknown mode in MODE.md: {mode}", file=sys.stderr)
    return 1
