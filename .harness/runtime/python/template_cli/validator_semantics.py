from __future__ import annotations

import re
from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text
from template_cli.render_capabilities import contract_list, contract_milestones, finalized_contract, project_profile

GENERATED_DOCS = [
    "README.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
    "docs/VERSIONING_AND_RELEASE_POLICY.md",
    "docs/SECURITY_POLICY.md",
    "docs/RUNTIME_VERIFICATION_REPORT.md",
    "docs/MIGRATION_POLICY.md",
    "docs/adr/ADR-0001-record-architecture-decisions.md",
]


def validate_semantic_finalization(root: Path, result: ValidationResult, state: dict) -> None:
    profile = project_profile(state)
    documents = _read_documents(root)
    combined = "\n".join(documents.values())
    lower_combined = combined.lower()

    if profile.is_cli:
        _reject_terms(result, lower_combined, ["web ui", "admin ui", "editor-facing"], "CLI project")
    if not profile.has_api:
        _reject_terms(result, lower_combined, ["api endpoints", "dto structures", "api handlers"], "non-API project")
    if not profile.has_authentication:
        _reject_terms(result, lower_combined, ["configure auth", "configure authentication"], "no-auth project")
    if not profile.uses_javascript:
        _reject_terms(result, lower_combined, ["typescript", "npm", "unhandled promise"], "non-JavaScript project")

    if re.search(r"\bCom,\s", combined):
        result.add_failure("Generated docs contain malformed dotted-name concept fragment: Com,")

    deferred = contract_list(state, "deferredScope")
    _validate_unique_deferred_scope(result, deferred)
    _validate_deferred_scope_not_active(result, documents.get("docs/ROADMAP.md", ""), deferred)
    _validate_structured_contract_rendered(result, combined, state)


def _read_documents(root: Path) -> dict[str, str]:
    documents: dict[str, str] = {}
    for relative_path in GENERATED_DOCS:
        path = root / relative_path
        if path.exists():
            documents[relative_path] = read_text(path)
    return documents


def _reject_terms(result: ValidationResult, lower_content: str, terms: list[str], context: str) -> None:
    for term in terms:
        pattern = r"\b" + re.escape(term) + r"\b" if re.fullmatch(r"[a-z0-9]+", term) else re.escape(term)
        if re.search(pattern, lower_content):
            result.add_failure(f"Generated development docs contain unsupported {context} surface: {term}")


def _validate_unique_deferred_scope(result: ValidationResult, deferred: list[str]) -> None:
    seen: set[str] = set()
    for item in deferred:
        key = item.strip().lower()
        if not key:
            continue
        if key in seen:
            result.add_failure(f"finalizedContract.deferredScope contains duplicate exclusion: {item}")
        seen.add(key)


def _validate_deferred_scope_not_active(result: ValidationResult, roadmap: str, deferred: list[str]) -> None:
    checkbox_lines = [line.lower() for line in roadmap.splitlines() if re.match(r"^\s*-\s+\[[ xX]\]", line)]
    for item in deferred:
        key = item.strip().lower()
        if not key:
            continue
        if any(key in line for line in checkbox_lines):
            result.add_failure(f"Deferred scope appears as an active roadmap task: {item}")


def _validate_structured_contract_rendered(result: ValidationResult, combined: str, state: dict) -> None:
    if not finalized_contract(state):
        return
    for label, values in [
        ("invariant", contract_list(state, "invariants")),
        ("ownership boundary", contract_list(state, "ownershipBoundaries")),
        ("deferred scope", contract_list(state, "deferredScope")),
    ]:
        for value in values:
            if value not in combined:
                result.add_failure(f"Generated development docs are missing captured {label}: {value}")
    for milestone in contract_milestones(state):
        if milestone["id"] not in combined or milestone["name"] not in combined:
            result.add_failure(
                f"Generated development docs are missing captured milestone: {milestone['id']} {milestone['name']}"
            )
