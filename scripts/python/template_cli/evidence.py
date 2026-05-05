from __future__ import annotations

import re
from pathlib import Path

from template_cli.io_helpers import read_text, write_text


TASK_RE = re.compile(r"^(\s*-\s+\[)([ xX])(\]\s+)(.+)$")


def run_lab_evidence(
    root: Path,
    *,
    task: str,
    command: str,
    result: str,
    notes: list[str],
    no_complete: bool = False,
) -> int:
    roadmap = root / "docs/ROADMAP.md"
    if not roadmap.exists():
        print("Missing docs/ROADMAP.md. Finalize the project before recording development evidence.")
        return 1

    task_query = task.strip()
    command_value = _single_line(command)
    result_value = _single_line(result)
    if not task_query:
        print("--task is required.")
        return 1
    if not command_value:
        print("--command is required.")
        return 1
    if not result_value:
        print("--result is required.")
        return 1

    lines = read_text(roadmap).splitlines()
    matches = _matching_task_indexes(lines, task_query)
    if not matches:
        print(f"No roadmap checkbox task matched: {task_query}")
        return 1
    if len(matches) > 1:
        print(f"Roadmap task match is ambiguous: {task_query}")
        for index in matches:
            print(f"- {lines[index].strip()}")
        return 1

    task_index = matches[0]
    match = TASK_RE.match(lines[task_index])
    if match is None:
        print(f"Matched roadmap line is not a checkbox task: {lines[task_index]}")
        return 1

    if not no_complete:
        lines[task_index] = f"{match.group(1)}x{match.group(3)}{match.group(4)}"

    insert_at = _task_insert_index(lines, task_index)
    evidence_lines = [
        f"  - Evidence: {_inline_code(command_value)} -> {result_value}",
        *[f"  - Notes: {_single_line(note)}" for note in notes if _single_line(note)],
    ]
    lines[insert_at:insert_at] = evidence_lines
    write_text(roadmap, "\n".join(lines) + "\n")

    print(f"Recorded evidence for roadmap task: {match.group(4).strip()}")
    print("Updated docs/ROADMAP.md")
    return 0


def _matching_task_indexes(lines: list[str], task_query: str) -> list[int]:
    normalized_query = task_query.casefold()
    exact: list[int] = []
    fuzzy: list[int] = []
    for index, line in enumerate(lines):
        match = TASK_RE.match(line)
        if match is None:
            continue
        task_text = match.group(4).strip()
        normalized_task = task_text.casefold()
        if normalized_task == normalized_query:
            exact.append(index)
        elif normalized_query in normalized_task:
            fuzzy.append(index)
    return exact or fuzzy


def _task_insert_index(lines: list[str], task_index: int) -> int:
    index = task_index + 1
    while index < len(lines):
        line = lines[index]
        if TASK_RE.match(line) or line.startswith("#") or line.startswith("---"):
            break
        if line and not line.startswith((" ", "\t")):
            break
        index += 1
    return index


def _single_line(value: str) -> str:
    return " ".join(value.strip().split())


def _inline_code(value: str) -> str:
    escaped = value.replace("`", "\\`")
    return f"`{escaped}`"
