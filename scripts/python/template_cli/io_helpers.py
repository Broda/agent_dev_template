from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

NOTE_ID_RE = re.compile(r"^note-\d{4}$")
NOTE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IDEA_ROW_RE = re.compile(r"^\|\s*idea-[a-z0-9-]+")
ADR_LINK_RE = re.compile(r"docs/adr/ADR-[0-9]{4}-[a-z0-9-]+\.md")
PLACEHOLDER_RE = re.compile(r"<[^>]+>")
FORBIDDEN_DEVELOPMENT_TEMPLATE_TERMS = [
    "gameplay",
    "player",
    "battle",
    "economy",
    "market",
    "playable loop",
    "starter progression",
    "onboarding",
]
DEVELOPMENT_SEMANTIC_DOCS = [
    "README.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
]


def path_exists(root: Path, relative_path: str) -> bool:
    return bool(relative_path) and (root / relative_path).exists()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def replace_literal(content: str, old: str, new: str) -> str:
    return content.replace(old, new)


def read_mode(root: Path) -> str:
    mode_path = root / "MODE.md"
    if not mode_path.exists():
        return ""
    for line in read_text(mode_path).splitlines():
        if line.startswith("Current mode:"):
            return line.split(":", 1)[1].strip()
    return ""


def parse_markdown_table_rows(path: Path, pattern: re.Pattern[str]) -> list[list[str]]:
    if not path.exists():
        return []

    rows: list[list[str]] = []
    for line in read_text(path).splitlines():
        if pattern.search(line):
            rows.append([cell.strip() for cell in line.split("|")[1:-1]])
    return rows


def clean_backticks(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def is_noneish(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"_none_", "_none yet_", "_n/a_", "n/a"}


def find_markdown_files(root: Path) -> list[Path]:
    excluded_prefixes = [
        ".git",
        "external",
        "codex_brainstorming_template",
        "codex_template",
        "development/templates",
        "development/bootstrap",
    ]
    results: list[Path] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if any(rel == prefix or rel.startswith(prefix + "/") for prefix in excluded_prefixes):
            continue
        results.append(path)
    return results


@dataclass
class ValidationResult:
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_failure(self, message: str) -> None:
        self.failures.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def print_brainstorming_summary(result: ValidationResult) -> int:
    print("Lean validation summary")
    print(f"- Failures: {len(result.failures)}")
    print(f"- Warnings: {len(result.warnings)}")

    if result.warnings:
        print()
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.failures:
        print()
        print("Failures:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    print()
    print("PASS: lean integrity checks completed with no blocking failures.")
    return 0


def print_development_summary(result: ValidationResult) -> int:
    print("Development validation summary")
    print(f"- Failures: {len(result.failures)}")

    if result.failures:
        print()
        print("Failures:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    print()
    print("PASS: development integrity checks completed with no blocking failures.")
    return 0
