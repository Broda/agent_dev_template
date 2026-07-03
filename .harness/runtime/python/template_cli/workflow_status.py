from __future__ import annotations

import json
from pathlib import Path

from template_cli.finalize.helpers import existing_state_value, files_containing
from template_cli.io_helpers import IDEA_ROW_RE, clean_backticks, parse_markdown_table_rows, path_exists, read_mode
from template_cli.workflow_data import (
    FINALIZE_ADVISORY_FIELDS,
    FINALIZE_REQUIRED_FIELDS,
    _collect_session_links,
    _default_owner,
    _extract_catalog_row,
    _find_idea_block,
    _title_from_idea_id,
)
from template_cli.workflow_development_status import development_status_data, run_development_status
from template_cli.workflow_readiness import (
    resolved_finalize_target,
    status_counts,
    status_readiness,
    status_signal_details,
)


def run_lab_status(root: Path, *, json_output: bool = False) -> int:
    mode = read_mode(root) or "unknown"
    if mode == "development":
        if json_output:
            print(json.dumps(development_status_data(root), indent=2, sort_keys=True))
            return 0
        return run_development_status(root)

    status = brainstorming_status_data(root, mode=mode)
    if json_output:
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0

    counts = status["ideas"]["counts"]
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    state_idea_id = status["canonicalState"]["ideaId"]
    state_status = status["canonicalState"]["status"]

    print(f"Mode: {mode}")
    print(
        "Ideas tracked: "
        f"{len(rows)} "
        f"(inbox {counts['inbox']}, active {counts['active']}, parked {counts['parked']}, "
        f"killed {counts['killed']}, finalized {counts['finalized']})"
    )
    if state_idea_id:
        if state_status:
            print(f"Canonical state: {state_status} for {state_idea_id}")
        else:
            print(f"Canonical state: {state_idea_id}")
    else:
        print("Canonical state: no bound idea yet")

    if active:
        print("Active ideas:")
        for cells in active:
            while len(cells) < 2:
                cells.append("")
            print(f"- {cells[0].strip()} ({cells[1].strip() or 'untitled'})")

    finalize = status["finalize"]
    if not finalize["target"]:
        if finalize["targetSource"] == "ambiguous":
            print("Finalize target: ambiguous")
            print("Finalize readiness: blocked")
            print("Missing before finalize: explicit --idea-id or a single active idea")
        else:
            print("Finalize target: none")
            print("Finalize readiness: blocked")
            print("Missing before finalize: capture and activate an idea")
        return 0

    target = finalize["target"]
    print(f"Finalize target: {target['ideaId']} (from {finalize['targetSource']})")
    print(f"Target title: {target['title']}")
    print(f"Target owner: {target['owner']}")
    print(f"Related sessions: {len(target['sessions'])}")
    if target["summarySnapshot"]:
        print(f"Summary snapshot: {target['summarySnapshot']}")
    else:
        print("Summary snapshot: none")

    print(f"Finalize readiness: {finalize['readiness']}")
    if finalize["requiredMissing"]:
        print("Missing before low-friction finalize: " + ", ".join(finalize["requiredMissing"]))
    if finalize["advisoryMissing"]:
        print("Advisories: capture " + ", ".join(finalize["advisoryMissing"]))
    for note in finalize["advisoryPresent"]:
        print(f"Signals: {note}")
    return 0


