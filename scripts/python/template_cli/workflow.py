from __future__ import annotations

from pathlib import Path

from template_cli.finalize import run_finalize_project
from template_cli.sync import run_lab_commit, run_lab_push
from template_cli.validators import run_validate_governance


def run_lab_audit(root: Path) -> int:
    return run_validate_governance(root)


def run_lab_finalize(root: Path, *, idea_id: str = "", write_export: bool = False, interactive: bool = False) -> int:
    return run_finalize_project(root, idea_id, write_export=write_export, interactive=interactive)


def run_lab_commit_command(root: Path, *, message: str = "brainstorm: milestone update") -> int:
    return run_lab_commit(root, message=message)


def run_lab_push_command(root: Path) -> int:
    return run_lab_push(root)
