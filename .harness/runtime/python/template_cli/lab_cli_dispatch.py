from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from template_cli.adr import run_lab_adr
from template_cli.evidence import run_lab_evidence
from template_cli.handoff import run_lab_handoff
from template_cli.notes import run_lab_note
from template_cli.sync import run_lab_sync_from_argv
from template_cli.wiki import run_lab_wiki_check, run_lab_wiki_render
from template_cli.workflow import run_lab_audit, run_lab_commit_command, run_lab_finalize, run_lab_push_command
from template_cli.workflow_commands import run_lab_decide, run_lab_path_note, run_lab_review, run_lab_risk
from template_cli.workflow_export import run_lab_export
from template_cli.workflow_idea_commands import (
    run_lab_activate,
    run_lab_capture,
    run_lab_import_idea,
    run_lab_kill,
    run_lab_park,
)
from template_cli.workflow_status import run_lab_doctor, run_lab_status

Dispatcher = Callable[[Path, Any, list[str]], int]


def _dispatch_note(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_note(
        root,
        topic=args.topic,
        source_context=args.source,
        idea_id=args.idea_id,
        tags=args.tags,
        summaries=args.summary,
        summary_files=args.summary_file,
        details=args.detail,
        detail_files=args.details_file,
        facts=args.fact,
        fact_files=args.facts_file,
        questions=args.question,
        question_files=args.questions_file,
        links=args.link,
        link_files=args.links_file,
        no_sync=args.no_sync,
    )


def _dispatch_sync(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_sync_from_argv(root, remaining)


def _dispatch_status(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_status(root, json_output=args.json)


def _dispatch_doctor(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_doctor(root, idea_id=args.idea_id, json_output=args.json)


def _dispatch_audit(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_audit(root)


def _dispatch_wiki_render(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_wiki_render(root)


def _dispatch_wiki_check(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_wiki_check(root)


def _dispatch_adr(root: Path, args: Any, remaining: list[str]) -> int:
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


def _dispatch_evidence(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_evidence(
        root,
        task=args.task,
        command=args.evidence_command,
        result=args.result,
        notes=args.note,
        no_complete=args.no_complete,
    )


def _dispatch_commit(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_commit_command(root, message=args.message)


def _dispatch_push(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_push_command(root)


def _dispatch_finalize(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_finalize(
        root,
        idea_id=args.idea_id,
        write_export=args.write_export,
        interactive=args.interactive,
    )


def _dispatch_handoff(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_handoff(root, idea_id=args.idea_id, check=args.check, no_sync=args.no_sync)


def _dispatch_import_idea(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_import_idea(
        root,
        idea_id=args.idea_id,
        title=args.title,
        summary=args.summary,
        source=args.source,
        source_id=args.source_id,
        payload_file=args.payload_file,
        activate=args.activate,
        create_session=args.create_session,
        path_note=args.path_note,
        no_sync=args.no_sync,
        json_output=args.json,
    )


def _dispatch_capture(root: Path, args: Any, remaining: list[str]) -> int:
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


def _dispatch_activate(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_activate(
        root,
        idea_id=args.idea_id,
        title=args.title,
        owner=args.owner,
        session=args.session,
        no_sync=args.no_sync,
    )


def _dispatch_park(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_park(root, idea_id=args.idea_id, owner=args.owner, reason=args.reason, no_sync=args.no_sync)


def _dispatch_kill(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_kill(root, idea_id=args.idea_id, owner=args.owner, reason=args.reason, no_sync=args.no_sync)


def _dispatch_path_note(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_path_note(
        root,
        idea_id=args.idea_id,
        title=args.title,
        summaries=args.summary,
        deferred=args.deferred,
        session=args.session,
        no_sync=args.no_sync,
    )


def _dispatch_decide(root: Path, args: Any, remaining: list[str]) -> int:
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


def _dispatch_risk(root: Path, args: Any, remaining: list[str]) -> int:
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


def _dispatch_review(root: Path, args: Any, remaining: list[str]) -> int:
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


def _dispatch_export(root: Path, args: Any, remaining: list[str]) -> int:
    return run_lab_export(root, idea_id=args.idea_id, no_sync=args.no_sync)


LAB_COMMAND_DISPATCHERS: dict[str, Dispatcher] = {
    "lab-note": _dispatch_note,
    "lab-sync": _dispatch_sync,
    "lab-status": _dispatch_status,
    "lab-doctor": _dispatch_doctor,
    "lab-audit": _dispatch_audit,
    "lab-wiki-render": _dispatch_wiki_render,
    "lab-wiki-check": _dispatch_wiki_check,
    "lab-adr": _dispatch_adr,
    "lab-evidence": _dispatch_evidence,
    "lab-push": _dispatch_push,
    "lab-commit": _dispatch_commit,
    "lab-finalize": _dispatch_finalize,
    "lab-handoff": _dispatch_handoff,
    "lab-capture": _dispatch_capture,
    "lab-import-idea": _dispatch_import_idea,
    "lab-activate": _dispatch_activate,
    "lab-park": _dispatch_park,
    "lab-kill": _dispatch_kill,
    "lab-path-note": _dispatch_path_note,
    "lab-decide": _dispatch_decide,
    "lab-risk": _dispatch_risk,
    "lab-review": _dispatch_review,
    "lab-export": _dispatch_export,
}


def dispatch_lab_command(root: Path, args: Any, remaining: list[str]) -> int | None:
    dispatcher = LAB_COMMAND_DISPATCHERS.get(args.command)
    if dispatcher is None:
        return None
    return dispatcher(root, args, remaining)
