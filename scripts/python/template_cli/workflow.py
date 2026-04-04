from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

from template_cli.finalize import (
    STATE_FILE,
    _write_summary_export,
    existing_state_value,
    files_containing,
    first_value_for_label,
    infer_project_type,
    run_finalize_project,
)
from template_cli.sync import run_lab_commit, run_lab_push, run_lab_sync
from template_cli.validators import (
    IDEA_ROW_RE,
    clean_backticks,
    parse_markdown_table_rows,
    path_exists,
    read_mode,
    read_text,
    run_validate_governance,
    write_text,
)


BUCKET_FILES = {
    "inbox": "ideas/_inbox.md",
    "active": "ideas/_active.md",
    "parked": "ideas/_parked.md",
    "killed": "ideas/_killed.md",
    "finalized": "ideas/_active.md",
}
IDEA_BLOCK_RE = re.compile(r"(?ms)^## Idea:.*?(?=^## Idea:|\Z)")
SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def _trim(value: str | None) -> str:
    return (value or "").strip()


def _today() -> str:
    return datetime.now().date().isoformat()


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _default_owner(root: Path) -> str:
    result = subprocess.run(
        ["git", "config", "--get", "user.name"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return _trim(result.stdout) or "unassigned"


def _title_from_idea_id(idea_id: str) -> str:
    stem = idea_id.replace("idea-", "").replace("-", " ").strip()
    return stem.title() or idea_id


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", slug)


def _default_adr_references(root: Path) -> list[str]:
    candidates = [
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        "brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md",
    ]
    return [candidate for candidate in candidates if path_exists(root, candidate)]


def _strip_wrapping_backticks(value: str) -> str:
    stripped = _trim(value)
    if stripped.startswith("`") and stripped.endswith("`") and stripped.count("`") == 2:
        return stripped[1:-1]
    return stripped


def _extract_label_from_text(block: str, label: str) -> str:
    pattern = re.compile(rf"^\s*[-*]\s+{re.escape(label)}:\s*(.*?)\s*$")
    value = ""
    for line in block.splitlines():
        match = pattern.match(line)
        if match:
            value = _strip_wrapping_backticks(match.group(1))
    return value


def _block_matches_idea_id(block: str, idea_id: str) -> bool:
    return _extract_label_from_text(block, "Idea ID") == idea_id


def _extract_catalog_row(root: Path, idea_id: str) -> dict[str, str]:
    catalog_path = root / "IDEA_CATALOG.md"
    if not catalog_path.exists():
        return {}
    for cells in parse_markdown_table_rows(catalog_path, IDEA_ROW_RE):
        if cells and cells[0].strip() == idea_id:
            while len(cells) < 7:
                cells.append("")
            return {
                "idea_id": cells[0].strip(),
                "title": cells[1].strip(),
                "status": cells[2].strip(),
                "owner": cells[3].strip(),
                "sessions": cells[4].strip(),
                "summary_export": clean_backticks(cells[5].strip()),
                "notes": cells[6].strip(),
            }
    return {}


def _render_catalog_row(
    idea_id: str,
    title: str,
    status: str,
    owner: str,
    sessions: list[str],
    summary_export: str,
    notes: str,
) -> str:
    sessions_cell = ", ".join(f"`{value}`" for value in sessions) if sessions else "_none_"
    export_cell = f"`{summary_export}`" if _trim(summary_export) else "_n/a_"
    return (
        f"| {idea_id} | {title} | {status} | {owner} | {sessions_cell} | {export_cell} |"
        f" {notes or '_none_'} |"
    )


def _upsert_catalog_row(
    root: Path,
    *,
    idea_id: str,
    title: str,
    status: str,
    owner: str,
    sessions: list[str],
    summary_export: str,
    notes: str,
) -> None:
    catalog_path = root / "IDEA_CATALOG.md"
    lines = read_text(catalog_path).splitlines()
    row = _render_catalog_row(idea_id, title, status, owner, sessions, summary_export, notes)
    updated: list[str] = []
    inserted = False
    for line in lines:
        if IDEA_ROW_RE.search(line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells and cells[0] == idea_id:
                updated.append(row)
                inserted = True
                continue
            updated.append(line)
            continue
        if line.startswith("| _none yet_"):
            if not inserted:
                updated.append(row)
                inserted = True
            continue
        updated.append(line)

    if not inserted:
        updated.append(row)
    write_text(catalog_path, "\n".join(updated) + "\n")


def _read_idea_blocks(path: Path) -> tuple[str, list[str]]:
    content = read_text(path)
    matches = list(IDEA_BLOCK_RE.finditer(content))
    if not matches:
        return content.rstrip() + "\n", []
    header = content[: matches[0].start()].rstrip() + "\n"
    blocks = [match.group(0).strip() for match in matches]
    return header, blocks


def _write_idea_blocks(path: Path, header: str, blocks: list[str]) -> None:
    body = header.rstrip() + "\n\n---\n"
    if blocks:
        body += "\n\n" + "\n\n".join(blocks).strip() + "\n"
    write_text(path, body)


def _find_idea_block(root: Path, idea_id: str) -> tuple[str, str] | None:
    for status, relpath in BUCKET_FILES.items():
        if status == "finalized":
            continue
        path = root / relpath
        if not path.exists():
            continue
        _, blocks = _read_idea_blocks(path)
        for block in blocks:
            if _block_matches_idea_id(block, idea_id):
                return relpath, block
    return None


def _remove_idea_from_buckets(root: Path, idea_id: str) -> None:
    for status, relpath in BUCKET_FILES.items():
        if status == "finalized":
            continue
        path = root / relpath
        if not path.exists():
            continue
        header, blocks = _read_idea_blocks(path)
        kept = [block for block in blocks if not _block_matches_idea_id(block, idea_id)]
        if len(kept) != len(blocks):
            _write_idea_blocks(path, header, kept)


def _append_idea_to_bucket(root: Path, status: str, block: str) -> None:
    path = root / BUCKET_FILES[status]
    header, blocks = _read_idea_blocks(path)
    blocks.append(block.strip())
    _write_idea_blocks(path, header, blocks)


def _collect_session_links(root: Path, idea_id: str, catalog_row: dict[str, str]) -> list[str]:
    session_links: list[str] = []
    sessions_col = catalog_row.get("sessions", "")
    session_links.extend(re.findall(r"sessions/[^`,\s]+\.md", sessions_col))
    for match in files_containing(root, "sessions", idea_id):
        if match not in session_links:
            session_links.append(match)
    return session_links


def _render_idea_block(fields: dict[str, str]) -> str:
    return "\n".join(
        [
            f"## Idea: {fields['title']}",
            "",
            "## Metadata",
            "",
            f"- Idea ID: `{fields['idea_id']}`",
            f"- Codename (kebab case): {fields['codename']}",
            f"- Title: {fields['title']}",
            f"- Date: {fields['date']}",
            f"- Owner: {fields['owner']}",
            f"- Status: {fields['status']}",
            f"- Sensitivity: {fields['sensitivity']}",
            "",
            "## Problem Definition",
            "",
            f"- Problem statement: {fields['problem_statement']}",
            f"- Affected users/personas: {fields['affected_users']}",
            f"- Why now: {fields['why_now']}",
            f"- Current alternatives: {fields['current_alternatives']}",
            "",
            "## Hypotheses",
            "",
            f"- Value hypothesis: {fields['value_hypothesis']}",
            f"- Adoption hypothesis: {fields['adoption_hypothesis']}",
            f"- Feasibility hypothesis: {fields['feasibility_hypothesis']}",
            "",
            "## Proposed Scope",
            "",
            f"- MVP scope: {fields['mvp_scope']}",
            f"- Out of scope: {fields['out_of_scope']}",
            f"- Assumptions: {fields['assumptions']}",
            f"- Constraints: {fields['constraints']}",
            "",
            "## Governance Rationale",
            "",
            f"- Why this idea should be pursued: {fields['why_pursue']}",
            f"- Strategic alignment: {fields['strategic_alignment']}",
            f"- Non-goals: {fields['non_goals']}",
            "",
            "## Risks and Unknowns",
            "",
            f"- Top risks (link to risk entries): {fields['top_risks']}",
            f"- Open questions: {fields['open_questions']}",
            f"- Dependency concerns: {fields['dependency_concerns']}",
            "",
            "## Decisions and ADR Links",
            "",
            f"- Related decisions: {fields['related_decisions']}",
            f"- Related ADRs (`docs/adr/ADR-XXXX-*.md`): {fields['related_adrs']}",
            "",
            "## Validation Plan",
            "",
            f"- Evidence needed: {fields['evidence_needed']}",
            f"- Test plan: {fields['test_plan']}",
            f"- Success criteria: {fields['success_criteria']}",
            f"- Failure criteria: {fields['failure_criteria']}",
            "",
            "## Review and Export Readiness",
            "",
            f"- Latest review outcome: {fields['latest_review_outcome']}",
            f"- Conditions to finalize: {fields['conditions_to_finalize']}",
            f"- Optional summary export path: {fields['summary_export']}",
            "",
            "## Traceability",
            "",
            f"- Session links: {fields['session_links']}",
            "- Catalog reference: `IDEA_CATALOG.md`",
        ]
    )


def _build_idea_fields(
    root: Path,
    idea_id: str,
    *,
    title: str = "",
    owner: str = "",
    status: str = "",
    session_links: list[str] | None = None,
    summary_export: str = "",
    problem_statement: str = "",
    solution_summary: str = "",
    mvp_scope: str = "",
    constraints: str = "",
    why_now: str = "",
    top_risks: str = "",
) -> dict[str, str]:
    existing = _find_idea_block(root, idea_id)
    block = existing[1] if existing else ""
    catalog_row = _extract_catalog_row(root, idea_id)
    session_links = session_links or _collect_session_links(root, idea_id, catalog_row)
    block_title = _extract_label_from_text(block, "Title")
    block_owner = _extract_label_from_text(block, "Owner")
    fields = {
        "idea_id": idea_id,
        "codename": _extract_label_from_text(block, "Codename (kebab case)") or idea_id.replace("idea-", ""),
        "title": title or block_title or catalog_row.get("title") or _title_from_idea_id(idea_id),
        "date": _extract_label_from_text(block, "Date") or _today(),
        "owner": owner or block_owner or catalog_row.get("owner") or _default_owner(root),
        "status": status or _extract_label_from_text(block, "Status") or catalog_row.get("status") or "inbox",
        "sensitivity": _extract_label_from_text(block, "Sensitivity") or "Internal",
        "problem_statement": problem_statement or _extract_label_from_text(block, "Problem statement"),
        "affected_users": _extract_label_from_text(block, "Affected users/personas"),
        "why_now": why_now or _extract_label_from_text(block, "Why now"),
        "current_alternatives": _extract_label_from_text(block, "Current alternatives"),
        "value_hypothesis": solution_summary or _extract_label_from_text(block, "Value hypothesis"),
        "adoption_hypothesis": _extract_label_from_text(block, "Adoption hypothesis"),
        "feasibility_hypothesis": _extract_label_from_text(block, "Feasibility hypothesis"),
        "mvp_scope": mvp_scope or _extract_label_from_text(block, "MVP scope"),
        "out_of_scope": _extract_label_from_text(block, "Out of scope"),
        "assumptions": _extract_label_from_text(block, "Assumptions"),
        "constraints": constraints or _extract_label_from_text(block, "Constraints"),
        "why_pursue": _extract_label_from_text(block, "Why this idea should be pursued"),
        "strategic_alignment": _extract_label_from_text(block, "Strategic alignment"),
        "non_goals": _extract_label_from_text(block, "Non-goals"),
        "top_risks": top_risks or _extract_label_from_text(block, "Top risks (link to risk entries)"),
        "open_questions": _extract_label_from_text(block, "Open questions"),
        "dependency_concerns": _extract_label_from_text(block, "Dependency concerns"),
        "related_decisions": _extract_label_from_text(block, "Related decisions"),
        "related_adrs": _extract_label_from_text(block, "Related ADRs (`docs/adr/ADR-XXXX-*.md`)"),
        "evidence_needed": _extract_label_from_text(block, "Evidence needed"),
        "test_plan": _extract_label_from_text(block, "Test plan"),
        "success_criteria": _extract_label_from_text(block, "Success criteria"),
        "failure_criteria": _extract_label_from_text(block, "Failure criteria"),
        "latest_review_outcome": _extract_label_from_text(block, "Latest review outcome") or "conditional-pass",
        "conditions_to_finalize": _extract_label_from_text(block, "Conditions to finalize"),
        "summary_export": summary_export or _extract_label_from_text(block, "Optional summary export path"),
        "session_links": ", ".join(f"`{value}`" for value in session_links) if session_links else "_none_",
    }
    return fields


def _next_sequence_id(root: Path, prefix: str) -> str:
    pattern = re.compile(rf"{re.escape(prefix)}-(\d+)")
    highest = 0
    for path in sorted((root / "sessions").glob("*.md")) if (root / "sessions").exists() else []:
        for match in pattern.findall(read_text(path)):
            highest = max(highest, int(match))
    return f"{prefix}-{highest + 1:03d}"


def _ensure_session_file(root: Path, idea_id: str, title: str, owner: str, explicit_path: str = "") -> str:
    if explicit_path:
        session_path = explicit_path
    else:
        row = _extract_catalog_row(root, idea_id)
        existing = _collect_session_links(root, idea_id, row)
        session_path = existing[-1] if existing else f"sessions/{_today()}_{idea_id}.md"

    full_path = root / session_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    if not full_path.exists():
        content = "\n".join(
            [
                "# Brainstorming Session",
                "",
                "## Metadata",
                "",
                f"- Date: {_today()}",
                f"- Idea ID: `{idea_id}`",
                f"- Title: {title}",
                f"- Owner: {owner}",
                "- Status: active",
                "",
                "## Current Focus",
                "",
                "- ",
                "",
                "## Exploration Path Notes",
                "",
                "## Decisions",
                "",
                "## Risks",
                "",
                "## Review Gates",
                "",
            ]
        )
        write_text(full_path, content)
    return session_path


def _append_under_section(path: Path, section_title: str, block: str) -> None:
    lines = read_text(path).splitlines()
    block_lines = block.strip().splitlines()
    normalized_title = re.sub(r"\s+", " ", section_title.strip())
    section_start = -1
    section_end = len(lines)

    for index, line in enumerate(lines):
        match = SECTION_HEADING_RE.match(line)
        if not match:
            continue
        heading_title = re.sub(r"\s+", " ", match.group(1).strip())
        if heading_title == normalized_title:
            section_start = index

    if section_start >= 0:
        for index in range(section_start + 1, len(lines)):
            if SECTION_HEADING_RE.match(lines[index]):
                section_end = index
                break

        body = list(lines[section_start + 1 : section_end])
        while body and not body[-1].strip():
            body.pop()
        if not body:
            body = [""]
        elif body[-1].strip():
            body.append("")
        body.extend(block_lines)
        body.append("")
        updated_lines = lines[: section_start + 1] + body + lines[section_end:]
        write_text(path, "\n".join(updated_lines).rstrip() + "\n")
        return

    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        lines.append("")
    lines.append(f"## {section_title}")
    lines.append("")
    lines.extend(block_lines)
    lines.append("")
    write_text(path, "\n".join(lines).rstrip() + "\n")


def _status_counts(rows: list[list[str]]) -> dict[str, int]:
    counts = {name: 0 for name in ["inbox", "active", "parked", "killed", "finalized"]}
    for cells in rows:
        if len(cells) > 2:
            status = cells[2].strip()
            if status in counts:
                counts[status] += 1
    return counts


def _resolved_finalize_target(root: Path, active_rows: list[list[str]]) -> tuple[dict[str, str] | None, str]:
    state_idea_id = existing_state_value(root, "ideaId")
    if state_idea_id:
        row = _extract_catalog_row(root, state_idea_id)
        if row.get("idea_id"):
            return row, "canonical state"

    if len(active_rows) == 1:
        idea_id = active_rows[0][0].strip()
        row = _extract_catalog_row(root, idea_id)
        if row.get("idea_id"):
            return row, "single active idea"

    if len(active_rows) > 1:
        return None, "ambiguous"
    return None, "none"


def _status_signal(
    root: Path,
    *,
    state_keys: list[str],
    idea_block: str,
    hydration_files: list[Path],
    label: str = "",
) -> str:
    for state_key in state_keys:
        value = existing_state_value(root, state_key)
        if value:
            return value
    if label:
        direct_value = _extract_label_from_text(idea_block, label)
        if direct_value:
            return direct_value
        hydrated_value = first_value_for_label(hydration_files, label)
        if hydrated_value:
            return hydrated_value
    return ""


def _status_readiness(root: Path, row: dict[str, str]) -> tuple[str, list[str], list[str], list[str]]:
    idea_id = row["idea_id"]
    idea_lookup = _find_idea_block(root, idea_id)
    idea_block = idea_lookup[1] if idea_lookup else ""
    session_files = _collect_session_links(root, idea_id, row)
    hydration_files = [
        root / rel
        for rel in files_containing(root, "ideas", idea_id) + session_files
        if path_exists(root, rel)
    ]

    required_missing: list[str] = []
    advisory_missing: list[str] = []

    if not session_files:
        required_missing.append("session history")

    field_checks = [
        ("problem statement", ["product.problemStatement", "purpose"], "Problem statement"),
        ("MVP scope", ["product.mvpScope"], "MVP scope"),
        ("build command", ["commands.build"], ""),
        ("run command", ["commands.run"], ""),
        ("test command", ["commands.test"], ""),
    ]
    for display_name, state_keys, label in field_checks:
        if not _status_signal(root, state_keys=state_keys, idea_block=idea_block, hydration_files=hydration_files, label=label):
            required_missing.append(display_name)

    advisory_checks = [
        ("latest review outcome", ["governance.latestReviewOutcome"], "Latest review outcome"),
        ("top risks", ["governance.topRisks"], "Top risks (link to risk entries)"),
    ]
    for display_name, state_keys, label in advisory_checks:
        if not _status_signal(root, state_keys=state_keys, idea_block=idea_block, hydration_files=hydration_files, label=label):
            advisory_missing.append(display_name)

    summary_export = clean_backticks(row.get("summary_export", ""))
    if summary_export and summary_export != "_n/a_":
        advisory_present = [f"summary snapshot: {summary_export}"]
    else:
        advisory_present = []

    if required_missing:
        return "needs-input", required_missing, advisory_missing, advisory_present
    if advisory_missing:
        return "ready-with-advisories", required_missing, advisory_missing, advisory_present
    return "ready", required_missing, advisory_missing, advisory_present


def _sync(root: Path, *, message: str, files: list[str], no_sync: bool) -> int:
    if no_sync:
        return 0
    mode = read_mode(root) or "brainstorming"
    return run_lab_sync(
        root,
        message=f"{mode}: {message}",
        quiet=True,
        no_warn_push_failure=True,
        files=files,
    )


def run_lab_status(root: Path) -> int:
    mode = read_mode(root) or "unknown"
    rows = parse_markdown_table_rows(root / "IDEA_CATALOG.md", IDEA_ROW_RE)
    active = [cells for cells in rows if len(cells) > 2 and cells[2].strip() == "active"]
    counts = _status_counts(rows)
    state_idea_id = existing_state_value(root, "ideaId")
    state_status = existing_state_value(root, "status")

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

    target_row, target_source = _resolved_finalize_target(root, active)
    if target_row is None:
        if target_source == "ambiguous":
            print("Finalize target: ambiguous")
            print("Finalize readiness: blocked")
            print("Missing before finalize: explicit --idea-id or a single active idea")
        else:
            print("Finalize target: none")
            print("Finalize readiness: blocked")
            print("Missing before finalize: capture and activate an idea")
        return 0

    sessions = _collect_session_links(root, target_row["idea_id"], target_row)
    print(f"Finalize target: {target_row['idea_id']} (from {target_source})")
    print(f"Target title: {target_row.get('title') or _title_from_idea_id(target_row['idea_id'])}")
    print(f"Target owner: {target_row.get('owner') or _default_owner(root)}")
    print(f"Related sessions: {len(sessions)}")
    summary_export = clean_backticks(target_row.get("summary_export", ""))
    if summary_export and summary_export != "_n/a_":
        print(f"Summary snapshot: {summary_export}")
    else:
        print("Summary snapshot: none")

    readiness, required_missing, advisory_missing, advisory_present = _status_readiness(root, target_row)
    print(f"Finalize readiness: {readiness}")
    if required_missing:
        print("Missing before low-friction finalize: " + ", ".join(required_missing))
    if advisory_missing:
        print("Advisories: capture " + ", ".join(advisory_missing))
    for note in advisory_present:
        print(f"Signals: {note}")
    return 0


def run_lab_capture(
    root: Path,
    *,
    idea_id: str,
    title: str = "",
    owner: str = "",
    problem: str = "",
    summary: str = "",
    scope: str = "",
    constraints: str = "",
    no_sync: bool = False,
) -> int:
    fields = _build_idea_fields(
        root,
        idea_id,
        title=title,
        owner=owner,
        status="inbox",
        problem_statement=problem,
        solution_summary=summary,
        mvp_scope=scope,
        constraints=constraints,
    )
    block = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, "inbox", block)
    row = _extract_catalog_row(root, idea_id)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status="inbox",
        owner=fields["owner"],
        sessions=_collect_session_links(root, idea_id, row),
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES["inbox"], "IDEA_CATALOG.md"]
    sync_code = _sync(root, message=f"capture {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Idea captured: {idea_id}")
    return 0


def run_lab_activate(
    root: Path,
    *,
    idea_id: str,
    title: str = "",
    owner: str = "",
    session: str = "",
    no_sync: bool = False,
) -> int:
    current_owner = owner or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, title or _title_from_idea_id(idea_id), current_owner, session)
    row = _extract_catalog_row(root, idea_id)
    sessions = _collect_session_links(root, idea_id, row)
    if session_path not in sessions:
        sessions.append(session_path)
    fields = _build_idea_fields(
        root,
        idea_id,
        title=title,
        owner=current_owner,
        status="active",
        session_links=sessions,
    )
    block = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, "active", block)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status="active",
        owner=fields["owner"],
        sessions=sessions,
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES["active"], "IDEA_CATALOG.md", session_path]
    sync_code = _sync(root, message=f"activate {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Idea activated: {idea_id}")
    print(f"Session: {session_path}")
    return 0


