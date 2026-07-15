from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from template_cli.finalize.helpers import files_containing, split_linkish_values, trim
from template_cli.io_helpers import IDEA_ROW_RE, clean_backticks, parse_markdown_table_rows, path_exists


@dataclass(frozen=True)
class FinalizeContext:
    idea_id: str
    project_name: str
    owner: str
    existing_export_path: str
    notes_col: str
    related_note_paths: list[str]
    idea_files: list[str]
    session_paths: list[str]
    hydrate_files: list[Path]


def load_finalize_context(root: Path, idea_id: str) -> FinalizeContext:
    catalog_cells = _catalog_cells_for_idea(root, idea_id)
    if catalog_cells is None:
        raise SystemExit(f"Idea '{idea_id}' not found in IDEA_CATALOG.md.")

    project_name = trim(catalog_cells[1] if len(catalog_cells) > 1 else "") or idea_id
    owner = _resolve_owner(root, trim(catalog_cells[3] if len(catalog_cells) > 3 else ""))
    sessions_col = trim(catalog_cells[4] if len(catalog_cells) > 4 else "")
    existing_export_path = clean_backticks(catalog_cells[5] if len(catalog_cells) > 5 else "")
    notes_col = trim(catalog_cells[6] if len(catalog_cells) > 6 else "")

    idea_files = files_containing(root, "ideas", idea_id)
    if not idea_files:
        raise SystemExit(
            f"Idea '{idea_id}' does not have a recorded idea entry under ideas/.\n"
            "Capture or activate the idea before finalizing."
        )

    session_paths = _session_paths_for_idea(root, idea_id, sessions_col)
    if not session_paths:
        raise SystemExit(
            f"Idea '{idea_id}' does not have a related session under sessions/.\n"
            "Create at least one session before finalizing."
        )

    related_note_paths = _note_paths_for_idea(root, idea_id)
    hydrate_files = [root / rel for rel in idea_files + session_paths + related_note_paths]
    if existing_export_path and path_exists(root, existing_export_path):
        hydrate_files.append(root / existing_export_path)

    return FinalizeContext(
        idea_id=idea_id,
        project_name=project_name,
        owner=owner,
        existing_export_path=existing_export_path,
        notes_col=notes_col,
        related_note_paths=related_note_paths,
        idea_files=idea_files,
        session_paths=session_paths,
        hydrate_files=hydrate_files,
    )


def _catalog_cells_for_idea(root: Path, idea_id: str) -> list[str] | None:
    for cells in parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE):
        if cells and cells[0] == idea_id:
            return cells
    return None


def _resolve_owner(root: Path, owner: str) -> str:
    if owner and owner != "unassigned":
        return owner
    result = subprocess.run(
        ["git", "config", "--get", "user.name"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return trim(result.stdout) or "unassigned"


def _session_paths_for_idea(root: Path, idea_id: str, sessions_col: str) -> list[str]:
    session_paths: list[str] = []
    for match in split_linkish_values(sessions_col, ("sessions",)):
        if path_exists(root, match) and match not in session_paths:
            session_paths.append(match)
    for match in files_containing(root, "sessions", idea_id):
        if match not in session_paths:
            session_paths.append(match)
    return session_paths


def _note_paths_for_idea(root: Path, idea_id: str) -> list[str]:
    note_paths: list[str] = []
    catalog_path = root / "NOTES_CATALOG.md"
    if catalog_path.exists():
        for line in catalog_path.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 6 or cells[3] != idea_id:
                continue
            candidate = clean_backticks(cells[5])
            if candidate and path_exists(root, candidate) and candidate not in note_paths:
                note_paths.append(candidate)
    for candidate in files_containing(root, "notes", f"- Related Idea ID: {idea_id}"):
        if candidate not in note_paths:
            note_paths.append(candidate)
    return sorted(note_paths)
