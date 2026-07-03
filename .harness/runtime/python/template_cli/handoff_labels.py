from __future__ import annotations

from pathlib import Path
from typing import Any

from template_cli.finalize.helpers import trim
from template_cli.handoff_state import is_empty_handoff_value
from template_cli.io_helpers import read_text


def handoff_source_files(root: Path, context: Any) -> list[Path]:
    ordered: list[str] = []
    for rel_path in sorted(context.session_paths, reverse=True):
        if rel_path not in ordered:
            ordered.append(rel_path)
    if context.existing_export_path and context.existing_export_path not in ordered:
        ordered.append(context.existing_export_path)
    for rel_path in context.idea_files:
        if rel_path not in ordered:
            ordered.append(rel_path)
    return [root / rel_path for rel_path in ordered]


def first_label_value(files: list[Path], labels: list[str]) -> str:
    for label in labels:
        value = first_value_for_label(files, label)
        if value:
            return value
    return ""


def first_value_for_label(files: list[Path], label: str) -> str:
    prefix = f"- {label}:"
    for file_path in files:
        if not file_path.exists():
            continue
        for line in read_text(file_path).splitlines():
            stripped = line.strip()
            if stripped.startswith(prefix):
                value = trim(stripped[len(prefix) :])
                if not is_empty_handoff_value(value):
                    return value
    return ""
