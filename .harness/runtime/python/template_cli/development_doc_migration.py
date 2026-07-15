from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from template_cli.render_capabilities import effective_deferred_scope
from template_cli.render_contract import collect_implementation_contract, format_contract_sections
from template_cli.render_helpers import _related_hydration_files_from_state
from template_cli.render_markers import DEVELOPMENT_DOC_CONTRACT_MARKER

MIGRATION_DOCS = (
    "README.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/ARCHITECTURE.md",
    "docs/ROADMAP.md",
    "docs/adr/ADR-0001-record-architecture-decisions.md",
)
DEFERRED_NONE_PATTERN = re.compile(
    r"(?im)(^(?:Deferred scope:|#{1,6}[ \t]+Deferred Scope)[ \t]*\n(?:[ \t]*\n)?)[ \t]*-[ \t]*None recorded\.[ \t]*$"
)
DEFERRED_INLINE_NONE_PATTERN = re.compile(r"(?im)^Deferred scope:[ \t]*None recorded\.[ \t]*$")


@dataclass
class DevelopmentDocMigration:
    root: Path
    backup_dir: Path
    changed_paths: tuple[Path, ...]

    def rollback(self) -> None:
        for relative_path in self.changed_paths:
            backup = self.backup_dir / relative_path
            if not backup.is_file():
                continue
            destination = self.root / relative_path
            _atomic_copy(backup, destination)


def apply_pending_development_doc_migration(root: Path) -> DevelopmentDocMigration | None:
    """Upgrade legacy generated development semantics without rerendering authored docs."""
    context_path = root / "docs/PROJECT_CONTEXT.md"
    if _mode(root) != "development" or not context_path.is_file():
        return None
    context = context_path.read_text(encoding="utf-8")
    if DEVELOPMENT_DOC_CONTRACT_MARKER in context:
        return None

    state = _load_finalized_state(root)
    if state is None:
        return None
    idea_id = str(state.get("ideaId", "") or "").strip()
    hydration_files = _related_hydration_files_from_state(root, state, idea_id)
    contract = collect_implementation_contract(state, hydration_files)
    deferred_scope = effective_deferred_scope(state)

    updates: dict[Path, str] = {}
    deferred_lines = "\n".join(f"- {item}" for item in deferred_scope)
    for relative_path in MIGRATION_DOCS:
        path = root / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        migrated = content
        if deferred_lines:
            migrated = DEFERRED_NONE_PATTERN.sub(lambda match: match.group(1) + deferred_lines, migrated)
            migrated = DEFERRED_INLINE_NONE_PATTERN.sub(f"Deferred scope:\n\n{deferred_lines}", migrated)
        if relative_path == "docs/PROJECT_CONTEXT.md":
            migrated = _append_authoritative_contract(migrated, contract)
        if migrated != content:
            updates[relative_path] = migrated

    if not updates:
        return None

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_dir = root / ".harness-update-backups" / f"{stamp}-development-docs"
    transaction = DevelopmentDocMigration(root, backup_dir, tuple(updates))
    try:
        for relative_path in updates:
            source = root / relative_path
            backup = backup_dir / relative_path
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup)
        for relative_path, content in updates.items():
            _atomic_write(root / relative_path, content)
    except Exception:
        transaction.rollback()
        raise

    print("Migrated legacy generated development contract sections:")
    for relative_path in updates:
        print(f"- {relative_path}")
    print(f"Backup: {backup_dir.relative_to(root)}")
    print()
    return transaction


def _append_authoritative_contract(content: str, contract: list[tuple[str, list[str]]]) -> str:
    section = (
        "\n\n---\n\n"
        f"{DEVELOPMENT_DOC_CONTRACT_MARKER}\n\n"
        "# Harness-Managed Semantic Contract\n\n"
        "This authoritative generated section preserves the finalized implementation contract. "
        "Use `./scripts/render-development-docs` to regenerate all development surfaces when ready.\n\n"
        f"{format_contract_sections(contract, heading_level=2)}\n"
    )
    return content.rstrip() + section


def _mode(root: Path) -> str:
    path = root / "MODE.md"
    if not path.is_file():
        return ""
    match = re.search(r"(?im)^Current mode:\s*(brainstorming|development)\s*$", path.read_text(encoding="utf-8"))
    return match.group(1).lower() if match else ""


def _load_finalized_state(root: Path) -> dict | None:
    path = root / "state/project-init.json"
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(state, dict) or state.get("status") != "finalized":
        return None
    return state


def _atomic_write(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, prefix=".harness-doc-", delete=False
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        shutil.copymode(destination, temp_path)
        os.replace(temp_path, destination)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=destination.parent, prefix=".harness-doc-restore-")
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)
