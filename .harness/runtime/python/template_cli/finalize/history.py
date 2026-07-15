from __future__ import annotations

import copy
import re
import shutil
from pathlib import Path
from typing import Any

from template_cli.io_helpers import read_text, write_text

HISTORY_ROOT = ".harness/history"
HISTORY_ITEMS = [
    "ideas",
    "sessions",
    "notes",
    "exports",
    "IDEA_CATALOG.md",
    "NOTES_CATALOG.md",
]
HISTORY_PREFIXES = ("ideas/", "sessions/", "notes/", "exports/")


def archive_brainstorming_history(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    _move_history_items(root)
    archived_state = copy.deepcopy(state)
    _rewrite_state_history_paths(archived_state)
    _rewrite_archived_catalogs(root)
    return archived_state


def _move_history_items(root: Path) -> None:
    history_root = root / HISTORY_ROOT
    history_root.mkdir(parents=True, exist_ok=True)
    for item in HISTORY_ITEMS:
        source = root / item
        if not source.exists():
            continue
        target = history_root / item
        if source.is_dir():
            _merge_directory(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            shutil.move(source.as_posix(), target.as_posix())


def _merge_directory(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        destination = target / child.name
        if destination.exists():
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        shutil.move(child.as_posix(), destination.as_posix())
    source.rmdir()


def _rewrite_state_history_paths(state: dict[str, Any]) -> None:
    artifacts = state.get("artifacts")
    if isinstance(artifacts, dict):
        for key in ["ideaFiles", "sessionFiles"]:
            values = artifacts.get(key)
            if isinstance(values, list):
                artifacts[key] = [_history_path(str(value)) for value in values]
        for key in ["noteReferences", "summaryExport", "finalizationSession"]:
            value = artifacts.get(key)
            if isinstance(value, str):
                artifacts[key] = _history_text(value)
    governance = state.get("governance")
    if isinstance(governance, dict) and isinstance(governance.get("latestReviewSession"), str):
        governance["latestReviewSession"] = _history_text(str(governance["latestReviewSession"]))
    brainstorming_contract = state.get("brainstormingContract")
    if isinstance(brainstorming_contract, dict):
        for key in ["decisions", "risks", "relatedNotes", "sessionSections"]:
            records = brainstorming_contract.get(key, [])
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                for path_key in ["source", "path"]:
                    if isinstance(record.get(path_key), str):
                        record[path_key] = _history_text(record[path_key])


def _rewrite_archived_catalogs(root: Path) -> None:
    for catalog in ["IDEA_CATALOG.md", "NOTES_CATALOG.md"]:
        path = root / HISTORY_ROOT / catalog
        if not path.exists():
            continue
        write_text(path, _history_text(read_text(path)))


def _history_text(value: str) -> str:
    return re.sub(r"(?<![A-Za-z0-9_./-])(ideas|sessions|notes|exports)/", rf"{HISTORY_ROOT}/\1/", value)


def _history_path(value: str) -> str:
    return _history_text(value) if value.startswith(HISTORY_PREFIXES) else value
