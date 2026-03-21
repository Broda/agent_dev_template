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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-brainstorming")
    subparsers.add_parser("validate-development")
    subparsers.add_parser("validate-governance")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-brainstorming":
        return run_validate_brainstorming(Path.cwd())
    if args.command == "validate-development":
        return run_validate_development(Path.cwd())
    if args.command == "validate-governance":
        return run_validate_governance(Path.cwd())

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
