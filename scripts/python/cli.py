#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_cli.validators import (  # noqa: E402
    run_validate_brainstorming,
    run_validate_development,
    run_validate_governance,
)
from template_cli.notes import run_lab_note  # noqa: E402
from template_cli.render import run_render_development_docs  # noqa: E402
from template_cli.finalize import run_finalize_project  # noqa: E402
from template_cli.sync import run_lab_sync_from_argv  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-brainstorming")
    subparsers.add_parser("validate-development")
    subparsers.add_parser("validate-governance")
    subparsers.add_parser("render-development-docs")
    finalize_parser = subparsers.add_parser("finalize-project")
    finalize_parser.add_argument("--idea-id", default="")
    note_parser = subparsers.add_parser("lab-note")
    note_parser.add_argument("--topic", required=True)
    note_parser.add_argument("--source", default="recent assistant research context")
    note_parser.add_argument("--idea-id", default="")
    note_parser.add_argument("--tags", default="")
    note_parser.add_argument("--summary", action="append", default=[])
    note_parser.add_argument("--no-sync", action="store_true")
    subparsers.add_parser("lab-sync")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command == "validate-brainstorming":
        return run_validate_brainstorming(Path.cwd())
    if args.command == "validate-development":
        return run_validate_development(Path.cwd())
    if args.command == "validate-governance":
        return run_validate_governance(Path.cwd())
    if args.command == "render-development-docs":
        return run_render_development_docs(Path.cwd())
    if args.command == "finalize-project":
        return run_finalize_project(Path.cwd(), args.idea_id or "")
    if args.command == "lab-note":
        return run_lab_note(
            Path.cwd(),
            topic=args.topic,
            source_context=args.source,
            idea_id=args.idea_id,
            tags=args.tags,
            summaries=args.summary,
            no_sync=args.no_sync,
        )
    if args.command == "lab-sync":
        return run_lab_sync_from_argv(Path.cwd(), remaining)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
