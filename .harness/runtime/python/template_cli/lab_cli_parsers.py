from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from template_cli.workflow_data import normalize_idea_id


@dataclass(frozen=True)
class ArgumentSpec:
    flags: tuple[str, ...]
    kwargs: dict[str, Any]


def arg(*flags: str, **kwargs: Any) -> ArgumentSpec:
    return ArgumentSpec(flags=flags, kwargs=kwargs)


def idea_arg(**kwargs: Any) -> ArgumentSpec:
    return arg("--idea-id", type=normalize_idea_id, **kwargs)


LAB_COMMAND_ARGUMENTS: dict[str, tuple[ArgumentSpec, ...]] = {
    "lab-note": (
        arg("--topic", required=True),
        arg("--source", default="recent assistant research context"),
        idea_arg(default=""),
        arg("--tags", default=""),
        arg("--summary", action="append", default=[]),
        arg("--summary-file", action="append", default=[]),
        arg("--detail", action="append", default=[]),
        arg("--details-file", action="append", default=[]),
        arg("--fact", action="append", default=[]),
        arg("--facts-file", action="append", default=[]),
        arg("--question", action="append", default=[]),
        arg("--questions-file", action="append", default=[]),
        arg("--link", action="append", default=[]),
        arg("--links-file", action="append", default=[]),
        arg("--no-sync", action="store_true"),
    ),
    "lab-sync": (),
    "lab-status": (arg("--json", action="store_true"),),
    "lab-doctor": (idea_arg(default=""), arg("--json", action="store_true")),
    "lab-audit": (),
    "lab-wiki-render": (),
    "lab-wiki-check": (),
    "lab-adr": (
        arg("--title", required=True),
        arg("--context", action="append", default=[]),
        arg("--decision", required=True),
        arg("--consequence", action="append", default=[]),
        arg("--alternative", action="append", default=[]),
        arg("--status", default="Accepted"),
        arg("--deciders", default=""),
        arg("--supersedes", default=""),
        arg("--date", dest="adr_date", default=""),
    ),
    "lab-evidence": (
        arg("--task", required=True),
        arg("--command", dest="evidence_command", required=True),
        arg("--result", required=True),
        arg("--note", action="append", default=[]),
        arg("--no-complete", action="store_true"),
    ),
    "lab-push": (),
    "lab-commit": (arg("--message", default="brainstorm: milestone update"),),
    "lab-finalize": (
        idea_arg(default=""),
        arg("--write-export", action="store_true"),
        arg("--interactive", action="store_true"),
    ),
    "lab-handoff": (
        idea_arg(default=""),
        arg("--check", action="store_true"),
        arg("--no-sync", action="store_true"),
    ),
    "lab-capture": (
        idea_arg(required=True),
        arg("--title", default=""),
        arg("--owner", default=""),
        arg("--problem", default=""),
        arg("--summary", default=""),
        arg("--scope", default=""),
        arg("--constraints", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-import-idea": (
        idea_arg(default=""),
        arg("--payload-file", default=""),
        arg("--title", default=""),
        arg("--summary", default=""),
        arg("--source", default="external"),
        arg("--source-id", default=""),
        arg("--activate", action="store_true"),
        arg("--create-session", action="store_true"),
        arg("--path-note", default=""),
        arg("--no-sync", action="store_true"),
        arg("--json", action="store_true"),
    ),
    "lab-activate": (
        idea_arg(required=True),
        arg("--title", default=""),
        arg("--owner", default=""),
        arg("--session", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-park": (
        idea_arg(required=True),
        arg("--owner", default=""),
        arg("--reason", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-kill": (
        idea_arg(required=True),
        arg("--owner", default=""),
        arg("--reason", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-path-note": (
        idea_arg(required=True),
        arg("--title", required=True),
        arg("--summary", action="append", default=[]),
        arg("--deferred", default=""),
        arg("--session", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-decide": (
        idea_arg(required=True),
        arg("--decision-id", default=""),
        arg("--owner", default=""),
        arg("--session", default=""),
        arg("--decision-level", default="L2"),
        arg("--situation", default=""),
        arg("--chosen-option", default=""),
        arg("--rationale", default=""),
        arg("--constraints", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-risk": (
        idea_arg(required=True),
        arg("--risk-id", default=""),
        arg("--owner", default=""),
        arg("--session", default=""),
        arg("--statement", default=""),
        arg("--mitigation", default=""),
        arg("--contingency", default=""),
        arg("--probability", default="medium"),
        arg("--impact", default="medium"),
        arg("--no-sync", action="store_true"),
    ),
    "lab-review": (
        idea_arg(required=True),
        arg("--result", required=True),
        arg("--owner", default=""),
        arg("--session", default=""),
        arg("--summary", default=""),
        arg("--outcome", default="revise"),
        arg("--next-action", default=""),
        arg("--no-sync", action="store_true"),
    ),
    "lab-export": (
        idea_arg(required=True),
        arg("--no-sync", action="store_true"),
    ),
}


def add_lab_subparsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    for command, arguments in LAB_COMMAND_ARGUMENTS.items():
        parser = subparsers.add_parser(command)
        parser.add_argument("--root", default="")
        for argument in arguments:
            parser.add_argument(*argument.flags, **argument.kwargs)