def _transition_idea_state(
    root: Path,
    *,
    idea_id: str,
    status: str,
    owner: str = "",
    note: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    sessions = _collect_session_links(root, idea_id, row)
    fields = _build_idea_fields(
        root,
        idea_id,
        owner=owner or row.get("owner") or _default_owner(root),
        status=status,
        session_links=sessions,
    )
    if note:
        fields["open_questions"] = note
    block = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, status, block)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status=status,
        owner=fields["owner"],
        sessions=sessions,
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES[status], "IDEA_CATALOG.md"]
    sync_code = _sync(root, message=f"{status} {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Idea marked {status}: {idea_id}")
    return 0


def run_lab_park(root: Path, *, idea_id: str, owner: str = "", reason: str = "", no_sync: bool = False) -> int:
    return _transition_idea_state(root, idea_id=idea_id, status="parked", owner=owner, note=reason, no_sync=no_sync)


def run_lab_kill(root: Path, *, idea_id: str, owner: str = "", reason: str = "", no_sync: bool = False) -> int:
    return _transition_idea_state(root, idea_id=idea_id, status="killed", owner=owner, note=reason, no_sync=no_sync)


def run_lab_path_note(
    root: Path,
    *,
    idea_id: str,
    title: str,
    summaries: list[str] | None = None,
    deferred: str = "",
    session: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner = row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner, session)
    lines = [f"### {_timestamp()} - {title}"]
    for summary in summaries or []:
        lines.append(f"- {summary}")
    if deferred:
        lines.append(f"- Deferred/Parked rationale: {deferred}")
    _append_under_section(root / session_path, "Exploration Path Notes", "\n".join(lines))
    sync_code = _sync(root, message=f"path-note {idea_id}", files=[session_path], no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Path note saved: {session_path}")
    return 0


def run_lab_decide(
    root: Path,
    *,
    idea_id: str,
    decision_id: str = "",
    owner: str = "",
    session: str = "",
    decision_level: str = "L2",
    situation: str = "",
    chosen_option: str = "",
    rationale: str = "",
    constraints: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner_value = owner or row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner_value, session)
    decision_id = decision_id or _next_sequence_id(root, "decision")
    block = "\n".join(
        [
            f"### Decision: {decision_id}",
            "",
            f"- Decision ID: {decision_id}",
            f"- Decision level: {decision_level}",
            f"- Related Idea ID: {idea_id}",
            f"- Date: {_today()}",
            f"- Owner: {owner_value}",
            f"- Session Link: `{session_path}`",
            "- ADR Link (required for L3): ",
            f"- Situation summary: {situation}",
            f"- Constraints: {constraints}",
            f"- Chosen option: {chosen_option}",
            f"- Rationale: {rationale}",
        ]
    )
    _append_under_section(root / session_path, "Decisions", block)
    sync_code = _sync(root, message=f"decide {idea_id}", files=[session_path], no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Decision recorded: {decision_id}")
    return 0


def run_lab_risk(
    root: Path,
    *,
    idea_id: str,
    risk_id: str = "",
    owner: str = "",
    session: str = "",
    statement: str = "",
    mitigation: str = "",
    contingency: str = "",
    probability: str = "medium",
    impact: str = "medium",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner_value = owner or row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner_value, session)
    risk_id = risk_id or _next_sequence_id(root, "risk")
    block = "\n".join(
        [
            f"### Risk: {risk_id}",
            "",
            f"- Risk ID: {risk_id}",
            f"- Related Idea ID: {idea_id}",
            f"- Date: {_today()}",
            f"- Owner: {owner_value}",
            f"- Session Link: `{session_path}`",
            f"- Risk statement: {statement}",
            f"- Probability: {probability}",
            f"- Impact: {impact}",
            f"- Preventive mitigation: {mitigation}",
            f"- Contingency plan: {contingency}",
        ]
    )
    _append_under_section(root / session_path, "Risks", block)
    sync_code = _sync(root, message=f"risk {idea_id}", files=[session_path], no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Risk recorded: {risk_id}")
    return 0


def run_lab_review(
    root: Path,
    *,
    idea_id: str,
    result: str,
    owner: str = "",
    session: str = "",
    summary: str = "",
    outcome: str = "revise",
    next_action: str = "",
    no_sync: bool = False,
) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_title = row.get("title") or _title_from_idea_id(idea_id)
    owner_value = owner or row.get("owner") or _default_owner(root)
    session_path = _ensure_session_file(root, idea_id, idea_title, owner_value, session)
    block = "\n".join(
        [
            f"### Review Gate - {_today()}",
            "",
            f"- Date: {_today()}",
            f"- Owner: {owner_value}",
            f"- Idea ID: {idea_id}",
            f"- Session: `{session_path}`",
            f"- Result: {result}",
            f"- Summary rationale: {summary}",
            f"- Outcome: {outcome}",
            f"- Next action: {next_action}",
        ]
    )
    _append_under_section(root / session_path, "Review Gates", block)
    fields = _build_idea_fields(root, idea_id, owner=owner_value, status=row.get("status") or "active")
    fields["latest_review_outcome"] = result
    block_text = _render_idea_block(fields)
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, fields["status"], block_text)
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status=fields["status"],
        owner=owner_value,
        sessions=_collect_session_links(root, idea_id, row) or [session_path],
        summary_export=row.get("summary_export", ""),
        notes=row.get("notes", "_none_"),
    )
    changed = [BUCKET_FILES[fields["status"]], "IDEA_CATALOG.md", session_path]
    sync_code = _sync(root, message=f"review {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Review recorded for: {idea_id}")
    return 0


def run_lab_export(root: Path, *, idea_id: str, no_sync: bool = False) -> int:
    row = _extract_catalog_row(root, idea_id)
    idea_lookup = _find_idea_block(root, idea_id)
    if idea_lookup is None:
        raise SystemExit(f"Idea '{idea_id}' not found in idea buckets.")
    idea_block = idea_lookup[1]
    session_files = _collect_session_links(root, idea_id, row)
    hydration_files = [root / rel for rel in files_containing(root, "ideas", idea_id) + session_files if path_exists(root, rel)]
    date_stamp = _today()
    export_path = f"exports/{date_stamp}_PROJECT_SUMMARY_{idea_id}.md"
    state = {
        "ideaId": idea_id,
        "projectName": _extract_label_from_text(idea_block, "Title") or row.get("title") or _title_from_idea_id(idea_id),
        "owner": _extract_label_from_text(idea_block, "Owner") or row.get("owner") or _default_owner(root),
        "finalizedAt": date_stamp,
        "purpose": first_value_for_label(hydration_files, "Problem statement")
        or first_value_for_label(hydration_files, "Value hypothesis")
        or "See related idea and session records.",
        "projectType": existing_state_value(root, "projectType")
        or infer_project_type(
            _extract_label_from_text(idea_block, "Title") or _title_from_idea_id(idea_id),
            first_value_for_label(hydration_files, "Problem statement"),
        )
        or "Unspecified",
        "techStack": {
            "language": existing_state_value(root, "techStack.language") or "Not captured yet",
            "runtime": existing_state_value(root, "techStack.runtime") or "Not captured yet",
            "framework": existing_state_value(root, "techStack.framework") or "None",
            "packageTool": existing_state_value(root, "techStack.packageTool") or "None",
        },
        "commands": {
            "build": existing_state_value(root, "commands.build") or "Not captured yet",
            "run": existing_state_value(root, "commands.run") or "Not captured yet",
            "test": existing_state_value(root, "commands.test") or "Not captured yet",
        },
        "product": {
            "problemStatement": _extract_label_from_text(idea_block, "Problem statement"),
            "targetUsers": _extract_label_from_text(idea_block, "Affected users/personas"),
            "whyNow": _extract_label_from_text(idea_block, "Why now"),
            "expectedValue": _extract_label_from_text(idea_block, "Value hypothesis"),
            "solutionSummary": _extract_label_from_text(idea_block, "Value hypothesis"),
            "mvpScope": _extract_label_from_text(idea_block, "MVP scope"),
            "outOfScope": _extract_label_from_text(idea_block, "Out of scope"),
            "assumptions": _extract_label_from_text(idea_block, "Assumptions"),
            "nonGoals": _extract_label_from_text(idea_block, "Non-goals"),
        },
        "governance": {
            "keyDecisions": _extract_label_from_text(idea_block, "Related decisions"),
            "topRisks": _extract_label_from_text(idea_block, "Top risks (link to risk entries)"),
            "mitigationPlans": first_value_for_label(hydration_files, "Preventive mitigation"),
            "contingencies": first_value_for_label(hydration_files, "Contingency plan"),
            "remainingAcceptedRisks": "See related sessions",
            "latestReviewOutcome": _extract_label_from_text(idea_block, "Latest review outcome"),
            "latestReviewSession": session_files[-1] if session_files else "",
        },
        "artifacts": {
            "ideaFiles": files_containing(root, "ideas", idea_id),
            "sessionFiles": session_files,
            "noteReferences": row.get("notes", "_none_"),
            "summaryExport": export_path,
            "finalizationSession": existing_state_value(root, "artifacts.finalizationSession"),
            "adrReferences": _default_adr_references(root),
        },
        "constraints": _extract_label_from_text(idea_block, "Constraints") or "None recorded",
        "persistence": existing_state_value(root, "persistence") or "None",
        "authentication": existing_state_value(root, "authentication") or "None",
        "determinism": existing_state_value(root, "determinism") or "Normal",
        "packaging": existing_state_value(root, "packaging") or "None",
    }
    (root / "exports").mkdir(parents=True, exist_ok=True)
    _write_summary_export(root, export_path, state)
    fields = _build_idea_fields(root, idea_id, summary_export=export_path, status=row.get("status") or "active")
    _remove_idea_from_buckets(root, idea_id)
    _append_idea_to_bucket(root, fields["status"], _render_idea_block(fields))
    _upsert_catalog_row(
        root,
        idea_id=idea_id,
        title=fields["title"],
        status=fields["status"],
        owner=fields["owner"],
        sessions=session_files,
        summary_export=export_path,
        notes=row.get("notes", "_none_"),
    )
    changed = ["exports/" + Path(export_path).name, BUCKET_FILES[fields["status"]], "IDEA_CATALOG.md"]
    sync_code = _sync(root, message=f"export {idea_id}", files=changed, no_sync=no_sync)
    if sync_code != 0:
        raise SystemExit(sync_code)
    print(f"Summary snapshot created: {export_path}")
    return 0


def run_lab_audit(root: Path) -> int:
    return run_validate_governance(root)


def run_lab_finalize(root: Path, *, idea_id: str = "", write_export: bool = False) -> int:
    return run_finalize_project(root, idea_id, write_export=write_export)


def run_lab_commit_command(root: Path, *, message: str = "brainstorm: milestone update") -> int:
    return run_lab_commit(root, message=message)


def run_lab_push_command(root: Path) -> int:
    return run_lab_push(root)
