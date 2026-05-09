from __future__ import annotations

import json
import os
from pathlib import Path

from template_cli.io_helpers import read_text

STATE_FILE = "state/project-init.json"
WIKI_ENV_DEFAULT = "PROJECT_HARNESS_WIKI_DIR"


def default_wiki_config(root: Path) -> dict:
    return {
        "enabled": False,
        "pathEnv": WIKI_ENV_DEFAULT,
        "defaultCheckout": f"../{root.name}.wiki",
        "remote": "",
    }


def wiki_config(root: Path) -> dict:
    config = default_wiki_config(root)
    state_path = root / STATE_FILE
    if not state_path.exists():
        return config
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return config
    documentation = state.get("documentation", {})
    if not isinstance(documentation, dict):
        return config
    wiki = documentation.get("wiki", {})
    if not isinstance(wiki, dict):
        return config
    config.update({key: wiki.get(key, config[key]) for key in config})
    config["enabled"] = bool(config.get("enabled") is True)
    config["pathEnv"] = str(config.get("pathEnv") or WIKI_ENV_DEFAULT)
    config["defaultCheckout"] = str(config.get("defaultCheckout") or f"../{root.name}.wiki")
    config["remote"] = str(config.get("remote") or "")
    return config


def wiki_dir(root: Path, config: dict) -> Path:
    env_name = str(config.get("pathEnv") or WIKI_ENV_DEFAULT)
    override = os.environ.get(env_name, "").strip()
    raw_path = override or str(config.get("defaultCheckout") or f"../{root.name}.wiki")
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (root / path).resolve()
