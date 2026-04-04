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
from template_cli.intents import run_render_intent_docs  # noqa: E402
from template_cli.finalize import run_finalize_project  # noqa: E402
from template_cli.sync import run_lab_sync_from_argv  # noqa: E402
from template_cli.workflow import (  # noqa: E402
    run_lab_activate,
    run_lab_audit,
    run_lab_capture,
    run_lab_commit_command,
    run_lab_decide,
    run_lab_doctor,
    run_lab_export,
    run_lab_finalize,
    run_lab_kill,
    run_lab_park,
    run_lab_path_note,
    run_lab_push_command,
    run_lab_review,
    run_lab_risk,
    run_lab_status,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-brainstorming")
    subparsers.add_parser("validate-development")
    subparsers.add_parser("validate-governance")
    subparsers.add_parser("render-development-docs")
    subparsers.add_parser("render-intent-docs")
    finalize_parser = subparsers.add_parser("finalize-project")
    finalize_parser.add_argument("--idea-id", default="")
    finalize_parser.add_argument("--write-export", action="store_true")
    note_parser = subparsers.add_parser("lab-note")
    note_parser.add_argument("--topic", required=True)
    note_parser.add_argument("--source", default="recent assistant research context")
    note_parser.add_argument("--idea-id", default="")
    note_parser.add_argument("--tags", default="")
    note_parser.add_argument("--summary", action="append", default=[])
    note_parser.add_argument("--no-sync", action="store_true")
    subparsers.add_parser("lab-sync")
    subparsers.add_parser("lab-status")
    doctor_parser = subparsers.add_parser("lab-doctor")
    doctor_parser.add_argument("--idea-id", default="")
    subparsers.add_parser("lab-audit")
    push_parser = subparsers.add_parser("lab-push")
    commit_parser = subparsers.add_parser("lab-commit")
    commit_parser.add_argument("--message", default="brainstorm: milestone update")
    lab_finalize_parser = subparsers.add_parser("lab-finalize")
    lab_finalize_parser.add_argument("--idea-id", default="")
    lab_finalize_parser.add_argument("--write-export", action="store_true")

    capture_parser = subparsers.add_parser("lab-capture")
    capture_parser.add_argument("--idea-id", required=True)
    capture_parser.add_argument("--title", default="")
    capture_parser.add_argument("--owner", default="")
    capture_parser.add_argument("--problem", default="")
    capture_parser.add_argument("--summary", default="")
    capture_parser.add_argument("--scope", default="")
    capture_parser.add_argument("--constraints", default="")
    capture_parser.add_argument("--no-sync", action="store_true")

    activate_parser = subparsers.add_parser("lab-activate")
    activate_parser.add_argument("--idea-id", required=True)
    activate_parser.add_argument("--title", default="")
    activate_parser.add_argument("--owner", default="")
    activate_parser.add_argument("--session", default="")
    activate_parser.add_argument("--no-sync", action="store_true")

    park_parser = subparsers.add_parser("lab-park")
    park_parser.add_argument("--idea-id", required=True)
    park_parser.add_argument("--owner", default="")
    park_parser.add_argument("--reason", default="")
    park_parser.add_argument("--no-sync", action="store_true")

    kill_parser = subparsers.add_parser("lab-kill")
    kill_parser.add_argument("--idea-id", required=True)
    kill_parser.add_argument("--owner", default="")
    kill_parser.add_argument("--reason", default="")
    kill_parser.add_argument("--no-sync", action="store_true")

    path_note_parser = subparsers.add_parser("lab-path-note")
    path_note_parser.add_argument("--idea-id", required=True)
    path_note_parser.add_argument("--title", required=True)
    path_note_parser.add_argument("--summary", action="append", default=[])
    path_note_parser.add_argument("--deferred", default="")
    path_note_parser.add_argument("--session", default="")
    path_note_parser.add_argument("--no-sync", action="store_true")

    decide_parser = subparsers.add_parser("lab-decide")
    decide_parser.add_argument("--idea-id", required=True)
    decide_parser.add_argument("--decision-id", default="")
    decide_parser.add_argument("--owner", default="")
    decide_parser.add_argument("--session", default="")
    decide_parser.add_argument("--decision-level", default="L2")
    decide_parser.add_argument("--situation", default="")
    decide_parser.add_argument("--chosen-option", default="")
    decide_parser.add_argument("--rationale", default="")
    decide_parser.add_argument("--constraints", default="")
    decide_parser.add_argument("--no-sync", action="store_true")

    risk_parser = subparsers.add_parser("lab-risk")
    risk_parser.add_argument("--idea-id", required=True)
    risk_parser.add_argument("--risk-id", default="")
    risk_parser.add_argument("--owner", default="")
    risk_parser.add_argument("--session", default="")
    risk_parser.add_argument("--statement", default="")
    risk_parser.add_argument("--mitigation", default="")
    risk_parser.add_argument("--contingency", default="")
    risk_parser.add_argument("--probability", default="medium")
    risk_parser.add_argument("--impact", default="medium")
    risk_parser.add_argument("--no-sync", action="store_true")

    review_parser = subparsers.add_parser("lab-review")
    review_parser.add_argument("--idea-id", required=True)
    review_parser.add_argument("--result", required=True)
    review_parser.add_argument("--owner", default="")
    review_parser.add_argument("--session", default="")
    review_parser.add_argument("--summary", default="")
    review_parser.add_argument("--outcome", default="revise")
    review_parser.add_argument("--next-action", default="")
    review_parser.add_argument("--no-sync", action="store_true")

    export_parser = subparsers.add_parser("lab-export")
    export_parser.add_argument("--idea-id", required=True)
    export_parser.add_argument("--no-sync", action="store_true")

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
    if args.command == "render-intent-docs":
        return run_render_intent_docs(Path.cwd())
    if args.command == "finalize-project":
        return run_finalize_project(Path.cwd(), args.idea_id or "", write_export=args.write_export)
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
    if args.command == "lab-status":
        return run_lab_status(Path.cwd())
    if args.command == "lab-doctor":
        return run_lab_doctor(Path.cwd(), idea_id=args.idea_id)
    if args.command == "lab-audit":
        return run_lab_audit(Path.cwd())
    if args.command == "lab-commit":
        return run_lab_commit_command(Path.cwd(), message=args.message)
    if args.command == "lab-push":
        return run_lab_push_command(Path.cwd())
    if args.command == "lab-finalize":
        return run_lab_finalize(Path.cwd(), idea_id=args.idea_id, write_export=args.write_export)
    if args.command == "lab-capture":
        return run_lab_capture(
            Path.cwd(),
            idea_id=args.idea_id,
            title=args.title,
            owner=args.owner,
            problem=args.problem,
            summary=args.summary,
            scope=args.scope,
            constraints=args.constraints,
            no_sync=args.no_sync,
        )
    if args.command == "lab-activate":
        return run_lab_activate(
            Path.cwd(),
            idea_id=args.idea_id,
            title=args.title,
            owner=args.owner,
            session=args.session,
            no_sync=args.no_sync,
        )
    if args.command == "lab-park":
        return run_lab_park(
            Path.cwd(), idea_id=args.idea_id, owner=args.owner, reason=args.reason, no_sync=args.no_sync
        )
    if args.command == "lab-kill":
        return run_lab_kill(
            Path.cwd(), idea_id=args.idea_id, owner=args.owner, reason=args.reason, no_sync=args.no_sync
        )
    if args.command == "lab-path-note":
        return run_lab_path_note(
            Path.cwd(),
            idea_id=args.idea_id,
            title=args.title,
            summaries=args.summary,
            deferred=args.deferred,
            session=args.session,
            no_sync=args.no_sync,
        )
    if args.command == "lab-decide":
        return run_lab_decide(
            Path.cwd(),
            idea_id=args.idea_id,
            decision_id=args.decision_id,
            owner=args.owner,
            session=args.session,
            decision_level=args.decision_level,
            situation=args.situation,
            chosen_option=args.chosen_option,
            rationale=args.rationale,
            constraints=args.constraints,
            no_sync=args.no_sync,
        )
    if args.command == "lab-risk":
        return run_lab_risk(
            Path.cwd(),
            idea_id=args.idea_id,
            risk_id=args.risk_id,
            owner=args.owner,
            session=args.session,
            statement=args.statement,
            mitigation=args.mitigation,
            contingency=args.contingency,
            probability=args.probability,
            impact=args.impact,
            no_sync=args.no_sync,
        )
    if args.command == "lab-review":
        return run_lab_review(
            Path.cwd(),
            idea_id=args.idea_id,
            result=args.result,
            owner=args.owner,
            session=args.session,
            summary=args.summary,
            outcome=args.outcome,
            next_action=args.next_action,
            no_sync=args.no_sync,
        )
    if args.command == "lab-export":
        return run_lab_export(Path.cwd(), idea_id=args.idea_id, no_sync=args.no_sync)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
