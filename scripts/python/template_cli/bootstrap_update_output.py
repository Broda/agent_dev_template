from __future__ import annotations

from pathlib import Path

from template_cli.bootstrap_update_source import source_worktree_state


def _print_update_plan(
    root: Path,
    source_root: Path,
    current_manifest: dict,
    target_manifest: dict,
    plan_with_baseline: tuple[dict[str, list[str]], bool],
) -> None:
    plan, baseline_available = plan_with_baseline
    print("Project harness update dry run")
    print(f"Current project: {root}")
    print(f"Target source: {source_root}")
    print(
        "Current harness: "
        f"{current_manifest.get('harnessVersion', 'unknown')} "
        f"({current_manifest.get('sourceCommit', 'unknown')})"
    )
    print(
        "Target harness: "
        f"{target_manifest.get('harnessVersion', 'unknown')} "
        f"({target_manifest.get('sourceCommit', 'unknown')})"
    )
    print(f"Target source worktree: {source_worktree_state(source_root)}")
    if baseline_available:
        print("Recorded source baseline: resolved")
    else:
        print("Recorded source baseline: unavailable")
    print("Writes: none")
    for label in [
        "harness-owned",
        "mixed-generated",
        "conflicted",
        "missing",
        "removed",
        "added",
        "project-owned-preserved",
        "unchanged",
    ]:
        paths = plan[label]
        print(f"{label}: {len(paths)}")
        for path in paths:
            print(f"  - {path}")
    print("Next commands:")
    print("  apply clean harness-owned updates: ./scripts/project-harness update --apply --source-path <template-checkout> --yes")
    print("  include mixed/generated updates after review: add --include-mixed")
    print("  skip groups: rerun dry-run after adjusting the source or local files")