def brainstorming_status_data(root: Path, *, mode: str | None = None) -> dict:
    mode = mode or read_mode(root) or "unknown"
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    counts = status_counts(rows)
    state_idea_id = existing_state_value(root, "ideaId")
    state_status = existing_state_value(root, "status")
    target_row, target_source = resolved_finalize_target(root, active)
    finalize: dict = {
        "targetSource": target_source,
        "target": None,
        "readiness": "blocked",
        "requiredMissing": [],
        "advisoryMissing": [],
        "advisoryPresent": [],
    }
    if target_row is not None:
        sessions = _collect_session_links(root, target_row["idea_id"], target_row)
        summary_export = clean_backticks(target_row.get("summary_export", ""))
        if summary_export == "_n/a_":
            summary_export = ""
        readiness, required_missing, advisory_missing, advisory_present = status_readiness(root, target_row)
        finalize = {
            "targetSource": target_source,
            "target": {
                "ideaId": target_row["idea_id"],
                "title": target_row.get("title") or _title_from_idea_id(target_row["idea_id"]),
                "owner": target_row.get("owner") or _default_owner(root),
                "sessions": sessions,
                "summarySnapshot": summary_export,
            },
            "readiness": readiness,
            "requiredMissing": required_missing,
            "advisoryMissing": advisory_missing,
            "advisoryPresent": advisory_present,
        }
    return {
        "mode": mode,
        "ideas": {
            "total": len(rows),
            "counts": counts,
            "active": [
                {
                    "ideaId": cells[0].strip() if len(cells) > 0 else "",
                    "title": cells[1].strip() if len(cells) > 1 else "",
                }
                for cells in active
            ],
        },
        "canonicalState": {
            "ideaId": state_idea_id,
            "status": state_status,
            "bound": bool(state_idea_id),
        },
        "finalize": finalize,
    }


def run_lab_doctor(root: Path, *, idea_id: str = "", json_output: bool = False) -> int:
    doctor = lab_doctor_data(root, idea_id=idea_id)
    if json_output:
        print(json.dumps(doctor, indent=2, sort_keys=True))
        return 0

    mode = doctor["mode"]
    print("Finalize doctor")
    print(f"Mode: {mode}")
    print(f"Requested target: {idea_id or 'auto'}")

    if doctor["targetStatus"] == "missing":
        print("Finalize target: missing")
        print(f"Blocked on: idea '{idea_id}' not found in IDEA_CATALOG.md")
        print("Next step: pass a valid --idea-id or capture/activate the intended idea first")
        return 0
    if doctor["targetStatus"] == "ambiguous":
        print("Finalize target: ambiguous")
        print("Candidates:")
        for candidate in doctor["candidates"]:
            print(f"- {candidate['ideaId']} ({candidate['title'] or 'untitled'})")
        print("Blocked on: explicit --idea-id or a single active idea")
        print("Next step: rerun ./scripts/lab doctor --idea-id <idea-id> or reduce active ideas to one")
        return 0
    if doctor["targetStatus"] == "none":
        print("Finalize target: none")
        print("Blocked on: no active or state-bound idea")
        print("Next step: capture and activate an idea, then rerun ./scripts/lab doctor")
        return 0

    target = doctor["target"]
    print(f"Finalize target: {target['ideaId']} (from {doctor['targetSource']})")
    print(f"Target title: {target['title']}")
    print(f"Target owner: {target['owner']}")
    print(f"Finalize readiness: {doctor['readiness']}")
    print("Target evidence:")
    print("- catalog row: IDEA_CATALOG.md")
    if target["ideaRecord"]:
        print(f"- idea record: {target['ideaRecord']}")
    else:
        print("- idea record: not found in idea buckets")
    if target["sessions"]:
        print("- sessions: " + ", ".join(target["sessions"]))
    else:
        print("- sessions: none")
    if target["summarySnapshot"]:
        print(f"- summary snapshot: {target['summarySnapshot']}")
    else:
        print("- summary snapshot: none")

    print("Field checks:")
    for check in doctor["fieldChecks"]:
        if check["name"] == "session history":
            if check["ok"]:
                print(f"- session history: OK via {check['source']}")
            else:
                print("- session history: MISSING")
        elif check["ok"]:
            print(f"- {check['name']}: OK via {check['source']}")
        else:
            print(f"- {check['name']}: MISSING")

    if doctor["advisoryPresent"]:
        print("Signals:")
        for note in doctor["advisoryPresent"]:
            print(f"- {note}")

    if doctor["requiredMissing"]:
        print("Blocked on:")
        for item in doctor["requiredMissing"]:
            print(f"- {item}")
        print(
            "Next step: run ./scripts/lab handoff "
            f"--idea-id {target['ideaId']} --check to see what can be distilled from source material"
        )
        print("Then update the active idea/session or state/project-init.json for anything still missing.")
    elif doctor["advisoryMissing"]:
        print("Advisories:")
        for item in doctor["advisoryMissing"]:
            print(f"- capture {item} for a cleaner finalize record")
        print(f"Next step: finalize can run now with ./scripts/finalize-project --idea-id {target['ideaId']}")
    else:
        print(f"Next step: finalize can run now with ./scripts/finalize-project --idea-id {target['ideaId']}")
    return 0


