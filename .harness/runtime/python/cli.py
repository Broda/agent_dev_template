#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_cli.bootstrap import (  # noqa: E402
    run_project_harness_new,
    run_project_harness_validate,
)
from template_cli.bootstrap_update import (  # noqa: E402
    run_project_harness_update_apply,
    run_project_harness_update_dry_run,
)
from template_cli.finalize import run_finalize_project  # noqa: E402
from template_cli.intent_registry import modes_for_command  # noqa: E402
from template_cli.intents import IntentRegistryError, run_render_intent_docs  # noqa: E402
from template_cli.io_helpers import read_mode  # noqa: E402
from template_cli.lab_cli import add_lab_subparsers, dispatch_lab_command  # noqa: E402
from template_cli.plugin_sync import run_sync_plugin_skills  # noqa: E402
from template_cli.release_check import run_harness_release_check  # noqa: E402
from template_cli.render import run_render_development_docs  # noqa: E402
from template_cli.validators import (  # noqa: E402
    run_validate_brainstorming,
    run_validate_development,
    run_validate_governance,
)
from template_cli.workflow_data import normalize_idea_id  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_brainstorming_parser = subparsers.add_parser("validate-brainstorming")
    validate_brainstorming_parser.add_argument("--json", action="store_true")
    validate_development_parser = subparsers.add_parser("validate-development")
    validate_development_parser.add_argument("--json", action="store_true")
    validate_governance_parser = subparsers.add_parser("validate-governance")
    validate_governance_parser.add_argument("--json", action="store_true")
    subparsers.add_parser("render-development-docs")
    subparsers.add_parser("render-intent-docs")
    subparsers.add_parser("sync-plugin-skills")
    subparsers.add_parser("harness-release-check")
    harness_new_parser = subparsers.add_parser("project-harness-new")
    harness_new_parser.add_argument("target")
    harness_new_parser.add_argument("--origin", default="")
    harness_new_parser.add_argument("--no-git", action="store_true")
    harness_update_parser = subparsers.add_parser("project-harness-update")
    harness_update_parser.add_argument("--dry-run", action="store_true")
    harness_update_parser.add_argument("--source-path", default="")
    harness_update_parser.add_argument("--source-commit", default="")
    harness_update_parser.add_argument("--release-version", default="")
    harness_update_parser.add_argument("--apply", action="store_true")
    harness_update_parser.add_argument("--yes", action="store_true")
    harness_update_parser.add_argument("--include-mixed", action="store_true")
    harness_update_parser.add_argument("--json", action="store_true")
    subparsers.add_parser("project-harness-validate")
    finalize_parser = subparsers.add_parser("finalize-project")
    finalize_parser.add_argument("--idea-id", default="", type=normalize_idea_id)
    finalize_parser.add_argument("--write-export", action="store_true")
    finalize_parser.add_argument("--interactive", action="store_true")
    add_lab_subparsers(subparsers)

    return parser


def _lab_command_name(command: str) -> str:
    return command.removeprefix("lab-")


def _enforce_lab_mode(root: Path, command: str) -> int:
    if not command.startswith("lab-"):
        return 0

    lab_command = _lab_command_name(command)
    try:
        allowed_modes = modes_for_command(root, lab_command)
    except IntentRegistryError as exc:
        print(f"Cannot load harness command registry: {exc}", file=sys.stderr)
        return 2

    mode = read_mode(root) or "unknown"
    if mode in allowed_modes:
        return 0

    if allowed_modes:
        allowed_display = ", ".join(sorted(allowed_modes))
    else:
        allowed_display = "no registered modes"
    print(
        f"/lab {lab_command} is not available in {mode} mode (allowed: {allowed_display}).",
        file=sys.stderr,
    )
    print(
        "Check MODE.md and .harness/commands/intent_registry.json before dispatching this command.",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)
    mode_error = _enforce_lab_mode(Path.cwd(), args.command)
    if mode_error:
        return mode_error

    if args.command == "validate-brainstorming":
        return run_validate_brainstorming(Path.cwd(), json_output=args.json)
    if args.command == "validate-development":
        return run_validate_development(Path.cwd(), json_output=args.json)
    if args.command == "validate-governance":
        return run_validate_governance(Path.cwd(), json_output=args.json)
    if args.command == "render-development-docs":
        return run_render_development_docs(Path.cwd())
    if args.command == "render-intent-docs":
        return run_render_intent_docs(Path.cwd())
    if args.command == "sync-plugin-skills":
        return run_sync_plugin_skills(Path.cwd())
    if args.command == "harness-release-check":
        return run_harness_release_check(Path.cwd())
    if args.command == "project-harness-new":
        return run_project_harness_new(
            Path.cwd(),
            args.target,
            origin=args.origin,
            no_git=args.no_git,
        )
    if args.command == "project-harness-validate":
        return run_project_harness_validate(Path.cwd())
    if args.command == "project-harness-update":
        if args.apply == args.dry_run:
            print("project-harness update requires exactly one mode: --dry-run or --apply.", file=sys.stderr)
            return 2
        if args.apply and args.json:
            print("project-harness update --json is only supported with --dry-run.", file=sys.stderr)
            return 2
        if args.apply:
            return run_project_harness_update_apply(
                Path.cwd(),
                source_path=args.source_path,
                source_commit=args.source_commit,
                release_version=args.release_version,
                yes=args.yes,
                include_mixed=args.include_mixed,
            )
        return run_project_harness_update_dry_run(
            Path.cwd(),
            source_path=args.source_path,
            source_commit=args.source_commit,
            release_version=args.release_version,
            json_output=args.json,
        )
    if args.command == "finalize-project":
        return run_finalize_project(
            Path.cwd(),
            args.idea_id or "",
            write_export=args.write_export,
            interactive=args.interactive,
        )
    lab_result = dispatch_lab_command(Path.cwd(), args, remaining)
    if lab_result is not None:
        return lab_result

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
