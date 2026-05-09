from __future__ import annotations

import json
from pathlib import Path

from template_cli.finalize_helpers import STATE_FILE, trim, unique_values
from template_cli.handoff_contract import EMPTY_HANDOFF_VALUES, STATE_DEFAULTS
from template_cli.io_helpers import read_text


def load_state(root: Path) -> dict:
    try:
        data = json.loads(read_text(root / STATE_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def with_defaults(state: dict) -> dict:
    merged = json.loads(json.dumps(STATE_DEFAULTS))
    _merge_dicts(merged, state)
    return merged


def fill(state: dict, dotted_path: str, value: object, filled: list[str]) -> None:
    if is_empty_handoff_value(value):
        return
    if value_at(state, dotted_path):
        return
    set_value(state, dotted_path, value)
    filled.append(dotted_path)


def fill_list(state: dict, dotted_path: str, values: list[str], filled: list[str]) -> None:
    existing = raw_value_at(state, dotted_path)
    merged = unique_values((existing if isinstance(existing, list) else []) + values)
    if merged != existing:
        set_value(state, dotted_path, merged)
        filled.append(dotted_path)


def value_at(state: dict, dotted_path: str) -> str:
    value = raw_value_at(state, dotted_path)
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if str(item).strip())
    if isinstance(value, dict):
        return ""
    text = "" if value is None else str(value).strip()
    return "" if is_empty_handoff_value(text) else text


def raw_value_at(state: dict, dotted_path: str) -> object:
    cur: object = state
    for part in dotted_path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def set_value(state: dict, dotted_path: str, value: object) -> None:
    cur = state
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def is_empty_handoff_value(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    return trim(value) in EMPTY_HANDOFF_VALUES


def _merge_dicts(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value
