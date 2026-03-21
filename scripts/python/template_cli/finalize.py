from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from template_cli.render import run_render_development_docs
from template_cli.validators import (
    IDEA_ROW_RE,
    clean_backticks,
    parse_markdown_table_rows,
    path_exists,
    read_text,
    run_validate_development,
    write_text,
)


STATE_FILE = "state/project-init.json"


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def trim(value: str | None) -> str:
    return (value or "").strip()


def join_by(sep: str, values: list[str]) -> str:
    return sep.join(v for v in values if trim(v))


def replace_line_prefix(path: Path, prefix: str, value: str) -> None:
    normalized = value.replace("\n", " ").replace("\r", " ")
    lines = read_text(path).splitlines()
    updated = []
    for line in lines:
        if line.startswith(prefix):
            updated.append(f"{prefix} {normalized}".rstrip())
        else:
            updated.append(line)
    write_text(path, "\n".join(updated) + ("\n" if read_text(path).endswith("\n") else ""))


def existing_state_value(root: Path, dotted_path: str) -> str:
    state_path = root / STATE_FILE
    if not state_path.exists():
        return ""
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return ""
    cur = state
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return ""
        cur = cur[part]
    return "" if cur is None else str(cur)


def infer_project_type(project_name: str, objective: str) -> str:
    text = f"{project_name} {objective}".lower()
    if "cli" in text or "command line" in text:
        return "CLI"
    if "desktop" in text or "electron" in text:
        return "Desktop"
    if any(token in text for token in ("web", "frontend", "browser")):
        return "Web App"
    if any(token in text for token in ("api", "service", "backend")):
        return "API"
    if any(token in text for token in ("library", "sdk", "package")):
        return "Library"
    return ""


def prompt_eof_error(field: str) -> None:
    raise SystemExit(
        f"Cannot finalize non-interactively without a value for '{field}'.\n"
        "Populate state/project-init.json first or rerun with stdin/TTY answers."
    )


def ask_non_empty(prompt: str, current: str = "") -> str:
    current = trim(current)
    if current:
        try:
            response = input(f"{prompt} [{current}]: ")
        except EOFError:
            return current
        response = trim(response)
        return response or current

    while True:
        try:
            response = input(f"{prompt}: ")
        except EOFError:
            prompt_eof_error(prompt)
        response = trim(response)
        if response:
            return response


def choose_project_type(current: str) -> str:
    eprint("Project type options:")
    for idx, option in enumerate(["CLI", "Desktop", "Web App", "API", "Library"], start=1):
        eprint(f"{idx}) {option}")
    if current:
        eprint(f"Detected: {current}")

    while True:
        try:
            response = input(
                f"Select project type [1-5]{f' (current: {current})' if current else ''}: "
            )
        except EOFError:
            if current:
                return current
            prompt_eof_error("project type")
        response = trim(response)
        if not response and current:
            return current
        mapping = {"1": "CLI", "2": "Desktop", "3": "Web App", "4": "API", "5": "Library"}
        if response in mapping:
            return mapping[response]


def choose_from_list(prompt: str, current: str, options: list[str]) -> str:
    for idx, option in enumerate(options, start=1):
        eprint(f"{idx}) {option}")

    while True:
        try:
            response = input(
                f"{prompt} [1-{len(options)}]{f' (current: {current})' if current else ''}: "
            )
        except EOFError:
            if current:
                return current
            prompt_eof_error(prompt)
        response = trim(response)
        if not response and current:
            return current
        if response.isdigit():
            idx = int(response)
            if 1 <= idx <= len(options):
                return options[idx - 1]


def extract_label_value(path: Path, label: str) -> str:
    prefix = f"- {label}:"
    if not path.exists():
        return ""
    for line in read_text(path).splitlines():
        if line.startswith(prefix):
            return trim(line[len(prefix) :])
    return ""


def is_placeholder_value(value: str) -> bool:
    value = trim(value)
    return value in {"", "None", "_none_", "_n/a_", "_none yet_", "pass | conditional-pass | fail"}


def first_value_for_label(files: list[Path], label: str) -> str:
    for file_path in files:
        value = trim(extract_label_value(file_path, label))
        if value and not is_placeholder_value(value):
            return value
    return ""


