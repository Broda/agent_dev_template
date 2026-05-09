from __future__ import annotations

import shutil
from pathlib import Path

from template_cli.validator_plugins import PLUGIN_SKILL_METADATA, PLUGIN_SKILLS
from template_cli.validator_skills import REPO_SKILL_METADATA, REPO_SKILLS
from template_cli.validators import run_validate_governance


def run_sync_plugin_skills(root: Path) -> int:
    copied = []
    for skill_name, source in REPO_SKILLS.items():
        mirror = PLUGIN_SKILLS[skill_name]
        _copy_file(root / source, root / mirror)
        copied.append(mirror)

        metadata_source = REPO_SKILL_METADATA[skill_name]
        metadata_mirror = PLUGIN_SKILL_METADATA[skill_name]
        _copy_file(root / metadata_source, root / metadata_mirror)
        copied.append(metadata_mirror)

    print("Synced plugin skill mirrors from canonical repo skills:")
    for relative_path in copied:
        print(f"- {relative_path}")
    print()
    return run_validate_governance(root)


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
