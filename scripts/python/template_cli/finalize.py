from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import AbstractContextManager
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
STATE_SCHEMA_VERSION = 2


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def trim(value: str | None) -> str:
    return (value or "").strip()


def join_by(sep: str, values: list[str]) -> str:
    return sep.join(v for v in values if trim(v))


def join_lines(values: list[str]) -> str:
    return "\n".join(v for v in values if trim(v))


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


def choose_idea_to_finalize(candidates: list[tuple[str, str, str]]) -> str:
    eprint("Multiple ideas are available to finalize:")
    for idx, (idea_id, title, status) in enumerate(candidates, start=1):
        display_title = title or idea_id
        eprint(f"{idx}) {display_title} [{idea_id}] ({status})")

    while True:
        try:
            response = input(f"Select idea to finalize [1-{len(candidates)}]: ")
        except EOFError:
            raise SystemExit(
                "Cannot infer which idea to finalize non-interactively.\n"
                "Rerun with stdin/TTY answers or pass --idea-id explicitly."
            )
        response = trim(response)
        if response.isdigit():
            idx = int(response)
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1][0]


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


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = trim(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def split_linkish_values(value: str, prefixes: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for prefix in prefixes:
        matches.extend(re.findall(rf"{re.escape(prefix)}/[^`,\s]+\.md", value))
    return unique_values(matches)


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
    _update_catalog_transition(root, idea_id, session_path="", export_path=export_path)


def _update_catalog_transition(root: Path, idea_id: str, session_path: str, export_path: str) -> None:
    catalog_path = root / "IDEA_CATALOG.md"
    lines = read_text(catalog_path).splitlines()
    updated: list[str] = []
    for line in lines:
        if IDEA_ROW_RE.search(line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells and cells[0] == idea_id:
                while len(cells) < 7:
                    cells.append("")
                _, title, _, owner, sessions, existing_export, notes = cells[:7]
                session_links = unique_values(
                    split_linkish_values(sessions, ("sessions",)) + ([session_path] if session_path else [])
                )
                summary_export = export_path or clean_backticks(existing_export)
                session_cell = ", ".join(f"`{value}`" for value in session_links) or "_none_"
                export_cell = f"`{summary_export}`" if trim(summary_export) else "_n/a_"
                line = f"| {idea_id} | {title} | finalized | {owner} | {session_cell} | {export_cell} | {notes} |"
        updated.append(line)
    write_text(catalog_path, "\n".join(updated) + "\n")


def _write_mode_development(root: Path) -> None:
    write_text(
        root / "MODE.md",
        "# Repository Mode\n\nCurrent mode: development\n\nAllowed values:\n\n- brainstorming\n- development\n\nSwitch modes with `./scripts/finalize-project`.\n",
    )


def resolve_finalize_idea_id(root: Path, explicit_idea_id: str = "") -> str:
    catalog_path = root / "IDEA_CATALOG.md"
    if not catalog_path.exists():
        raise SystemExit("IDEA_CATALOG.md not found.")

    explicit_idea_id = trim(explicit_idea_id)
    if explicit_idea_id:
        return explicit_idea_id

    state_idea_id = trim(existing_state_value(root, "ideaId"))
    if state_idea_id:
        return state_idea_id

    active_rows: list[tuple[str, str, str]] = []
    finalized_rows: list[tuple[str, str, str]] = []
    all_rows: list[tuple[str, str, str]] = []
    for cells in parse_markdown_table_rows(catalog_path, IDEA_ROW_RE):
        if not cells:
            continue
        idea_id = trim(cells[0] if len(cells) > 0 else "")
        title = trim(cells[1] if len(cells) > 1 else "") or idea_id
        status = trim(cells[2] if len(cells) > 2 else "")
        if not idea_id:
            continue
        row = (idea_id, title, status or "unknown")
        all_rows.append(row)
        if status == "active":
            active_rows.append(row)
        elif status in {"exported", "finalized"}:
            finalized_rows.append(row)

    if len(active_rows) == 1:
        return active_rows[0][0]
    if len(active_rows) > 1:
        return choose_idea_to_finalize(active_rows)
    if len(all_rows) == 1:
        return all_rows[0][0]
    if len(finalized_rows) == 1:
        return finalized_rows[0][0]
    if len(all_rows) > 1:
        return choose_idea_to_finalize(all_rows)

    raise SystemExit(
        "Could not infer which idea to finalize.\n"
        "Set state/project-init.json ideaId, keep at least one idea in IDEA_CATALOG.md, or pass --idea-id explicitly."
    )


def _write_summary_export(root: Path, export_path: str, state: dict) -> None:
    product = state.get("product", {})
    governance = state.get("governance", {})
    artifacts = state.get("artifacts", {})

    shutil.copyfile(root / "brainstorming/templates/project_plan_packet_template.md", root / export_path)
    export_file = root / export_path
    replace_line_prefix(export_file, "- Project name:", str(state.get("projectName", "")))
    replace_line_prefix(export_file, "- Idea ID:", str(state.get("ideaId", "")))
    replace_line_prefix(export_file, "- Owner:", str(state.get("owner", "unassigned")))
    replace_line_prefix(export_file, "- Date:", str(state.get("finalizedAt", "")))
    replace_line_prefix(export_file, "- One-sentence objective:", str(state.get("purpose", "")))
    replace_line_prefix(
        export_file,
        "- Problem statement:",
        str(product.get("problemStatement", "")) or str(state.get("purpose", "")),
    )
    replace_line_prefix(export_file, "- Target users:", str(product.get("targetUsers", "")) or "See related sessions")
    replace_line_prefix(export_file, "- Why now:", str(product.get("whyNow", "")) or "See related sessions")
    replace_line_prefix(
        export_file,
        "- Expected value:",
        str(product.get("expectedValue", "")) or str(state.get("purpose", "")),
    )
    replace_line_prefix(
        export_file,
        "- Solution summary:",
        str(product.get("solutionSummary", ""))
        or f"Deliver the first milestone vertical slice for {state.get('projectName', '')}.",
    )
    replace_line_prefix(
        export_file,
        "- MVP scope:",
        str(product.get("mvpScope", ""))
        or "Milestone 0 vertical slice with working build, run, and test commands.",
    )
    replace_line_prefix(
        export_file,
        "- Out of scope:",
        str(product.get("outOfScope", "")) or "See roadmap and follow-up sessions.",
    )
    replace_line_prefix(
        export_file,
        "- Assumptions and constraints:",
        join_by("; ", [str(product.get("assumptions", "")), str(state.get("constraints", ""))]),
    )
    replace_line_prefix(
        export_file,
        "- Key decisions:",
        str(governance.get("keyDecisions", "")) or "See canonical state and related sessions.",
    )
    replace_line_prefix(
        export_file,
        "- ADR references:",
        join_by(", ", [f"`{value}`" for value in list(artifacts.get("adrReferences", []))]),
    )
    replace_line_prefix(
        export_file,
        "- Top risks:",
        str(governance.get("topRisks", "")) or "Capture implementation risks during Milestone 0 execution.",
    )
    replace_line_prefix(
        export_file,
        "- Mitigation plans:",
        str(governance.get("mitigationPlans", ""))
        or "Keep scope narrow, validate early, and update governance on change.",
    )
    replace_line_prefix(
        export_file,
        "- Contingencies:",
        str(governance.get("contingencies", "")) or "Reduce scope and re-baseline roadmap if assumptions fail.",
    )
    replace_line_prefix(
        export_file,
        "- Remaining accepted risks:",
        str(governance.get("remainingAcceptedRisks", "")) or "None recorded at finalization time.",
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
        f"{state['commands']['build']} (success), {state['commands']['test']} (pass), {state['commands']['run']} (smoke verified).",
    )
    replace_line_prefix(
        export_file,
        "- Technical dependencies:",
        summarize_dependencies(
            str(state["techStack"]["language"]),
            str(state["techStack"]["runtime"]),
            str(state["techStack"]["framework"]),
            str(state["techStack"]["packageTool"]),
        ),
    )
    replace_line_prefix(
        export_file,
        "- External dependencies:",
        str(artifacts.get("noteReferences", "")) or "None recorded",
    )
    replace_line_prefix(export_file, "- Team/process dependencies:", f"Owner: {state.get('owner', 'unassigned')}")
    replace_line_prefix(
        export_file,
        "- Latest review session:",
        str(governance.get("latestReviewSession", "")) or "None recorded",
    )
    replace_line_prefix(
        export_file,
        "- Quality gate result:",
        str(governance.get("latestReviewOutcome", "")) or "conditional-pass",
    )
    replace_line_prefix(
        export_file,
        "- Required artifacts:",
        f"`{STATE_FILE}`, development governance docs, verification evidence, and implementation source.",
    )
    replace_line_prefix(
        export_file,
        "- Implementation recommendations:",
        f"Start with Milestone 0 and keep changes aligned to {state.get('projectType', '')} boundaries.",
    )
    replace_line_prefix(
        export_file,
        "- Sequencing notes:",
        "Build first, then run, then test, then capture verification evidence.",
    )
    replace_line_prefix(
        export_file,
        "- Explicit non-goals:",
        str(product.get("nonGoals", "")) or "Avoid scope expansion before baseline verification is complete.",
    )
    replace_line_prefix(
        export_file,
        "- Idea source link:",
        join_by(", ", [f"`{value}`" for value in list(artifacts.get("ideaFiles", []))]),
    )
    replace_line_prefix(
        export_file,
        "- Session links:",
        join_by(", ", [f"`{value}`" for value in list(artifacts.get("sessionFiles", []))]),
    )
    replace_line_prefix(
        export_file,
        "- ADR links:",
        join_by(", ", [f"`{value}`" for value in list(artifacts.get("adrReferences", []))]),
    )
    replace_line_prefix(
        export_file,
        "- Risk references:",
        str(governance.get("latestReviewSession", "")) or "See related sessions",
    )


def run_finalize_project(root: Path, idea_id: str, *, write_export: bool = False) -> int:
    idea_id = resolve_finalize_idea_id(root, idea_id)
    catalog_path = root / "IDEA_CATALOG.md"

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
    for match in split_linkish_values(sessions_col, ("sessions",)):
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
    existing_problem_statement = existing_state_value(root, "product.problemStatement")
    existing_target_users = existing_state_value(root, "product.targetUsers")
    existing_why_now = existing_state_value(root, "product.whyNow")
    existing_expected_value = existing_state_value(root, "product.expectedValue")
    existing_solution_summary = existing_state_value(root, "product.solutionSummary")
    existing_mvp_scope = existing_state_value(root, "product.mvpScope")
    existing_out_of_scope = existing_state_value(root, "product.outOfScope")
    existing_assumptions = existing_state_value(root, "product.assumptions")
    existing_non_goals = existing_state_value(root, "product.nonGoals")
    existing_key_decisions = existing_state_value(root, "governance.keyDecisions")
    existing_top_risks = existing_state_value(root, "governance.topRisks")
    existing_mitigation_plans = existing_state_value(root, "governance.mitigationPlans")
    existing_contingencies = existing_state_value(root, "governance.contingencies")
    existing_remaining_risks = existing_state_value(root, "governance.remainingAcceptedRisks")
    existing_latest_review_outcome = existing_state_value(root, "governance.latestReviewOutcome")
    existing_latest_review_session = existing_state_value(root, "governance.latestReviewSession")

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

    problem_statement = existing_problem_statement or first_value_for_label(hydrate_files, "Problem statement")
    target_users = existing_target_users or first_value_for_label(hydrate_files, "Affected users/personas") or first_value_for_label(
        hydrate_files, "Target users"
    )
    why_now = existing_why_now or first_value_for_label(hydrate_files, "Why now")
    expected_value = existing_expected_value or first_value_for_label(hydrate_files, "Expected value") or first_value_for_label(
        hydrate_files, "Value hypothesis"
    )
    solution_summary = existing_solution_summary or first_value_for_label(hydrate_files, "Solution summary")
    mvp_scope = existing_mvp_scope or first_value_for_label(hydrate_files, "MVP scope")
    out_of_scope = existing_out_of_scope or first_value_for_label(hydrate_files, "Out of scope")
    assumptions = existing_assumptions or first_value_for_label(hydrate_files, "Assumptions")
    non_goals = existing_non_goals or first_value_for_label(hydrate_files, "Non-goals")
    top_risks = existing_top_risks or first_value_for_label(hydrate_files, "Top risks") or first_value_for_label(
        hydrate_files, "Top risks (link to risk entries)"
    )
    mitigation_plans = existing_mitigation_plans or first_value_for_label(hydrate_files, "Mitigation plans") or first_value_for_label(
        hydrate_files, "Preventive mitigation"
    )
    contingencies = existing_contingencies or first_value_for_label(hydrate_files, "Contingency plan")
    remaining_risks = existing_remaining_risks or first_value_for_label(hydrate_files, "Remaining accepted risks")
    latest_review_outcome = existing_latest_review_outcome or first_value_for_label(hydrate_files, "Latest review outcome") or first_value_for_label(
        hydrate_files, "Result"
    )
    latest_review_session = existing_latest_review_session or latest_session_path(session_paths)

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
    key_decisions = existing_key_decisions or summarize_decisions(
        project_type, persistence, authentication, determinism, packaging
    )

    date_stamp = date.today().isoformat()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    session_path = f"sessions/{date_stamp}_FINALIZATION_SESSION_{idea_id}.md"

    (root / "sessions").mkdir(parents=True, exist_ok=True)
    if write_export:
        (root / "exports").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "docs/adr").mkdir(parents=True, exist_ok=True)

    with BackupManager(root) as backups:
        for relative_path in [
            STATE_FILE,
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
        if write_export:
            backups.backup_path(export_path)

        state = {
            "schemaVersion": STATE_SCHEMA_VERSION,
            "status": "finalized",
            "finalizedAt": date_stamp,
            "ideaId": idea_id,
            "projectName": project_name,
            "owner": owner,
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
            "product": {
                "problemStatement": problem_statement or objective,
                "targetUsers": target_users or "See related sessions",
                "whyNow": why_now or "See related sessions",
                "expectedValue": expected_value or objective,
                "solutionSummary": solution_summary or f"Deliver the first milestone vertical slice for {project_name}.",
                "mvpScope": mvp_scope or "Milestone 0 vertical slice with working build, run, and test commands.",
                "outOfScope": out_of_scope or "See roadmap and follow-up sessions.",
                "assumptions": assumptions,
                "nonGoals": non_goals,
            },
            "governance": {
                "keyDecisions": key_decisions
                or summarize_decisions(project_type, persistence, authentication, determinism, packaging),
                "topRisks": top_risks or "Capture implementation risks during Milestone 0 execution.",
                "mitigationPlans": mitigation_plans
                or "Keep scope narrow, validate early, and update governance on change.",
                "contingencies": contingencies or "Reduce scope and re-baseline roadmap if assumptions fail.",
                "remainingAcceptedRisks": remaining_risks or "None recorded at finalization time.",
                "latestReviewOutcome": latest_review_outcome or "conditional-pass",
                "latestReviewSession": latest_review_session,
            },
            "artifacts": {
                "ideaFiles": unique_values(idea_files),
                "sessionFiles": unique_values(session_paths + [session_path]),
                "noteReferences": notes_col or "None recorded",
                "summaryExport": export_path if write_export else "",
                "finalizationSession": session_path,
                "adrReferences": ["docs/adr/ADR-0001-record-architecture-decisions.md"],
            },
        }
        write_text(root / STATE_FILE, json.dumps(state, indent=2) + "\n")
        if write_export:
            _write_summary_export(root, export_path, state)

        render_code = run_render_development_docs(root)
        if render_code != 0:
            raise SystemExit(render_code)

        _update_catalog_transition(root, idea_id, session_path, export_path if write_export else "")
        _write_mode_development(root)

        session_lines = [
            "# Finalization Session",
            "",
            f"- Date: {date_stamp}",
            f"- Owner: {owner}",
            f"- Idea ID: {idea_id}",
            f"- Session: {session_path}",
            f"- Canonical state: `{STATE_FILE}`",
        ]
        if write_export:
            session_lines.append(f"- Summary export: `{export_path}`")
        session_content = join_lines(session_lines) + "\n\n"
        session_content += (
            "- Result: in-place mode switch completed\n\n"
            "The repository has been successfully finalized into development mode.\n"
        )
        write_text(root / session_path, session_content)

        validation_code = run_validate_development(root)
        if validation_code != 0:
            raise SystemExit(validation_code)

        backups.commit()

    print(f"Canonical state saved: {STATE_FILE}")
    print(f"Finalization session log: {session_path}")
    if write_export:
        print(f"Optional project summary written: {export_path}")
    print("The repository has been successfully finalized into development mode.")
    return 0
