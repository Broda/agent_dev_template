from __future__ import annotations

import json
from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text


PLUGIN_NAME = "project-lifecycle-lab"
PLUGIN_MANIFEST = "plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
PLUGIN_MARKETPLACE = ".agents/plugins/marketplace.json"


def validate_repo_plugins(root: Path, result: ValidationResult) -> None:
    manifest = _read_json(root / PLUGIN_MANIFEST, result, "plugin manifest")
    marketplace = _read_json(root / PLUGIN_MARKETPLACE, result, "plugin marketplace")
    _validate_plugin_file_map(root, result)
    if not manifest or not marketplace:
        return

    if manifest.get("name") != PLUGIN_NAME:
        result.add_failure(f"Plugin manifest name must be {PLUGIN_NAME}: {PLUGIN_MANIFEST}")
    if not manifest.get("interface", {}).get("displayName"):
        result.add_failure(f"Plugin manifest must include interface.displayName: {PLUGIN_MANIFEST}")

    entries = marketplace.get("plugins", [])
    matching_entries = [entry for entry in entries if entry.get("name") == PLUGIN_NAME]
    if len(matching_entries) != 1:
        result.add_failure(f"Plugin marketplace must contain exactly one {PLUGIN_NAME} entry.")
        return

    entry = matching_entries[0]
    if entry.get("source", {}).get("path") != "./plugins/project-lifecycle-lab":
        result.add_failure(f"Plugin marketplace path is incorrect for {PLUGIN_NAME}.")
    policy = entry.get("policy", {})
    if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
        result.add_failure(f"Plugin marketplace policy is incorrect for {PLUGIN_NAME}.")


def _validate_plugin_file_map(root: Path, result: ValidationResult) -> None:
    file_map_path = root / "brainstorming/FILE_MAP.md"
    if not file_map_path.exists():
        return
    file_map_text = read_text(file_map_path)
    for artifact in [PLUGIN_MARKETPLACE, PLUGIN_MANIFEST]:
        if f"`{artifact}`" not in file_map_text:
            result.add_failure(f"FILE_MAP.md missing registry row for plugin artifact: {artifact}")


def _read_json(path: Path, result: ValidationResult, label: str) -> dict:
    if not path.exists():
        result.add_failure(f"Missing repo {label}: {path.as_posix()}")
        return {}
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        result.add_failure(f"Invalid JSON in repo {label}: {path.as_posix()} ({exc})")
        return {}
