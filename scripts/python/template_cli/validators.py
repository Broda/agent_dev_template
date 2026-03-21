from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


NOTE_ID_RE = re.compile(r"^note-\d{4}$")
NOTE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IDEA_ROW_RE = re.compile(r"^\|\s*idea-[a-z0-9-]+")
ADR_LINK_RE = re.compile(r"docs/adr/ADR-[0-9]{4}-[a-z0-9-]+\.md")
PLACEHOLDER_RE = re.compile(r"<[^>]+>")


def path_exists(root: Path, relative_path: str) -> bool:
    return bool(relative_path) and (root / relative_path).exists()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def replace_literal(content: str, old: str, new: str) -> str:
    return content.replace(old, new)


def read_mode(root: Path) -> str:
    mode_path = root / "MODE.md"
    if not mode_path.exists():
        return ""
    for line in read_text(mode_path).splitlines():
        if line.startswith("Current mode:"):
            return line.split(":", 1)[1].strip()
    return ""


def parse_markdown_table_rows(path: Path, pattern: re.Pattern[str]) -> list[list[str]]:
    if not path.exists():
        return []

    rows: list[list[str]] = []
    for line in read_text(path).splitlines():
        if pattern.search(line):
            rows.append([cell.strip() for cell in line.split("|")[1:-1]])
    return rows


