from __future__ import annotations

import json
from pathlib import Path

from template_cli.finalize.helpers import STATE_FILE, join_lines
from template_cli.finalize.state import BackupManager
from template_cli.io_helpers import read_text, write_text

FINALIZATION_BACKUP_PATHS = [
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
    ".github/workflows/ci.yml",
    "IDEA_CATALOG.md",
    "NOTES_CATALOG.md",
    "ideas/",
    "sessions/",
    "notes/",
    "exports/",
    ".harness/history/",
    "MODE.md",
]


def _ensure_finalization_dirs(root: Path, *, write_export: bool) -> None:
    (root / "sessions").mkdir(parents=True, exist_ok=True)
    if write_export:
        (root / "exports").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "docs/adr").mkdir(parents=True, exist_ok=True)


def _load_existing_state(root: Path) -> dict:
    state_path = root / STATE_FILE
    if not state_path.exists():
        return {}
    try:
        data = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _backup_finalization_outputs(
    backups: BackupManager,
    *,
    session_path: str,
    export_path: str,
    write_export: bool,
) -> None:
    for relative_path in FINALIZATION_BACKUP_PATHS + [session_path]:
        backups.backup_path(relative_path)
    if write_export:
        backups.backup_path(export_path)


def _write_finalization_session_log(
    root: Path,
    *,
    session_path: str,
    date_stamp: str,
    owner: str,
    idea_id: str,
    export_path: str,
    write_export: bool,
) -> None:
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
