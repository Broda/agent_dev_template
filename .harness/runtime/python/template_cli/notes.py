from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

from template_cli.finalize_history import HISTORY_ROOT
from template_cli.io_helpers import read_mode, read_text, write_text
from template_cli.sync import run_lab_sync

NOTE_ROW_RE = re.compile(r"^\|\s*note-(\d{4})\s*\|")


def _kebab(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", slug) or "note"


def _trim(value: str | None) -> str:
    return (value or "").strip()


def _strip_list_marker(value: str) -> str:
    return re.sub(r"^\s*[-*]\s+", "", value).strip()


def _read_items_file(path_value: str) -> list[str]:
    path_value = _trim(path_value)
    if not path_value:
        return []
    if path_value == "-":
        text = sys.stdin.read()
    else:
        text = Path(path_value).read_text(encoding="utf-8")
    return [_strip_list_marker(line) for line in text.splitlines() if _strip_list_marker(line)]


def _section_items(values: list[str] | None = None, file_values: list[str] | None = None) -> list[str]:
    items: list[str] = []
    for value in values or []:
        for line in value.splitlines():
            item = _strip_list_marker(line)
            if item:
                items.append(item)
    for file_value in file_values or []:
        items.extend(_read_items_file(file_value))
    return items


def _append_bullets(lines: list[str], items: list[str], placeholder: str) -> None:
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append(f"- {placeholder}")


def run_lab_note(
    root: Path,
    *,
    topic: str,
    source_context: str = "recent assistant research context",
    idea_id: str = "",
    tags: str = "",
    summaries: list[str] | None = None,
    summary_files: list[str] | None = None,
    details: list[str] | None = None,
    detail_files: list[str] | None = None,
    facts: list[str] | None = None,
    fact_files: list[str] | None = None,
    questions: list[str] | None = None,
    question_files: list[str] | None = None,
    links: list[str] | None = None,
    link_files: list[str] | None = None,
    no_sync: bool = False,
) -> int:
    topic = _trim(topic)
    if not topic:
        raise SystemExit("--topic is required.")

    captured_items = [
        *_section_items(summaries, summary_files),
        *_section_items(details, detail_files),
    ]
    fact_items = _section_items(facts, fact_files)
    question_items = _section_items(questions, question_files)
    link_items = _section_items(links, link_files)
    mode = read_mode(root) or "brainstorming"
    notes_base = (
        Path(HISTORY_ROOT) if mode == "development" and (root / HISTORY_ROOT / "NOTES_CATALOG.md").exists() else Path()
    )
    notes_dir = root / notes_base / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    notes_catalog_path = root / notes_base / "NOTES_CATALOG.md"
    if not notes_catalog_path.exists():
        raise SystemExit(f"{(notes_base / 'NOTES_CATALOG.md').as_posix()} not found.")

    max_id = 0
    for line in read_text(notes_catalog_path).splitlines():
        match = NOTE_ROW_RE.match(line)
        if match:
            max_id = max(max_id, int(match.group(1)))

    note_id = f"note-{max_id + 1:04d}"
    date_stamp = date.today().isoformat()
    note_path = notes_base / "notes" / f"{date_stamp}_{note_id}-{_kebab(topic)}.md"

    lines = [
        "# Research Note",
        "",
        "## Metadata",
        "",
        f"- Note ID: {note_id}",
        f"- Title: {topic}",
        f"- Date: {date_stamp}",
        f"- Related Idea ID: {idea_id or 'n/a'}",
        f"- Source Context: {source_context}",
        f"- Tags: {tags or 'n/a'}",
        "",
        "## Captured Information",
        "",
    ]
    _append_bullets(lines, captured_items, "Summary pending: fill in captured research details.")
    lines.extend(
        [
            "",
            "## Key Facts / Constraints",
            "",
        ]
    )
    _append_bullets(lines, fact_items, "None recorded.")
    lines.extend(
        [
            "",
            "## Open Questions / Follow-ups",
            "",
        ]
    )
    _append_bullets(lines, question_items, "None recorded.")
    lines.extend(
        [
            "",
            "## Links",
            "",
        ]
    )
    _append_bullets(lines, link_items, "None recorded.")
    lines.extend(
        [
            "",
        ]
    )
    write_text(root / note_path, "\n".join(lines))

    with notes_catalog_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"| {note_id} | {topic} | {date_stamp} | {idea_id or 'n/a'} | {source_context} | `{note_path.as_posix()}` | {tags or 'n/a'} |\n"
        )

    if not no_sync:
        exit_code = run_lab_sync(
            root,
            message=f"{mode}: note {note_id}",
            quiet=True,
            no_warn_push_failure=True,
            files=[note_path.as_posix(), (notes_base / "NOTES_CATALOG.md").as_posix()],
        )
        if exit_code != 0:
            raise SystemExit(exit_code)
        print(f"Note saved and persisted: {note_path.as_posix()}")
    else:
        print(f"Note saved (sync skipped): {note_path.as_posix()}")

    return 0
