from __future__ import annotations

from pathlib import Path

from template_cli.handoff_contract import CONTRACT_KEY_BY_TITLE
from template_cli.render_contract import collect_implementation_contract


def fill_implementation_contract(
    state: dict,
    hydration_files: list[Path],
    filled: list[str],
) -> list[tuple[str, list[str]]]:
    sections = collect_implementation_contract(state, hydration_files)
    if not sections:
        return []
    implementation = state.setdefault("implementation", {})
    for title, details in sections:
        key = CONTRACT_KEY_BY_TITLE.get(title)
        if not key or implementation.get(key):
            continue
        implementation[key] = details
        filled.append(f"implementation.{key}")
    return sections