def latest_session_path(session_paths: list[str]) -> str:
    return max(session_paths) if session_paths else ""


def summarize_decisions(project_type: str, persistence: str, authentication: str, determinism: str, packaging: str) -> str:
    parts = []
    if project_type:
        parts.append(f"Project type: {project_type}.")
    if persistence:
        parts.append(f"Persistence: {persistence}.")
    if authentication:
        parts.append(f"Authentication: {authentication}.")
    if determinism:
        parts.append(f"Correctness sensitivity: {determinism}.")
    if packaging:
        parts.append(f"Packaging: {packaging}.")
    return " ".join(parts).strip()


def summarize_dependencies(language: str, runtime: str, framework: str, package_tool: str) -> str:
    return f"Language: {language}; Runtime: {runtime}; Framework: {framework or 'None'}; Tooling: {package_tool or 'None'}"


def files_containing(root: Path, subdir: str, needle: str) -> list[str]:
    base = root / subdir
    if not base.exists():
        return []
    matches: list[str] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        try:
            if needle in read_text(path):
                matches.append(path.relative_to(root).as_posix())
        except UnicodeDecodeError:
            continue
    return matches


class BackupManager(AbstractContextManager["BackupManager"]):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.backup_dir = Path(tempfile.mkdtemp(prefix="finalize-project."))
        self.backed_up: set[str] = set()
        self.created: set[str] = set()
        self.committed = False

    def backup_path(self, relative_path: str) -> None:
        rel = Path(relative_path)
        target = self.root / rel
        if target.exists():
            backup_target = self.backup_dir / rel
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                shutil.copytree(target, backup_target, dirs_exist_ok=True)
            else:
                shutil.copy2(target, backup_target)
            self.backed_up.add(relative_path)
        else:
            self.created.add(relative_path)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        for relative_path in sorted(self.created, key=lambda p: len(Path(p).parts), reverse=True):
            target = self.root / relative_path
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            elif target.exists():
                target.unlink()
        for relative_path in sorted(self.backed_up):
            target = self.root / relative_path
            backup_target = self.backup_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            if backup_target.is_dir():
                shutil.copytree(backup_target, target)
            else:
                shutil.copy2(backup_target, target)

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None and not self.committed:
            self.rollback()
        shutil.rmtree(self.backup_dir, ignore_errors=True)
        return None


