from __future__ import annotations

from datetime import date
from pathlib import Path

from template_cli.io_helpers import write_text


def write_handoff_session(
    root: Path,
    idea_id: str,
    idea_files: list[str],
    session_paths: list[str],
    filled: list[str],
    missing: list[str],
    contract_sections: list[tuple[str, list[str]]],
) -> str:
    session_path = f"sessions/{date.today().isoformat()}_HANDOFF_SESSION_{idea_id}.md"
    lines = summary_lines(idea_id, idea_files, session_paths, filled, missing, contract_sections)
    write_text(root / session_path, "\n".join(["# Handoff Session", "", *lines]) + "\n")
    return session_path


def print_summary(
    idea_id: str,
    idea_files: list[str],
    session_paths: list[str],
    filled: list[str],
    missing: list[str],
    contract_sections: list[tuple[str, list[str]]],
    *,
    check: bool,
) -> None:
    print("Handoff check" if check else "Handoff compile")
    for line in summary_lines(idea_id, idea_files, session_paths, filled, missing, contract_sections):
        print(line)


def summary_lines(
    idea_id: str,
    idea_files: list[str],
    session_paths: list[str],
    filled: list[str],
    missing: list[str],
    contract_sections: list[tuple[str, list[str]]],
) -> list[str]:
    return [
        f"- Idea ID: {idea_id}",
        "- Source idea files: " + (", ".join(idea_files) if idea_files else "none"),
        "- Source session files: " + (", ".join(session_paths) if session_paths else "none"),
        "- Filled fields: " + (", ".join(filled) if filled else "none"),
        "- Missing fields: " + (", ".join(missing) if missing else "none"),
        "- Implementation contract sections: "
        + (", ".join(title for title, _ in contract_sections) if contract_sections else "none"),
    ]
