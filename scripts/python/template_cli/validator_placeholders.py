from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from template_cli.io_helpers import PLACEHOLDER_RE, read_text


@dataclass
class PlaceholderFinding:
    relative_path: str
    line_number: int
    token: str
    line: str
    source: str


def _code_spans(line: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start: int | None = None
    idx = 0
    while idx < len(line):
        if line[idx] == "`":
            if start is None:
                start = idx
            else:
                spans.append((start, idx + 1))
                start = None
        idx += 1
    return spans


def _inside_span(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _state_scalar_sources(state: object, prefix: str = "state/project-init.json") -> list[tuple[str, str]]:
    if isinstance(state, dict):
        values: list[tuple[str, str]] = []
        for key, value in state.items():
            values.extend(_state_scalar_sources(value, f"{prefix}.{key}"))
        return values
    if isinstance(state, list):
        values = []
        for idx, value in enumerate(state):
            values.extend(_state_scalar_sources(value, f"{prefix}[{idx}]"))
        return values
    if state is None:
        return []
    return [(prefix, str(state))]


def _load_state_sources(root: Path) -> list[tuple[str, str]]:
    state_path = root / "state/project-init.json"
    if not state_path.exists():
        return []
    try:
        return _state_scalar_sources(json.loads(read_text(state_path)))
    except json.JSONDecodeError:
        return []


def _source_for_token(token: str, line: str, sources: list[tuple[str, str]]) -> str:
    line_clean = line.strip()
    for path, value in sources:
        if token in value or value in line_clean:
            return f"{path}: {value}"
    return "generated doc text"


def find_unresolved_placeholders(root: Path, files: list[Path]) -> list[PlaceholderFinding]:
    state_sources = _load_state_sources(root)
    findings: list[PlaceholderFinding] = []
    for path in files:
        if path.name == "ADR-TEMPLATE.md" and path.parent.name == "adr":
            continue
        if not path.exists():
            continue
        relative_path = path.relative_to(root).as_posix()
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if line.startswith("    ") or line.startswith("\t"):
                continue
            spans = _code_spans(line)
            for match in PLACEHOLDER_RE.finditer(line):
                if _inside_span(match.start(), spans):
                    continue
                token = match.group(0)
                findings.append(
                    PlaceholderFinding(
                        relative_path=relative_path,
                        line_number=line_number,
                        token=token,
                        line=line.strip(),
                        source=_source_for_token(token, line, state_sources),
                    )
                )
    return findings