def lab_doctor_data(root: Path, *, idea_id: str = "") -> dict:
    mode = read_mode(root) or "unknown"
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]

    if idea_id:
        target_row: dict[str, str] | None = _extract_catalog_row(root, idea_id)
        if not target_row:
            return {
                "mode": mode,
                "requestedTarget": idea_id or "auto",
                "targetStatus": "missing",
                "targetSource": "explicit --idea-id",
                "target": None,
                "blockedOn": [f"idea '{idea_id}' not found in IDEA_CATALOG.md"],
                "nextStep": "pass a valid --idea-id or capture/activate the intended idea first",
            }
        target_source = "explicit --idea-id"
    else:
        target_row, target_source = resolved_finalize_target(root, active)

    if target_row is None:
        if target_source == "ambiguous":
            return {
                "mode": mode,
                "requestedTarget": idea_id or "auto",
                "targetStatus": "ambiguous",
                "targetSource": target_source,
                "target": None,
                "candidates": [
                    {
                        "ideaId": cells[0].strip() if len(cells) > 0 else "",
                        "title": cells[1].strip() if len(cells) > 1 else "",
                    }
                    for cells in active
                ],
                "blockedOn": ["explicit --idea-id or a single active idea"],
                "nextStep": "rerun ./scripts/lab doctor --idea-id <idea-id> or reduce active ideas to one",
            }
        else:
            return {
                "mode": mode,
                "requestedTarget": idea_id or "auto",
                "targetStatus": "none",
                "targetSource": target_source,
                "target": None,
                "blockedOn": ["no active or state-bound idea"],
                "nextStep": "capture and activate an idea, then rerun ./scripts/lab doctor",
            }

    resolved_idea_id = target_row["idea_id"]
    idea_lookup = _find_idea_block(root, resolved_idea_id)
    session_files = _collect_session_links(root, resolved_idea_id, target_row)
    hydration_files = [
        root / rel
        for rel in files_containing(root, "ideas", resolved_idea_id) + session_files
        if path_exists(root, rel)
    ]
    readiness, required_missing, advisory_missing, advisory_present = status_readiness(root, target_row)
    summary_export = clean_backticks(target_row.get("summary_export", ""))
    if summary_export == "_n/a_":
        summary_export = ""
    field_checks = [
        {
            "name": "session history",
            "ok": bool(session_files),
            "source": session_files[-1] if session_files else "",
        }
    ]

    for display_name, state_keys, label in FINALIZE_REQUIRED_FIELDS + FINALIZE_ADVISORY_FIELDS:
        value, source = status_signal_details(
            root,
            state_keys=state_keys,
            idea_label=label,
            idea_lookup=idea_lookup,
            hydration_files=hydration_files,
        )
        field_checks.append({"name": display_name, "ok": bool(value), "source": source if value else ""})

    if required_missing:
        next_step = (
            f"run ./scripts/lab handoff --idea-id {resolved_idea_id} --check to see what can be distilled "
            "from source material"
        )
    else:
        next_step = f"finalize can run now with ./scripts/finalize-project --idea-id {resolved_idea_id}"

    return {
        "mode": mode,
        "requestedTarget": idea_id or "auto",
        "targetStatus": "resolved",
        "targetSource": target_source,
        "target": {
            "ideaId": resolved_idea_id,
            "title": target_row.get("title") or _title_from_idea_id(resolved_idea_id),
            "owner": target_row.get("owner") or _default_owner(root),
            "ideaRecord": idea_lookup[0] if idea_lookup is not None else "",
            "sessions": session_files,
            "summarySnapshot": summary_export,
        },
        "readiness": readiness,
        "fieldChecks": field_checks,
        "requiredMissing": required_missing,
        "advisoryMissing": advisory_missing,
        "advisoryPresent": advisory_present,
        "nextStep": next_step,
    }
