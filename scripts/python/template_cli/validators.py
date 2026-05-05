from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from template_cli.intents import (
    IntentRegistryError,
    registry_commands,
    render_intent_docs_to_memory,
)
from template_cli.validator_code_size import validate_python_file_sizes
from template_cli.validator_launchers import validate_python_launchers
from template_cli.validator_plugins import (
    PLUGIN_MANIFEST,
    PLUGIN_MARKETPLACE,
    PLUGIN_SKILL_ARTIFACTS,
    validate_repo_plugins,
)
from template_cli.validator_skills import REPO_SKILLS, REPO_SKILL_METADATA, validate_repo_skills
from template_cli.io_helpers import (
    ADR_LINK_RE,
    DEVELOPMENT_SEMANTIC_DOCS,
    FORBIDDEN_DEVELOPMENT_TEMPLATE_TERMS,
    IDEA_ROW_RE,
    NOTE_DATE_RE,
    NOTE_ID_RE,
    PLACEHOLDER_RE,
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


REPO_SKILL_ARTIFACTS = [
    artifact
    for skill_path, metadata_path in zip(REPO_SKILLS.values(), REPO_SKILL_METADATA.values())
    for artifact in (skill_path, metadata_path)
]
REPO_PLUGIN_ARTIFACTS = [PLUGIN_MARKETPLACE, PLUGIN_MANIFEST, *PLUGIN_SKILL_ARTIFACTS]


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


def documented_lab_commands(root: Path) -> set[str]:
    commands_path = root / "brainstorming/COMMANDS.md"
    if not commands_path.exists():
        return set()
    commands: set[str] = set()
    for match in re.findall(r"### `/lab ([a-z-]+)", read_text(commands_path)):
        commands.add(match.strip())
    return commands


def registered_lab_commands(root: Path) -> set[str]:
    cli_path = root / "scripts/python/cli.py"
    if not cli_path.exists():
        return set()
    result = subprocess.run(
        [sys.executable, str(cli_path), "-h"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    commands: set[str] = set()
    for match in re.findall(r"\blab-([a-z-]+)\b", output):
        commands.add(match.strip())
    return commands


def validate_lab_command_parity(root: Path, result: ValidationResult) -> None:
    documented = documented_lab_commands(root)
    registered = registered_lab_commands(root)
    if not documented or not registered:
        return
    missing = sorted(documented - registered)
    for command in missing:
        result.add_failure(f"Documented lab command is not registered in CLI: {command}")


def validate_intent_registry(root: Path, result: ValidationResult) -> None:
    try:
        registry_command_names = registry_commands(root)
        rendered_docs = render_intent_docs_to_memory(root)
    except IntentRegistryError as exc:
        result.add_failure(str(exc))
        return

    documented = documented_lab_commands(root)
    registered = registered_lab_commands(root)

    missing_doc_sections = sorted(registry_command_names - documented)
    for command in missing_doc_sections:
        result.add_failure(f"Intent registry command is missing a command section in COMMANDS.md: {command}")

    unknown_registry_commands = sorted(registry_command_names - registered)
    for command in unknown_registry_commands:
        result.add_failure(f"Intent registry command is not registered in CLI: {command}")

    for relative_path, expected_content in rendered_docs.items():
        path = root / relative_path
        if not path.exists():
            result.add_failure(f"Missing generated intent doc target: {relative_path}")
            continue
        if read_text(path) != expected_content:
            result.add_failure(
                f"Generated intent section is stale in {relative_path}. Run ./scripts/render-intent-docs."
            )


def validate_intent_sync_ci(root: Path, result: ValidationResult) -> None:
    ci_path = root / ".github/workflows/ci.yml"
    if not ci_path.exists():
        return

    ci_text = read_text(ci_path)
    required_checks = [
        ("render step", "\n          ./scripts/render-intent-docs\n"),
        (
            "drift warning",
            "Generated intent docs are out of sync. Run ./scripts/render-intent-docs and commit the result.",
        ),
        (
            "focused generated-doc diff",
            "git diff -- brainstorming/CONVERSATIONAL_MODE.md brainstorming/COMMANDS.md",
        ),
    ]
    for label, snippet in required_checks:
        if snippet not in ci_text:
            result.add_failure(f"CI workflow is missing the generated intent sync contract: {label}")


def run_validate_brainstorming(root: Path) -> int:
    result = ValidationResult()

    core_artifacts = [
        "README.md",
        "AGENTS.md",
        "MODE.md",
        *REPO_SKILL_ARTIFACTS,
        *REPO_PLUGIN_ARTIFACTS,
        "brainstorming/AGENTS.brainstorming.md",
        "brainstorming/CONVERSATIONAL_MODE.md",
        "brainstorming/COMMANDS.md",
        "brainstorming/intent_registry.json",
        "brainstorming/QUICKSTART.md",
        "brainstorming/EXAMPLE_LIFECYCLE.md",
        "brainstorming/FILE_MAP.md",
        "IDEA_CATALOG.md",
        "NOTES_CATALOG.md",
        "ideas/_inbox.md",
        "ideas/_active.md",
        "ideas/_parked.md",
        "ideas/_killed.md",
        "sessions/",
        "notes/",
        "exports/",
        "brainstorming/templates/idea_template.md",
        "brainstorming/templates/decision_template.md",
        "brainstorming/templates/note_template.md",
        "brainstorming/templates/project_plan_packet_template.md",
        "brainstorming/templates/risk_template.md",
        "brainstorming/templates/review_gate_template.md",
        "brainstorming/docs/adr/template.md",
        "brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
        "scripts/lab",
        "scripts/lab.sh",
        "scripts/lab.ps1",
        "scripts/validate-brainstorming.ps1",
        "scripts/validate-governance.ps1",
        "scripts/lab-sync.ps1",
        "scripts/lab-note.ps1",
        "scripts/sync-plugin-skills.ps1",
        "scripts/finalize-project.sh",
        "scripts/render-development-docs.sh",
        "scripts/sync-plugin-skills.sh",
        "scripts/validate-development.sh",
        "scripts/validate-brainstorming.sh",
        "scripts/validate-governance.sh",
        "scripts/lab-sync.sh",
        "scripts/lab-note.sh",
        "scripts/finalize-project",
        "scripts/render-intent-docs",
        "scripts/render-intent-docs.sh",
        "scripts/render-intent-docs.ps1",
        "scripts/sync-plugin-skills",
        "scripts/render-development-docs",
        "scripts/validate-development",
        "scripts/validate-brainstorming",
        "scripts/validate-governance",
        "scripts/lab-sync",
        "scripts/lab-note",
        "tests/workflow_test_helpers.py",
        "tests/test_development_rendering.py",
        "tests/test_lab_lifecycle.py",
        "tests/test_intent_registry_contract.py",
        "tests/test_template_validation.py",
        "tests/fixtures/finalized_state_v2.json",
        "tests/fixtures/finalized_state_web_app_v2.json",
        "tests/fixtures/finalized_state_with_persistence_v2.json",
        "tests/fixtures/finalized_session.md",
        "state/project-init.json",
        ".github/workflows/ci.yml",
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
        *REPO_SKILL_ARTIFACTS,
        *REPO_PLUGIN_ARTIFACTS,
        "NOTES_CATALOG.md",
        "sessions/",
        "notes/",
        "exports/",
        "scripts/lab",
        "scripts/lab.sh",
        "scripts/lab.ps1",
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
    validate_python_file_sizes(root, result)
    validate_python_launchers(root, result)
    validate_repo_plugins(root, result)
    validate_repo_skills(root, result)
    return print_development_summary(result)


def run_validate_governance(root: Path) -> int:
    mode = read_mode(root)
    if mode == "brainstorming":
        return run_validate_brainstorming(root)
    if mode == "development":
        return run_validate_development(root)

    print(f"Unknown mode in MODE.md: {mode}", file=sys.stderr)
    return 1
