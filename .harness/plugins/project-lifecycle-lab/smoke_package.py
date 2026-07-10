#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_SKILLS = [
    "brainstorming-lab",
    "development-governance",
    "project-finalizer",
    "template-maintenance",
]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    plugin_root = Path(args[0]).resolve() if args else Path(__file__).resolve().parent
    failures: list[str] = []

    manifest = _read_manifest(plugin_root, failures)
    if manifest:
        if manifest.get("name") != "project-lifecycle-lab":
            failures.append("plugin manifest name must be project-lifecycle-lab")
        if manifest.get("skills") != "./skills/":
            failures.append("plugin manifest skills path must be ./skills/")
        interface = manifest.get("interface")
        if not isinstance(interface, dict) or not interface.get("displayName"):
            failures.append("plugin manifest interface.displayName is required")

    for skill_name in EXPECTED_SKILLS:
        _check_skill(plugin_root, skill_name, failures)
    if (plugin_root / "scripts").exists():
        failures.append("plugin package must not contain repo-local runtime scripts")

    if failures:
        print("Plugin package smoke check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Plugin package smoke check passed.")
    print(f"Checked skills: {', '.join(EXPECTED_SKILLS)}")
    return 0


def _read_manifest(plugin_root: Path, failures: list[str]) -> dict:
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    if not manifest_path.exists():
        failures.append("missing .codex-plugin/plugin.json")
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid plugin manifest JSON: {exc}")
        return {}
    if not isinstance(manifest, dict):
        failures.append("plugin manifest root must be an object")
        return {}
    return manifest


def _check_skill(plugin_root: Path, skill_name: str, failures: list[str]) -> None:
    skill_path = plugin_root / "skills" / skill_name / "SKILL.md"
    metadata_path = plugin_root / "skills" / skill_name / "agents/openai.yaml"
    if not skill_path.exists():
        failures.append(f"missing skill file: skills/{skill_name}/SKILL.md")
        return
    skill_text = skill_path.read_text(encoding="utf-8")
    if f"name: {skill_name}" not in skill_text:
        failures.append(f"skill frontmatter name mismatch: {skill_name}")
    if not metadata_path.exists():
        failures.append(f"missing skill UI metadata: skills/{skill_name}/agents/openai.yaml")
        return
    metadata_text = metadata_path.read_text(encoding="utf-8")
    for required in ["display_name:", "short_description:", "default_prompt:"]:
        if required not in metadata_text:
            failures.append(f"skill UI metadata for {skill_name} missing {required}")
    if f"${skill_name}" not in metadata_text:
        failures.append(f"skill UI metadata for {skill_name} must reference ${skill_name}")
    if skill_name == "template-maintenance" and "posixExecutablePaths" not in skill_text:
        failures.append("template-maintenance skill must preserve the POSIX executable-mode contract")


if __name__ == "__main__":
    raise SystemExit(main())
