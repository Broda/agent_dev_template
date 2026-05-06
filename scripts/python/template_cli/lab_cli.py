from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from template_cli.adr import run_lab_adr
from template_cli.evidence import run_lab_evidence
from template_cli.notes import run_lab_note
from template_cli.sync import run_lab_sync_from_argv
from template_cli.wiki import run_lab_wiki_check, run_lab_wiki_render
from template_cli.workflow import (
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


def add_lab_subparsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
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
    subparsers.add_parser("lab-wiki-render")
    subparsers.add_parser("lab-wiki-check")

    adr_parser = subparsers.add_parser("lab-adr")
    adr_parser.add_argument("--title", required=True)
    adr_parser.add_argument("--context", action="append", default=[])
    adr_parser.add_argument("--decision", required=True)
    adr_parser.add_argument("--consequence", action="append", default=[])
    adr_parser.add_argument("--alternative", action="append", default=[])
    adr_parser.add_argument("--status", default="Accepted")
    adr_parser.add_argument("--deciders", default="")
    adr_parser.add_argument("--supersedes", default="")
    adr_parser.add_argument("--date", dest="adr_date", default="")

    evidence_parser = subparsers.add_parser("lab-evidence")
    evidence_parser.add_argument("--task", required=True)
    evidence_parser.add_argument("--command", dest="evidence_command", required=True)
    evidence_parser.add_argument("--result", required=True)
    evidence_parser.add_argument("--note", action="append", default=[])
    evidence_parser.add_argument("--no-complete", action="store_true")

    subparsers.add_parser("lab-push")
    commit_parser = subparsers.add_parser("lab-commit")
    commit_parser.add_argument("--message", default="brainstorm: milestone update")
    lab_finalize_parser = subparsers.add_parser("lab-finalize")
    lab_finalize_parser.add_argument("--idea-id", default="")
    lab_finalize_parser.add_argument("--write-export", action="store_true")
    lab_finalize_parser.add_argument("--interactive", action="store_true")

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


def dispatch_lab_command(root: Path, args: Any, remaining: list[str]) -> int | None:
    if args.command == "lab-note":
        return run_lab_note(
            root,
            topic=args.topic,
            source_context=args.source,
            idea_id=args.idea_id,
            tags=args.tags,
            summaries=args.summary,
            no_sync=args.no_sync,
        )
    if args.command == "lab-sync":
        return run_lab_sync_from_argv(root, remaining)
    if args.command == "lab-status":
        return run_lab_status(root)
    if args.command == "lab-doctor":
        return run_lab_doctor(root, idea_id=args.idea_id)
    if args.command == "lab-audit":
        return run_lab_audit(root)
    if args.command == "lab-wiki-render":
        return run_lab_wiki_render(root)
    if args.command == "lab-wiki-check":
        return run_lab_wiki_check(root)
    if args.command == "lab-adr":
        return run_lab_adr(
            root,
            title=args.title,
            context=args.context,
            decision=args.decision,
            consequence=args.consequence,
            alternative=args.alternative,
            status=args.status,
            deciders=args.deciders,
            supersedes=args.supersedes,
            adr_date=args.adr_date,
        )
    if args.command == "lab-evidence":
        return run_lab_evidence(
            root,
            task=args.task,
            command=args.evidence_command,
            result=args.result,
            notes=args.note,
            no_complete=args.no_complete,
        )
    if args.command == "lab-commit":
        return run_lab_commit_command(root, message=args.message)
    if args.command == "lab-push":
        return run_lab_push_command(root)
    if args.command == "lab-finalize":
        return run_lab_finalize(
            root,
            idea_id=args.idea_id,
            write_export=args.write_export,
            interactive=args.interactive,
        )
    if args.command == "lab-capture":
        return run_lab_capture(
            root,
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
            root,
            idea_id=args.idea_id,
            title=args.title,
            owner=args.owner,
            session=args.session,
            no_sync=args.no_sync,
        )
    if args.command == "lab-park":
        return run_lab_park(root, idea_id=args.idea_id, owner=args.owner, reason=args.reason, no_sync=args.no_sync)
    if args.command == "lab-kill":
        return run_lab_kill(root, idea_id=args.idea_id, owner=args.owner, reason=args.reason, no_sync=args.no_sync)
    if args.command == "lab-path-note":
        return run_lab_path_note(
            root,
            idea_id=args.idea_id,
            title=args.title,
            summaries=args.summary,
            deferred=args.deferred,
            session=args.session,
            no_sync=args.no_sync,
        )
    if args.command == "lab-decide":
        return run_lab_decide(
            root,
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
            root,
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
            root,
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
        return run_lab_export(root, idea_id=args.idea_id, no_sync=args.no_sync)
    return None
