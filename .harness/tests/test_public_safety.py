from __future__ import annotations

import re
import unittest
from pathlib import Path

from workflow_test_helpers import REPO_ROOT

PUBLIC_DOC_PATHS = [
    "README.md",
    "AGENTS.md",
    "docs",
    ".hermes/plans",
    ".harness/commands",
    ".harness/brainstorming",
    ".agents/skills",
    ".harness/plugins/project-lifecycle-lab/skills",
]

ALLOWLIST = {
    "/home/<name>/",
}

PRIVATE_PATTERNS = [
    re.compile(r"/home/(?!<name>)[A-Za-z0-9_.-]+"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?<![0-9])[0-9]{17,}(?![0-9])"),
]


def _iter_public_text_files() -> list[Path]:
    files: list[Path] = []
    for relative in PUBLIC_DOC_PATHS:
        path = REPO_ROOT / relative
        if path.is_file():
            files.append(path)
            continue
        if not path.exists():
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".txt"}:
                files.append(child)
    return files


class PublicSafetyTests(unittest.TestCase):
    def test_public_docs_do_not_include_private_paths_or_credentials(self) -> None:
        violations: list[str] = []
        for path in _iter_public_text_files():
            text = path.read_text(encoding="utf-8")
            for pattern in PRIVATE_PATTERNS:
                for match in pattern.finditer(text):
                    value = match.group(0)
                    if value in ALLOWLIST:
                        continue
                    relative = path.relative_to(REPO_ROOT)
                    violations.append(f"{relative}: {value}")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
