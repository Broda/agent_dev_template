from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

from template_cli.bootstrap.update_plan import requires_target_planner_transition
from template_cli.bootstrap.update_source import source_worktree_state


def _print_update_plan(
    root: Path,
    source_root: Path,
    current_manifest: dict,
    target_manifest: dict,
    plan_with_baseline: tuple[dict[str, list[str]], bool],
    *,
    json_output: bool = False,
) -> None:
    plan, baseline_available = plan_with_baseline
    transition_required = requires_target_planner_transition(current_manifest, target_manifest)
    transition_apply = shlex.join(
        [
            sys.executable,
            str(source_root / ".harness/runtime/python/cli.py"),
            "project-harness-update",
            "--apply",
            "--source-path",
            str(source_root),
            "--yes",
        ]
    )
    if json_output:
        print(
            json.dumps(
                {
                    "command": "project-harness update --dry-run",
                    "currentProject": root.as_posix(),
                    "targetSource": source_root.as_posix(),
                    "currentHarness": {
                        "version": current_manifest.get("harnessVersion", "unknown"),
                        "sourceCommit": current_manifest.get("sourceCommit", "unknown"),
                    },
                    "targetHarness": {
                        "version": target_manifest.get("harnessVersion", "unknown"),
                        "sourceCommit": target_manifest.get("sourceCommit", "unknown"),
                    },
                    "targetSourceWorktree": source_worktree_state(source_root),
                    "recordedSourceBaseline": "resolved" if baseline_available else "unavailable",
                    "writes": "none",
                    "plannerTransition": {
                        "required": transition_required,
                        "reason": (
                            "current manifest broadly owns scripts/; continue with the target planner"
                            if transition_required
                            else ""
                        ),
                        "applyCommand": transition_apply if transition_required else "",
                    },
                    "plan": plan,
                    "nextCommands": {
                        "applyCleanHarnessOwned": (
                            "./scripts/project-harness update --apply --source-path <template-checkout> --yes"
                        ),
                        "includeMixedGenerated": "add --include-mixed",
                        "skipGroups": "rerun dry-run after adjusting the source or local files",
                    },
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

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
    if transition_required:
        print("Planner transition: required (current manifest broadly owns scripts/)")
        print(f"Continue with target planner: {transition_apply}")
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
    apply_command = (
        transition_apply
        if transition_required
        else ("./scripts/project-harness update --apply --source-path <template-checkout> --yes")
    )
    print(f"  apply clean harness-owned updates: {apply_command}")
    print("  include mixed/generated updates after review: add --include-mixed")
    print("  skip groups: rerun dry-run after adjusting the source or local files")
