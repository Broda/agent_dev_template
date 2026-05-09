from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import ValidationResult


PYTHON_CODE_ROOTS = ["scripts/python", "tests"]
MAX_CODE_LINES = 350


def validate_python_file_sizes(root: Path, result: ValidationResult) -> None:
    for relative_root in PYTHON_CODE_ROOTS:
        code_root = root / relative_root
        if not code_root.exists():
            continue
        for path in sorted(code_root.rglob("*.py")):
            relative_path = path.relative_to(root).as_posix()
            if "__pycache__" in path.parts:
                continue
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_CODE_LINES:
                result.add_failure(
                    f"Python code file exceeds {MAX_CODE_LINES} lines: {relative_path} ({line_count})"
                )
