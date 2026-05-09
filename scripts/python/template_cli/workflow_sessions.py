from __future__ import annotations

import re
from pathlib import Path

from template_cli.io_helpers import read_text, write_text
from template_cli.workflow_data import _collect_session_links, _extract_catalog_row, _today

SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def _next_sequence_id(root: Path, prefix: str) -> str:
    pattern = re.compile(rf"{re.escape(prefix)}-(\d+)")
    highest = 0
    for path in sorted((root / "sessions").glob("*.md")) if (root / "sessions").exists() else []:
        for match in pattern.findall(read_text(path)):
            highest = max(highest, int(match))
    return f"{prefix}-{highest + 1:03d}"


def _ensure_session_file(root: Path, idea_id: str, title: str, owner: str, explicit_path: str = "") -> str:
    if explicit_path:
        session_path = explicit_path
    else:
        row = _extract_catalog_row(root, idea_id)
        existing = _collect_session_links(root, idea_id, row)
        session_path = existing[-1] if existing else f"sessions/{_today()}_{idea_id}.md"

    full_path = root / session_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    if not full_path.exists():
        content = "\n".join(
            [
                "# Brainstorming Session",
                "",
                "## Metadata",
                "",
                f"- Date: {_today()}",
                f"- Idea ID: `{idea_id}`",
                f"- Title: {title}",
                f"- Owner: {owner}",
                "- Status: active",
                "",
                "## Current Focus",
                "",
                "- ",
                "",
                "## Exploration Path Notes",
                "",
                "## Decisions",
                "",
                "## Risks",
                "",
                "## Review Gates",
                "",
            ]
        )
        write_text(full_path, content)
    return session_path


def _append_under_section(path: Path, section_title: str, block: str) -> None:
    lines = read_text(path).splitlines()
    block_lines = block.strip().splitlines()
    normalized_title = re.sub(r"\s+", " ", section_title.strip())
    section_start = -1
    section_end = len(lines)

    for index, line in enumerate(lines):
        match = SECTION_HEADING_RE.match(line)
        if not match:
            continue
        heading_title = re.sub(r"\s+", " ", match.group(1).strip())
        if heading_title == normalized_title:
            section_start = index

    if section_start >= 0:
        for index in range(section_start + 1, len(lines)):
            if SECTION_HEADING_RE.match(lines[index]):
                section_end = index
                break

        body = list(lines[section_start + 1 : section_end])
        while body and not body[-1].strip():
            body.pop()
        if not body:
            body = [""]
        elif body[-1].strip():
            body.append("")
        body.extend(block_lines)
        body.append("")
        updated_lines = lines[: section_start + 1] + body + lines[section_end:]
        write_text(path, "\n".join(updated_lines).rstrip() + "\n")
        return

    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        lines.append("")
    lines.append(f"## {section_title}")
    lines.append("")
    lines.extend(block_lines)
    lines.append("")
    write_text(path, "\n".join(lines).rstrip() + "\n")
