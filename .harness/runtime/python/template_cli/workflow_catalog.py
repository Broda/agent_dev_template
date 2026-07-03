from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import (
    IDEA_ROW_RE,
    clean_backticks,
    parse_markdown_table_rows,
    read_text,
    split_table_row,
    write_text,
)


def _trim(value: str | None) -> str:
    return (value or "").strip()


def _extract_catalog_row(root: Path, idea_id: str) -> dict[str, str]:
    catalog_path = root / "IDEA_CATALOG.md"
    if not catalog_path.exists():
        return {}
    for cells in parse_markdown_table_rows(catalog_path, IDEA_ROW_RE, width=7):
        if cells and cells[0].strip() == idea_id:
            return {
                "idea_id": cells[0].strip(),
                "title": cells[1].strip(),
                "status": cells[2].strip(),
                "owner": cells[3].strip(),
                "sessions": cells[4].strip(),
                "summary_export": clean_backticks(cells[5].strip()),
                "notes": cells[6].strip(),
            }
    return {}


def _render_catalog_row(
    idea_id: str,
    title: str,
    status: str,
    owner: str,
    sessions: list[str],
    summary_export: str,
    notes: str,
) -> str:
    sessions_cell = ", ".join(f"`{value}`" for value in sessions) if sessions else "_none_"
    export_cell = f"`{summary_export}`" if _trim(summary_export) else "_n/a_"
    return f"| {idea_id} | {title} | {status} | {owner} | {sessions_cell} | {export_cell} | {notes or '_none_'} |"


def _upsert_catalog_row(
    root: Path,
    *,
    idea_id: str,
    title: str,
    status: str,
    owner: str,
    sessions: list[str],
    summary_export: str,
    notes: str,
) -> None:
    catalog_path = root / "IDEA_CATALOG.md"
    lines = read_text(catalog_path).splitlines()
    row = _render_catalog_row(idea_id, title, status, owner, sessions, summary_export, notes)
    updated: list[str] = []
    inserted = False
    for line in lines:
        if IDEA_ROW_RE.search(line):
            cells = split_table_row(line)
            if cells and cells[0] == idea_id:
                updated.append(row)
                inserted = True
                continue
            updated.append(line)
            continue
        if line.startswith("| _none yet_"):
            if not inserted:
                updated.append(row)
                inserted = True
            continue
        updated.append(line)

    if not inserted:
        updated.append(row)
    write_text(catalog_path, "\n".join(updated) + "\n")
