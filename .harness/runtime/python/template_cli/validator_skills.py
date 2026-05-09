from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text

REPO_SKILLS = {
    "brainstorming-lab": ".agents/skills/brainstorming-lab/SKILL.md",
    "project-finalizer": ".agents/skills/project-finalizer/SKILL.md",
    "development-governance": ".agents/skills/development-governance/SKILL.md",
    "template-maintenance": ".agents/skills/template-maintenance/SKILL.md",
}
REPO_SKILL_METADATA = {
    skill_name: skill_path.replace("/SKILL.md", "/agents/openai.yaml") for skill_name, skill_path in REPO_SKILLS.items()
}


def validate_repo_skills(root: Path, result: ValidationResult) -> None:
    agents_text = read_text(root / "AGENTS.md") if (root / "AGENTS.md").exists() else ""
    file_map_text = (
        read_text(root / ".harness/brainstorming/FILE_MAP.md")
        if (root / ".harness/brainstorming/FILE_MAP.md").exists()
        else ""
    )

    for skill_name, relative_path in REPO_SKILLS.items():
        skill_path = root / relative_path
        if not skill_path.exists():
            result.add_failure(f"Missing required repo skill: {relative_path}")
            continue

        text = read_text(skill_path)
        frontmatter = _skill_frontmatter(text)
        if frontmatter.get("name") != skill_name:
            result.add_failure(f"Repo skill has incorrect name in {relative_path}: {frontmatter.get('name', '')}")
        if not frontmatter.get("description"):
            result.add_failure(f"Repo skill is missing description in {relative_path}")
        if f"${skill_name}" not in agents_text:
            result.add_failure(f"AGENTS.md does not reference repo skill: ${skill_name}")
        if f"`{relative_path}`" not in file_map_text:
            result.add_failure(f"FILE_MAP.md missing registry row for repo skill: {relative_path}")

        metadata_path = REPO_SKILL_METADATA[skill_name]
        metadata_file = root / metadata_path
        if not metadata_file.exists():
            result.add_failure(f"Missing repo skill UI metadata: {metadata_path}")
            continue
        metadata_text = read_text(metadata_file)
        if "default_prompt:" not in metadata_text or f"${skill_name}" not in metadata_text:
            result.add_failure(
                f"Repo skill UI metadata must include default_prompt with ${skill_name}: {metadata_path}"
            )
        if f"`{metadata_path}`" not in file_map_text:
            result.add_failure(f"FILE_MAP.md missing registry row for repo skill metadata: {metadata_path}")


def _skill_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    _, frontmatter, _body = text.split("---", 2)
    values: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values
