from __future__ import annotations

from pathlib import Path

from template_cli.bootstrap.update_apply import _apply_update_source
from template_cli.bootstrap.update_output import _print_update_plan
from template_cli.bootstrap.update_plan import _build_update_plan
from template_cli.bootstrap.update_source import (
    cleanup_update_source,
    resolve_update_source,
)


def run_project_harness_update_dry_run(
    root: Path,
    *,
    source_path: str = "",
    source_commit: str = "",
    release_version: str = "",
    json_output: bool = False,
) -> int:
    resolved = resolve_update_source(root, source_path, source_commit, release_version, apply=False)
    if isinstance(resolved, int):
        return resolved
    source = resolved

    try:
        plan = _build_update_plan(root.resolve(), source.root, source.current_manifest, source.target_manifest)
        _print_update_plan(
            root.resolve(),
            source.root,
            source.current_manifest,
            source.target_manifest,
            plan,
            json_output=json_output,
        )
        return 0
    finally:
        cleanup_update_source(source)


def run_project_harness_update_apply(
    root: Path,
    *,
    source_path: str = "",
    source_commit: str = "",
    release_version: str = "",
    yes: bool = False,
    include_mixed: bool = False,
) -> int:
    resolved = resolve_update_source(root, source_path, source_commit, release_version, apply=True)
    if isinstance(resolved, int):
        return resolved
    try:
        return _apply_update_source(root, resolved, yes=yes, include_mixed=include_mixed)
    finally:
        cleanup_update_source(resolved)