def clean_backticks(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def is_noneish(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"_none_", "_none yet_", "_n/a_", "n/a"}


def find_markdown_files(root: Path) -> list[Path]:
    excluded_prefixes = [
        ".git",
        "external",
        "codex_brainstorming_template",
        "codex_template",
        "development/templates",
        "development/bootstrap",
    ]
    results: list[Path] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if any(rel == prefix or rel.startswith(prefix + "/") for prefix in excluded_prefixes):
            continue
        results.append(path)
    return results


@dataclass
class ValidationResult:
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_failure(self, message: str) -> None:
        self.failures.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def print_brainstorming_summary(result: ValidationResult) -> int:
    print("Lean validation summary")
    print(f"- Failures: {len(result.failures)}")
    print(f"- Warnings: {len(result.warnings)}")

    if result.warnings:
        print()
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.failures:
        print()
        print("Failures:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    print()
    print("PASS: lean integrity checks completed with no blocking failures.")
    return 0


def print_development_summary(result: ValidationResult) -> int:
    print("Development validation summary")
    print(f"- Failures: {len(result.failures)}")

    if result.failures:
        print()
        print("Failures:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    print()
    print("PASS: development integrity checks completed with no blocking failures.")
    return 0


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


def run_validate_brainstorming(root: Path) -> int:
    result = ValidationResult()

    core_artifacts = [
        "README.md",
        "AGENTS.md",
        "MODE.md",
        "brainstorming/AGENTS.brainstorming.md",
        "brainstorming/CONVERSATIONAL_MODE.md",
        "brainstorming/COMMANDS.md",
        "brainstorming/QUICKSTART.md",
        "brainstorming/FILE_MAP.md",
        "IDEA_CATALOG.md",
        "NOTES_CATALOG.md",
        "ideas/_inbox.md",
        "ideas/_active.md",
        "ideas/_parked.md",
        "ideas/_killed.md",
        "notes/",
        "brainstorming/templates/idea_template.md",
        "brainstorming/templates/decision_template.md",
        "brainstorming/templates/note_template.md",
        "brainstorming/templates/project_plan_packet_template.md",
        "brainstorming/templates/risk_template.md",
        "brainstorming/templates/review_gate_template.md",
        "brainstorming/docs/adr/template.md",
        "brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
        "scripts/validate-brainstorming.ps1",
        "scripts/validate-governance.ps1",
        "scripts/lab-sync.ps1",
        "scripts/lab-note.ps1",
        "scripts/finalize-project.sh",
        "scripts/render-development-docs.sh",
        "scripts/validate-development.sh",
        "scripts/validate-brainstorming.sh",
        "scripts/validate-governance.sh",
        "scripts/lab-sync.sh",
        "scripts/lab-note.sh",
        "scripts/finalize-project",
        "scripts/render-development-docs",
        "scripts/validate-development",
        "scripts/validate-brainstorming",
        "scripts/validate-governance",
        "scripts/lab-sync",
        "scripts/lab-note",
        "state/project-init.json",
        ".github/workflows/governance-audit.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ]

    for artifact in core_artifacts:
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
            }
            state_file = state_file_by_status.get(status)
            if state_file is None:
                result.add_failure(f"Unknown status '{status}' for '{idea_id}'.")
                continue

            if not path_exists(root, state_file):
                result.add_failure(f"Required state file '{state_file}' missing for status '{status}'.")

            if status == "active" and is_noneish(sessions):
                result.add_warning(f"Active idea '{idea_id}' has no session link yet.")

            if status == "exported":
                if not export_path or is_noneish(export_path):
                    result.add_failure(f"Exported idea '{idea_id}' must include export file path.")
                else:
                    clean_export_path = clean_backticks(export_path)
                    if not path_exists(root, clean_export_path):
                        result.add_failure(
                            f"Catalog export path missing for '{idea_id}': {clean_export_path}"
                        )

    validate_notes_catalog(root, result)

    if read_mode(root) != "brainstorming":
        result.add_failure(
            "MODE.md must remain in brainstorming mode while using brainstorming validation."
        )

    file_map_path = root / "brainstorming/FILE_MAP.md"
    if file_map_path.exists():
        file_map_contents = read_text(file_map_path)
        for artifact in core_artifacts:
            if f"`{artifact}`" not in file_map_contents:
                result.add_warning(f"FILE_MAP.md missing registry row for: {artifact}")

    return print_brainstorming_summary(result)


def run_validate_development(root: Path) -> int:
    result = ValidationResult()

    required = [
        "AGENTS.md",
        "MODE.md",
        "README.md",
        "CHANGELOG.md",
        ".gitignore",
        "NOTES_CATALOG.md",
        "notes/",
        "scripts/lab-note",
        "scripts/lab-note.sh",
        "scripts/lab-note.ps1",
        "docs/PROJECT_CONTEXT.md",
        "docs/ROADMAP.md",
        "docs/ARCHITECTURE.md",
        "docs/FILE_MAP.md",
        "docs/GOVERNANCE_INDEX.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
        "docs/SECURITY_POLICY.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        "docs/adr/ADR-TEMPLATE.md",
        "state/project-init.json",
    ]

    for artifact in required:
        if not path_exists(root, artifact):
            result.add_failure(f"Missing required artifact: {artifact}")

    if read_mode(root) != "development":
        result.add_failure("MODE.md must be switched to development.")

    placeholder_files = [root / "README.md", root / "CHANGELOG.md"]
    docs_dir = root / "docs"
    if docs_dir.exists():
        placeholder_files.extend(sorted(docs_dir.rglob("*.md")))
    for path in placeholder_files:
        if path.name == "ADR-TEMPLATE.md" and path.parent.name == "adr":
            continue
        if not path.exists():
            continue
        if PLACEHOLDER_RE.search(read_text(path)):
            result.add_failure("Unresolved placeholders detected in generated development docs.")
            break

    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists() or "## [Unreleased]" not in read_text(changelog_path):
        result.add_failure("CHANGELOG.md is missing the [Unreleased] section.")

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

    validate_notes_catalog(root, result)
    return print_development_summary(result)


def run_validate_governance(root: Path) -> int:
    mode = read_mode(root)
    if mode == "brainstorming":
        return run_validate_brainstorming(root)
    if mode == "development":
        return run_validate_development(root)

    print(f"Unknown mode in MODE.md: {mode}", file=sys.stderr)
    return 1
