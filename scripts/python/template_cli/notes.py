from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from template_cli.sync import run_lab_sync
from template_cli.validators import read_mode, read_text, write_text


NOTE_ROW_RE = re.compile(r"^\|\s*note-(\d{4})\s*\|")


def _kebab(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", slug) or "note"


def _trim(value: str | None) -> str:
    return (value or "").strip()


def run_lab_note(
    root: Path,
    *,
    topic: str,
    source_context: str = "recent assistant research context",
    idea_id: str = "",
    tags: str = "",
    summaries: list[str] | None = None,
    no_sync: bool = False,
) -> int:
    topic = _trim(topic)
    if not topic:
        raise SystemExit("--topic is required.")

    summaries = summaries or []
    mode = read_mode(root) or "brainstorming"
    notes_dir = root / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    notes_catalog_path = root / "NOTES_CATALOG.md"
    if not notes_catalog_path.exists():
        raise SystemExit("NOTES_CATALOG.md not found.")

    max_id = 0
    for line in read_text(notes_catalog_path).splitlines():
        match = NOTE_ROW_RE.match(line)
        if match:
            max_id = max(max_id, int(match.group(1)))

    note_id = f"note-{max_id + 1:04d}"
    date_stamp = date.today().isoformat()
    note_path = Path("notes") / f"{date_stamp}_{note_id}-{_kebab(topic)}.md"

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
    if summaries:
        lines.extend(f"- {summary}" for summary in summaries)
    else:
        lines.append("- Summary pending: fill in captured research details.")
    lines.extend(
        [
            "",
            "## Key Facts / Constraints",
            "",
            "- ",
            "",
            "## Open Questions / Follow-ups",
            "",
            "- ",
            "",
            "## Links",
            "",
            "- ",
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
            files=[note_path.as_posix(), "NOTES_CATALOG.md"],
        )
        if exit_code != 0:
            raise SystemExit(exit_code)
        print(f"Note saved and persisted: {note_path.as_posix()}")
    else:
        print(f"Note saved (sync skipped): {note_path.as_posix()}")

    return 0
