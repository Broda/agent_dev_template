from __future__ import annotations

import json
from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text
from template_cli.validator_manifest import EXPECTED_HARNESS_VERSION
from template_cli.validator_skills import REPO_SKILL_METADATA, REPO_SKILLS

PLUGIN_NAME = "project-lifecycle-lab"
PLUGIN_README = ".harness/plugins/project-lifecycle-lab/README.md"
PLUGIN_SMOKE_SCRIPT = ".harness/plugins/project-lifecycle-lab/smoke_package.py"
PLUGIN_MANIFEST = ".harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json"
PLUGIN_MARKETPLACE = ".agents/plugins/marketplace.json"
PLUGIN_SKILLS_DIR = ".harness/plugins/project-lifecycle-lab/skills"
PLUGIN_SKILLS = {skill_name: f"{PLUGIN_SKILLS_DIR}/{skill_name}/SKILL.md" for skill_name in REPO_SKILLS}
PLUGIN_SKILL_METADATA = {
    skill_name: f"{PLUGIN_SKILLS_DIR}/{skill_name}/agents/openai.yaml" for skill_name in REPO_SKILLS
}
PLUGIN_SKILL_ARTIFACTS = [
    artifact
    for skill_path, metadata_path in zip(PLUGIN_SKILLS.values(), PLUGIN_SKILL_METADATA.values(), strict=True)
    for artifact in (skill_path, metadata_path)
]
PLUGIN_ARTIFACTS = [PLUGIN_MARKETPLACE, PLUGIN_README, PLUGIN_SMOKE_SCRIPT, PLUGIN_MANIFEST, *PLUGIN_SKILL_ARTIFACTS]
EXPECTED_PLUGIN_AUTHOR_NAME = "Project Harness Template Maintainers"
EXPECTED_PLUGIN_AUTHOR_EMAIL = "maintainers@example.invalid"


def validate_repo_plugins(root: Path, result: ValidationResult) -> None:
    manifest = _read_json(root / PLUGIN_MANIFEST, result, "plugin manifest")
    marketplace = _read_json(root / PLUGIN_MARKETPLACE, result, "plugin marketplace")
    _validate_plugin_file_map(root, result)
    if not manifest or not marketplace:
        return

    if manifest.get("name") != PLUGIN_NAME:
        result.add_failure(f"Plugin manifest name must be {PLUGIN_NAME}: {PLUGIN_MANIFEST}")
    if manifest.get("version") != EXPECTED_HARNESS_VERSION:
        result.add_failure(
            f"Plugin manifest version must match harnessVersion {EXPECTED_HARNESS_VERSION}: {PLUGIN_MANIFEST}"
        )
    if manifest.get("skills") != "./skills/":
        result.add_failure(f"Plugin manifest skills path must be ./skills/: {PLUGIN_MANIFEST}")
    _validate_plugin_public_metadata(manifest, result)
    if not manifest.get("interface", {}).get("displayName"):
        result.add_failure(f"Plugin manifest must include interface.displayName: {PLUGIN_MANIFEST}")
    _validate_plugin_boundary(manifest, result)
    _validate_plugin_readme(root, result)
    _validate_plugin_skill_mirrors(root, result)

    entries = marketplace.get("plugins", [])
    matching_entries = [entry for entry in entries if entry.get("name") == PLUGIN_NAME]
    if len(matching_entries) != 1:
        result.add_failure(f"Plugin marketplace must contain exactly one {PLUGIN_NAME} entry.")
        return

    entry = matching_entries[0]
    if entry.get("version") != EXPECTED_HARNESS_VERSION:
        result.add_failure(
            f"Plugin marketplace version must match harnessVersion {EXPECTED_HARNESS_VERSION}: {PLUGIN_MARKETPLACE}"
        )
    if entry.get("source", {}).get("path") != "./.harness/plugins/project-lifecycle-lab":
        result.add_failure(f"Plugin marketplace path is incorrect for {PLUGIN_NAME}.")
    policy = entry.get("policy", {})
    if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
        result.add_failure(f"Plugin marketplace policy is incorrect for {PLUGIN_NAME}.")
    _validate_plugin_readme_examples(root, manifest, entry, result)