def _update_catalog_export(root: Path, idea_id: str, export_path: str) -> None:
    catalog_path = root / "IDEA_CATALOG.md"
    lines = read_text(catalog_path).splitlines()
    updated: list[str] = []
    for line in lines:
        if IDEA_ROW_RE.search(line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells and cells[0] == idea_id:
                while len(cells) < 7:
                    cells.append("")
                _, title, _, owner, sessions, _, notes = cells[:7]
                line = f"| {idea_id} | {title} | exported | {owner} | {sessions} | `{export_path}` | {notes} |"
        updated.append(line)
    write_text(catalog_path, "\n".join(updated) + "\n")


def _write_mode_development(root: Path) -> None:
    write_text(
        root / "MODE.md",
        "# Repository Mode\n\nCurrent mode: development\n\nAllowed values:\n\n- brainstorming\n- development\n\nSwitch modes with `./scripts/finalize-project`.\n",
    )


def run_finalize_project(root: Path, idea_id: str) -> int:
    catalog_path = root / "IDEA_CATALOG.md"
    if not catalog_path.exists():
        raise SystemExit("IDEA_CATALOG.md not found.")

    catalog_cells = None
    for cells in parse_markdown_table_rows(catalog_path, IDEA_ROW_RE):
        if cells and cells[0] == idea_id:
            catalog_cells = cells
            break
    if catalog_cells is None:
        raise SystemExit(f"Idea '{idea_id}' not found in IDEA_CATALOG.md.")

    project_name = trim(catalog_cells[1] if len(catalog_cells) > 1 else "") or idea_id
    owner = trim(catalog_cells[3] if len(catalog_cells) > 3 else "")
    sessions_col = trim(catalog_cells[4] if len(catalog_cells) > 4 else "")
    existing_export_path = clean_backticks(catalog_cells[5] if len(catalog_cells) > 5 else "")
    notes_col = trim(catalog_cells[6] if len(catalog_cells) > 6 else "")

    if not owner or owner == "unassigned":
        result = subprocess.run(
            ["git", "config", "--get", "user.name"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        owner = trim(result.stdout) or "unassigned"

    idea_files = files_containing(root, "ideas", idea_id)
    if not idea_files:
        raise SystemExit(
            f"Idea '{idea_id}' does not have a recorded idea entry under ideas/.\n"
            "Capture or activate the idea before finalizing."
        )

    session_paths: list[str] = []
    for match in re.findall(r"sessions/[^`,\s]+\.md", sessions_col):
        if path_exists(root, match) and match not in session_paths:
            session_paths.append(match)
    for match in files_containing(root, "sessions", idea_id):
        if match not in session_paths:
            session_paths.append(match)
    if not session_paths:
        raise SystemExit(
            f"Idea '{idea_id}' does not have a related session under sessions/.\n"
            "Create at least one session before finalizing."
        )

    existing_project_name = existing_state_value(root, "projectName")
    existing_purpose = existing_state_value(root, "purpose")
    existing_project_type = existing_state_value(root, "projectType")
    existing_language = existing_state_value(root, "techStack.language")
    existing_runtime = existing_state_value(root, "techStack.runtime")
    existing_framework = existing_state_value(root, "techStack.framework")
    existing_package_tool = existing_state_value(root, "techStack.packageTool")
    existing_persistence = existing_state_value(root, "persistence")
    existing_authentication = existing_state_value(root, "authentication")
    existing_determinism = existing_state_value(root, "determinism")
    existing_packaging = existing_state_value(root, "packaging")
    existing_constraints = existing_state_value(root, "constraints")
    existing_build_command = existing_state_value(root, "commands.build")
    existing_run_command = existing_state_value(root, "commands.run")
    existing_test_command = existing_state_value(root, "commands.test")

    if existing_project_name:
        project_name = existing_project_name

    hydrate_files = [root / rel for rel in idea_files + session_paths]
    if existing_export_path and path_exists(root, existing_export_path):
        hydrate_files.append(root / existing_export_path)

    objective = existing_purpose or ""
    if not objective:
        for label in [
            "One-sentence objective",
            "Problem statement",
            "Value hypothesis",
            "Summary rationale",
            "Situation summary",
        ]:
            objective = first_value_for_label(hydrate_files, label)
            if objective:
                break
    objective = ask_non_empty("One-sentence objective", objective)

    problem_statement = first_value_for_label(hydrate_files, "Problem statement")
    target_users = first_value_for_label(hydrate_files, "Affected users/personas") or first_value_for_label(
        hydrate_files, "Target users"
    )
    why_now = first_value_for_label(hydrate_files, "Why now")
    expected_value = first_value_for_label(hydrate_files, "Expected value") or first_value_for_label(
        hydrate_files, "Value hypothesis"
    )
    solution_summary = first_value_for_label(hydrate_files, "Solution summary")
    mvp_scope = first_value_for_label(hydrate_files, "MVP scope")
    out_of_scope = first_value_for_label(hydrate_files, "Out of scope")
    assumptions = first_value_for_label(hydrate_files, "Assumptions")
    non_goals = first_value_for_label(hydrate_files, "Non-goals")
    top_risks = first_value_for_label(hydrate_files, "Top risks") or first_value_for_label(
        hydrate_files, "Top risks (link to risk entries)"
    )
    mitigation_plans = first_value_for_label(hydrate_files, "Mitigation plans") or first_value_for_label(
        hydrate_files, "Preventive mitigation"
    )
    contingencies = first_value_for_label(hydrate_files, "Contingency plan")
    remaining_risks = first_value_for_label(hydrate_files, "Remaining accepted risks")
    latest_review_outcome = first_value_for_label(hydrate_files, "Latest review outcome") or first_value_for_label(
        hydrate_files, "Result"
    )
    latest_review_session = latest_session_path(session_paths)

    constraints_source = existing_constraints if not is_placeholder_value(existing_constraints) else ""
    if not constraints_source:
        constraints_source = first_value_for_label(hydrate_files, "Constraints")

    project_type = choose_project_type(existing_project_type or infer_project_type(project_name, objective))
    language = ask_non_empty("Language", existing_language)
    runtime = ask_non_empty("Runtime", existing_runtime)
    framework = ask_non_empty("Framework (if any, else 'None')", existing_framework or "None")
    package_tool = ask_non_empty(
        "Package manager/build tool (if any, else 'None')", existing_package_tool or "None"
    )
    persistence = choose_from_list(
        "Persistence",
        existing_persistence,
        ["None", "File-based (JSON/YAML/etc.)", "SQLite", "Postgres/MySQL/Other RDBMS"],
    )
    authentication = choose_from_list(
        "Authentication", existing_authentication, ["None", "Local users", "External auth provider"]
    )
    determinism = choose_from_list(
        "Determinism/correctness sensitivity", existing_determinism, ["Normal", "High"]
    )
    packaging = choose_from_list(
        "Packaging/distribution planned",
        existing_packaging,
        ["None", "Yes (desktop installers / containers / artifacts)"],
    )
    constraints = ask_non_empty(
        "Constraints (comma-separated; use 'None' if none)", constraints_source or "None"
    )
    build_command = ask_non_empty("Build command", existing_build_command)
    run_command = ask_non_empty("Run command", existing_run_command)
    test_command = ask_non_empty("Test command", existing_test_command)

    date_stamp = date.today().isoformat()
    export_path = f"exports/{date_stamp}_PROJECT_PLAN_PACKET_{idea_id}.md"
    session_path = f"exports/{date_stamp}_FINALIZATION_SESSION_{idea_id}.md"

    (root / "exports").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "docs/adr").mkdir(parents=True, exist_ok=True)

    with BackupManager(root) as backups:
        for relative_path in [
            STATE_FILE,
            export_path,
            "README.md",
            "CHANGELOG.md",
            ".gitignore",
            "docs/PROJECT_CONTEXT.md",
            "docs/ROADMAP.md",
            "docs/ARCHITECTURE.md",
            "docs/FILE_MAP.md",
            "docs/GOVERNANCE_INDEX.md",
            "docs/VERSIONING_AND_RELEASE_POLICY.md",
            "docs/SECURITY_POLICY.md",
            "docs/RUNTIME_VERIFICATION_REPORT.md",
            "docs/MIGRATION_POLICY.md",
            "docs/adr/ADR-0001-record-architecture-decisions.md",
            "docs/adr/ADR-TEMPLATE.md",
            "IDEA_CATALOG.md",
            "MODE.md",
            session_path,
        ]:
            backups.backup_path(relative_path)

        state = {
            "status": "finalized",
            "ideaId": idea_id,
            "projectName": project_name,
            "purpose": objective,
            "projectType": project_type,
            "techStack": {
                "language": language,
                "runtime": runtime,
                "framework": framework,
                "packageTool": package_tool,
            },
            "persistence": persistence,
            "authentication": authentication,
            "determinism": determinism,
            "packaging": packaging,
            "constraints": constraints,
            "commands": {
                "build": build_command,
                "run": run_command,
                "test": test_command,
            },
        }
        write_text(root / STATE_FILE, json.dumps(state, indent=2) + "\n")

        shutil.copyfile(
            root / "brainstorming/templates/project_plan_packet_template.md", root / export_path
        )
        export_file = root / export_path
        replace_line_prefix(export_file, "- Project name:", project_name)
        replace_line_prefix(export_file, "- Idea ID:", idea_id)
        replace_line_prefix(export_file, "- Owner:", owner)
        replace_line_prefix(export_file, "- Date:", date_stamp)
        replace_line_prefix(export_file, "- One-sentence objective:", objective)
        replace_line_prefix(export_file, "- Problem statement:", problem_statement or objective)
        replace_line_prefix(export_file, "- Target users:", target_users or "See related sessions")
        replace_line_prefix(export_file, "- Why now:", why_now or "See related sessions")
        replace_line_prefix(export_file, "- Expected value:", expected_value or objective)
        replace_line_prefix(
            export_file,
            "- Solution summary:",
            solution_summary or f"Deliver the first milestone vertical slice for {project_name}.",
        )
        replace_line_prefix(
            export_file,
            "- MVP scope:",
            mvp_scope or "Milestone 0 vertical slice with working build, run, and test commands.",
        )
        replace_line_prefix(export_file, "- Out of scope:", out_of_scope or "See roadmap and follow-up sessions.")
        replace_line_prefix(
            export_file, "- Assumptions and constraints:", join_by("; ", [assumptions, constraints])
        )
        replace_line_prefix(
            export_file,
            "- Key decisions:",
            summarize_decisions(project_type, persistence, authentication, determinism, packaging),
        )
        replace_line_prefix(
            export_file, "- ADR references:", "`docs/adr/ADR-0001-record-architecture-decisions.md`"
        )
        replace_line_prefix(
            export_file, "- Top risks:", top_risks or "Capture implementation risks during Milestone 0 execution."
        )
        replace_line_prefix(
            export_file,
            "- Mitigation plans:",
            mitigation_plans or "Keep scope narrow, validate early, and update governance on change.",
        )
        replace_line_prefix(
            export_file,
            "- Contingencies:",
            contingencies or "Reduce scope and re-baseline roadmap if assumptions fail.",
        )
        replace_line_prefix(
            export_file, "- Remaining accepted risks:", remaining_risks or "None recorded at finalization time."
        )
        replace_line_prefix(export_file, "- Milestone 1:", "Milestone 0 vertical slice implemented and verified.")
        replace_line_prefix(
            export_file,
            "- Milestone 2:",
            "Stabilize architecture, tests, and documentation after first delivery.",
        )
        replace_line_prefix(
            export_file,
            "- Milestone 3:",
            "Expand scope only after baseline verification remains green.",
        )
        replace_line_prefix(
            export_file,
            "- Exit criteria per milestone:",
            f"{build_command} (success), {test_command} (pass), {run_command} (smoke verified).",
        )
        replace_line_prefix(
            export_file,
            "- Technical dependencies:",
            summarize_dependencies(language, runtime, framework, package_tool),
        )
        replace_line_prefix(export_file, "- External dependencies:", notes_col or "None recorded")
        replace_line_prefix(export_file, "- Team/process dependencies:", f"Owner: {owner}")
        replace_line_prefix(
            export_file, "- Latest review session:", latest_review_session or "None recorded"
        )
        replace_line_prefix(
            export_file, "- Quality gate result:", latest_review_outcome or "conditional-pass"
        )
        replace_line_prefix(
            export_file,
            "- Required artifacts:",
            f"`{STATE_FILE}`, development governance docs, verification evidence, and implementation source.",
        )
        replace_line_prefix(
            export_file,
            "- Implementation recommendations:",
            f"Start with Milestone 0 and keep changes aligned to {project_type} boundaries.",
        )
        replace_line_prefix(
            export_file,
            "- Sequencing notes:",
            "Build first, then run, then test, then capture verification evidence.",
        )
        replace_line_prefix(
            export_file,
            "- Explicit non-goals:",
            non_goals or "Avoid scope expansion before baseline verification is complete.",
        )
        replace_line_prefix(export_file, "- Idea source link:", join_by(", ", idea_files))
        replace_line_prefix(export_file, "- Session links:", join_by(", ", session_paths))
        replace_line_prefix(export_file, "- ADR links:", "`docs/adr/ADR-0001-record-architecture-decisions.md`")
        replace_line_prefix(export_file, "- Risk references:", latest_review_session or "See related sessions")

        render_code = run_render_development_docs(root)
        if render_code != 0:
            raise SystemExit(render_code)

        _update_catalog_export(root, idea_id, export_path)
        _write_mode_development(root)

        session_content = (
            "# Finalization Session\n\n"
            f"- Date: {date_stamp}\n"
            f"- Owner: {owner}\n"
            f"- Idea ID: {idea_id}\n"
            f"- Session: {session_path}\n"
            f"- Export: `{export_path}`\n"
            f"- Canonical state: `{STATE_FILE}`\n"
            "- Result: in-place mode switch completed\n\n"
            "The repository has been successfully finalized into development mode.\n"
        )
        write_text(root / session_path, session_content)

        validation_code = run_validate_development(root)
        if validation_code != 0:
            raise SystemExit(validation_code)

        backups.commit()

    print(f"Project plan created: {export_path}")
    print(f"Canonical state saved: {STATE_FILE}")
    print(f"Finalization session log: {session_path}")
    print("The repository has been successfully finalized into development mode.")
    return 0
