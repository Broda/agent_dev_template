from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

from template_cli.finalize_helpers import (
    files_containing,
)
from template_cli.io_helpers import (
    path_exists,
    read_mode,
    read_text,
    write_text,
)
from template_cli.sync import run_lab_sync
from template_cli.workflow_catalog import _extract_catalog_row

BUCKET_FILES = {
    "inbox": "ideas/_inbox.md",
    "active": "ideas/_active.md",
    "parked": "ideas/_parked.md",
    "killed": "ideas/_killed.md",
    "finalized": "ideas/_active.md",
}
IDEA_BLOCK_RE = re.compile(r"(?ms)^## Idea:.*?(?=^## Idea:|\Z)")
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
