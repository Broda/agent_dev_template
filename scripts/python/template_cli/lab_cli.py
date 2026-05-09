from __future__ import annotations

from template_cli.lab_cli_dispatch import dispatch_lab_command
from template_cli.lab_cli_parsers import LAB_COMMAND_ARGUMENTS, add_lab_subparsers


__all__ = [
    "LAB_COMMAND_ARGUMENTS",
    "add_lab_subparsers",
    "dispatch_lab_command",
]