def _validate_plugin_public_metadata(manifest: dict, result: ValidationResult) -> None:
    author = manifest.get("author", {})
    if not isinstance(author, dict):
        result.add_failure(f"Plugin manifest author must be an object: {PLUGIN_MANIFEST}")
        return
    if author.get("name") != EXPECTED_PLUGIN_AUTHOR_NAME:
        result.add_failure(f"Plugin manifest author.name must be {EXPECTED_PLUGIN_AUTHOR_NAME}: {PLUGIN_MANIFEST}")
    if author.get("email") != EXPECTED_PLUGIN_AUTHOR_EMAIL:
        result.add_failure(f"Plugin manifest author.email must be {EXPECTED_PLUGIN_AUTHOR_EMAIL}: {PLUGIN_MANIFEST}")
    if manifest.get("interface", {}).get("developerName") != EXPECTED_PLUGIN_AUTHOR_NAME:
        result.add_failure(
            f"Plugin manifest interface.developerName must be {EXPECTED_PLUGIN_AUTHOR_NAME}: {PLUGIN_MANIFEST}"
        )


def _validate_plugin_boundary(manifest: dict, result: ValidationResult) -> None:
    description = manifest.get("description", "")
    long_description = manifest.get("interface", {}).get("longDescription", "")
    if "agent workflows" not in description or "project harness" not in description:
        result.add_failure(f"Plugin description must frame {PLUGIN_NAME} as agent workflows for the harness.")
    for phrase in ["harness runtime stays in the repo", "Repo-scoped skills", ".agents/skills"]:
        if phrase not in long_description:
            result.add_failure(f"Plugin longDescription must preserve harness/plugin boundary phrase: {phrase}")


def _validate_plugin_readme(root: Path, result: ValidationResult) -> None:
    readme_path = root / PLUGIN_README
    if not readme_path.exists():
        result.add_failure(f"Missing plugin README: {PLUGIN_README}")
        return
    readme = read_text(readme_path)
    required_phrases = [
        "remains the canonical skill source",
        "Copied mirrors remain checked in",
        "./scripts/sync-plugin-skills",
        "./scripts/validate-governance",
        "smoke_package.py",
        "External Use Check",
        "ADR-0003",
        "Repo-scoped skills",
        "Portable plugin skills",
        "must not replace repo-local scripts",
    ]
    for phrase in required_phrases:
        if phrase not in readme:
            result.add_failure(f"Plugin README must document packaging boundary phrase: {phrase}")


def _validate_plugin_readme_examples(
    root: Path,
    manifest: dict,
    marketplace_entry: dict,
    result: ValidationResult,
) -> None:
    readme_path = root / PLUGIN_README
    if not readme_path.exists():
        return
    readme = read_text(readme_path)
    display_name = manifest.get("interface", {}).get("displayName", "")
    if display_name and f"# {display_name} Plugin" not in readme:
        result.add_failure(f"Plugin README title must match manifest displayName: {display_name}")
    skills_path = manifest.get("skills", "")
    if skills_path and f"`{skills_path}`" not in readme:
        result.add_failure(f"Plugin README must document manifest skills path: {skills_path}")
    marketplace_path = marketplace_entry.get("source", {}).get("path", "")
    if marketplace_path and f"`{marketplace_path}`" not in readme:
        result.add_failure(f"Plugin README must document marketplace source path: {marketplace_path}")
    for skill_name in sorted(PLUGIN_SKILLS):
        if f"- `{skill_name}`" not in readme:
            result.add_failure(f"Plugin README external-use skill list is missing: {skill_name}")


def _validate_plugin_file_map(root: Path, result: ValidationResult) -> None:
    file_map_path = root / ".harness/brainstorming/FILE_MAP.md"
    if not file_map_path.exists():
        return
    file_map_text = read_text(file_map_path)
    for artifact in PLUGIN_ARTIFACTS:
        if f"`{artifact}`" not in file_map_text:
            result.add_failure(f"FILE_MAP.md missing registry row for plugin artifact: {artifact}")


def _validate_plugin_skill_mirrors(root: Path, result: ValidationResult) -> None:
    for skill_name, repo_skill_path in REPO_SKILLS.items():
        _validate_mirrored_file(root, repo_skill_path, PLUGIN_SKILLS[skill_name], result)
        _validate_mirrored_file(root, REPO_SKILL_METADATA[skill_name], PLUGIN_SKILL_METADATA[skill_name], result)


def _validate_mirrored_file(root: Path, source: str, mirror: str, result: ValidationResult) -> None:
    source_path = root / source
    mirror_path = root / mirror
    if not mirror_path.exists():
        result.add_failure(f"Missing plugin skill mirror: {mirror}")
        return
    if not source_path.exists():
        return
    if read_text(source_path) != read_text(mirror_path):
        result.add_failure(f"Plugin skill mirror drifted from canonical repo skill: {mirror}")


def _read_json(path: Path, result: ValidationResult, label: str) -> dict:
    if not path.exists():
        result.add_failure(f"Missing repo {label}: {path.as_posix()}")
        return {}
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        result.add_failure(f"Invalid JSON in repo {label}: {path.as_posix()} ({exc})")
        return {}
