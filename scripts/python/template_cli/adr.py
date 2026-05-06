from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from template_cli.io_helpers import write_text


ADR_RE = re.compile(r"^ADR-(\d{4})-.+\.md$")
CHECKBOX_FIELDS = {
    "version_impact": [
        "Require MAJOR version bump",
        "Require MINOR version bump",
        "Require PATCH version bump",
        "Not affect versioning",
    ],
    "governance_impact": [
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "PROJECT_CONTEXT.md",
        "MIGRATION_POLICY.md",
        "SECURITY_POLICY.md",
        "VERSIONING_AND_RELEASE_POLICY.md",
        "CHANGELOG.md",
    ],
}


def run_lab_adr(
    root: Path,
    *,
    title: str,
    context: list[str],
    decision: str,
    consequence: list[str],
    alternative: list[str],
    status: str = "Accepted",
    deciders: str = "",
    supersedes: str = "",
    adr_date: str = "",
) -> int:
    clean_title = _single_line(title)
    clean_decision = _single_line(decision)
    if not clean_title:
        print("--title is required.")
        return 1
    if not clean_decision:
        print("--decision is required.")
        return 1

    docs_dir = root / "docs" / "adr"
    docs_dir.mkdir(parents=True, exist_ok=True)

    number = _next_adr_number(docs_dir)
    slug = _slugify(clean_title)
    path = docs_dir / f"ADR-{number:04d}-{slug}.md"
    if path.exists():
        print(f"ADR already exists: {path.relative_to(root)}")
        return 1

    content = _render_adr(
        number=number,
        title=clean_title,
        status=_single_line(status) or "Accepted",
        adr_date=_single_line(adr_date) or date.today().isoformat(),
        deciders=_single_line(deciders),
        supersedes=_single_line(supersedes),
        context=[_single_line(item) for item in context if _single_line(item)],
        decision=clean_decision,
        consequence=[_single_line(item) for item in consequence if _single_line(item)],
        alternative=[_single_line(item) for item in alternative if _single_line(item)],
    )
    write_text(path, content)

    print(f"Created {path.relative_to(root)}")
    return 0


def _next_adr_number(docs_dir: Path) -> int:
    numbers: list[int] = []
    for path in docs_dir.glob("ADR-*.md"):
        match = ADR_RE.match(path.name)
        if match:
            numbers.append(int(match.group(1)))
    return (max(numbers) + 1) if numbers else 1


def _single_line(value: str) -> str:
    return " ".join(value.strip().split())


def _slugify(value: str) -> str:
    normalized = value.casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "decision"


def _bullet_lines(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def _checkbox_lines(field: str) -> str:
    return "\n".join(f"- [ ] {item}" for item in CHECKBOX_FIELDS[field])


def _render_adr(
    *,
    number: int,
    title: str,
    status: str,
    adr_date: str,
    deciders: str,
    supersedes: str,
    context: list[str],
    decision: str,
    consequence: list[str],
    alternative: list[str],
) -> str:
    return f"""# ADR-{number:04d}: {title}

- Status: {status}
- Date: {adr_date}
- Deciders: {deciders or "TBD"}
- Supersedes: {supersedes}
- Superseded by:

---

## Context

{_bullet_lines(context, "TBD")}

---

## Decision

- {decision}

---

## Consequences

{_bullet_lines(consequence, "TBD")}

---

## Alternatives Considered

{_bullet_lines(alternative, "TBD")}

---

## Version Impact

{_checkbox_lines("version_impact")}

If persistence is affected:

- [ ] Migration required
- [ ] Migration not required

---

## Governance Impact

{_checkbox_lines("governance_impact")}

---

## Notes

TBD
"""
