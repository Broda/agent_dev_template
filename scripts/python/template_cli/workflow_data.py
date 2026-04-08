from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

from template_cli.finalize import (
    existing_state_value,
    files_containing,
    first_value_for_label,
)
from template_cli.sync import run_lab_sync
from template_cli.validators import (
    IDEA_ROW_RE,
    clean_backticks,
    parse_markdown_table_rows,
    path_exists,
    read_mode,
    read_text,
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
FINALIZE_REQUIRED_FIELDS = [
    ("problem statement", ["product.problemStatement", "purpose"], "Problem statement"),
    ("MVP scope", ["product.mvpScope"], "MVP scope"),
    ("build command", ["commands.build"], ""),
    ("run command", ["commands.run"], ""),
    ("test command", ["commands.test"], ""),
]
FINALIZE_ADVISORY_FIELDS = [
    ("latest review outcome", ["governance.latestReviewOutcome"], "Latest review outcome"),
    ("top risks", ["governance.topRisks"], "Top risks (link to risk entries)"),
]


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


def _is_placeholderish_value(value: str) -> bool:
    lowered = _trim(value).lower()
    return lowered in {"", "none", "_none_", "_none yet_", "_n/a_", "not captured yet", "none recorded"}


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

        body = list(lines[section_start + 1: section_end])
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
