from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text

PYPROJECT_PATH = "pyproject.toml"
REQUIRED_SECTIONS = [
    "[tool.ruff]",
    "[tool.ruff.lint]",
    "[tool.ruff.lint.isort]",
    "[tool.mypy]",
]
REQUIRED_SNIPPETS = [
    "line-length = 120",
    'target-version = "py312"',
    'known-first-party = ["template_cli"]',
    'select = ["E", "F", "I", "UP", "B"]',
    'python_version = "3.12"',
]


def validate_python_tool_config(root: Path, result: ValidationResult) -> None:
    path = root / PYPROJECT_PATH
    if not path.exists():
        result.add_failure(f"Missing Python tool config: {PYPROJECT_PATH}")
        return

    text = read_text(path)
    for section in REQUIRED_SECTIONS:
        if section not in text:
            result.add_failure(f"pyproject.toml missing required section: {section}")
    for snippet in REQUIRED_SNIPPETS:
        if snippet not in text:
            result.add_failure(f"pyproject.toml missing required snippet: {snippet}")
