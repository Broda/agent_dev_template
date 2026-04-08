from __future__ import annotations

import shutil
import tempfile
from contextlib import AbstractContextManager
from pathlib import Path

from template_cli.finalize_helpers import (
    STATE_FILE,
    choose_idea_to_finalize,
    clean_backticks,
    existing_state_value,
    join_by,
    replace_line_prefix,
    split_linkish_values,
    summarize_dependencies,
    trim,
    unique_values,
)
from template_cli.validators import IDEA_ROW_RE, parse_markdown_table_rows, read_text, write_text


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
        or f"Deliver the first implementation slice for {state.get('projectName', '')}.",
    )
    replace_line_prefix(
        export_file,
        "- MVP scope:",
        str(product.get("mvpScope", ""))
        or "Milestone 0 implementation slice with working build, run, and test commands.",
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
    replace_line_prefix(export_file, "- Milestone 1:", "Milestone 0 implementation slice implemented and verified.")
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
