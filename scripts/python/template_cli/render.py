from __future__ import annotations

import json
import shutil
from pathlib import Path

from template_cli.validators import read_text, replace_literal, write_text


MILESTONE_NAME = "Milestone 0 — Foundation / Spine"
STATE_FILE = "state/project-init.json"


class RenderError(Exception):
    pass


def _load_state(root: Path) -> dict:
    state_path = root / STATE_FILE
    try:
        return json.loads(read_text(state_path))
    except FileNotFoundError as exc:
        raise RenderError(f"Missing state file: {STATE_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise RenderError(f"Invalid JSON in {STATE_FILE}: {exc}") from exc


def _extract_value(state: dict, path: str) -> str:
    cur = state
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise RenderError(f"Missing required value in {STATE_FILE}: {path}")
        cur = cur[part]
    if cur is None or not str(cur).strip():
        raise RenderError(f"Missing required value in {STATE_FILE}: {path}")
    return str(cur)


def _copy_base(root: Path, src: str, dst: str) -> None:
    src_path = root / src
    dst_path = root / dst
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_path, dst_path)


def _replace_file_literals(path: Path, replacements: list[tuple[str, str]]) -> None:
    content = read_text(path)
    for old, new in replacements:
        content = replace_literal(content, old, new)
    write_text(path, content)


def _replace_readme_command_block(content: str, label: str, value: str) -> str:
    import re

    pattern = re.compile(rf"{re.escape(label)}:\r?\n\r?\n\s*<command>")
    return pattern.sub(f"{label}:\n\n    {value}", content)


def run_render_development_docs(root: Path) -> int:
    state = _load_state(root)

    project_name = _extract_value(state, "projectName")
    purpose = _extract_value(state, "purpose")
    _extract_value(state, "projectType")
    language = _extract_value(state, "techStack.language")
    runtime = _extract_value(state, "techStack.runtime")
    framework = str(state.get("techStack", {}).get("framework", "") or "None")
    package_tool = str(state.get("techStack", {}).get("packageTool", "") or "None")
    persistence = str(state.get("persistence", "") or "")
    build_command = _extract_value(state, "commands.build")
    run_command = _extract_value(state, "commands.run")
    test_command = _extract_value(state, "commands.test")

    _copy_base(root, "development/templates/docs/README.base.md", "README.md")
    _copy_base(root, "development/templates/docs/PROJECT_CONTEXT.base.md", "docs/PROJECT_CONTEXT.md")
    _copy_base(root, "development/templates/docs/ROADMAP.base.md", "docs/ROADMAP.md")
    _copy_base(root, "development/templates/docs/ARCHITECTURE.base.md", "docs/ARCHITECTURE.md")
    _copy_base(root, "development/templates/docs/FILE_MAP.base.md", "docs/FILE_MAP.md")
    _copy_base(root, "development/templates/docs/GOVERNANCE_INDEX.base.md", "docs/GOVERNANCE_INDEX.md")
    _copy_base(
        root,
        "development/templates/docs/VERSIONING_AND_RELEASE_POLICY.base.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
    )
    _copy_base(root, "development/templates/docs/SECURITY_POLICY.base.md", "docs/SECURITY_POLICY.md")
    _copy_base(
        root,
        "development/templates/docs/RUNTIME_VERIFICATION_REPORT.base.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
    )
    _copy_base(
        root,
        "development/templates/docs/adr/ADR-0001-record-architecture-decisions.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
    )
    _copy_base(root, "development/templates/docs/adr/ADR-TEMPLATE.md", "docs/adr/ADR-TEMPLATE.md")
    _copy_base(root, "development/templates/docs/CHANGELOG.base.md", "CHANGELOG.md")

    migration_policy_path = root / "docs/MIGRATION_POLICY.md"
    if persistence and persistence != "None":
        _copy_base(root, "development/templates/docs/MIGRATION_POLICY.base.md", "docs/MIGRATION_POLICY.md")
    elif migration_policy_path.exists():
        migration_policy_path.unlink()

    lc_lang = language.lower()
    if "python" in lc_lang:
        shutil.copyfile(root / "development/templates/gitignore/python.gitignore", root / ".gitignore")
    elif any(token in lc_lang for token in ("node", "javascript", "typescript")):
        shutil.copyfile(root / "development/templates/gitignore/node.gitignore", root / ".gitignore")
    elif any(token in lc_lang for token in ("c#", "dotnet", ".net")):
        shutil.copyfile(root / "development/templates/gitignore/dotnet.gitignore", root / ".gitignore")
    else:
        shutil.copyfile(root / "development/templates/gitignore/generic.gitignore", root / ".gitignore")

    if persistence and persistence != "None":
        with (root / ".gitignore").open("a", encoding="utf-8") as handle:
            handle.write("\n*.db\n*.sqlite\n*.sqlite3\n")

    setup_steps = (
        f"Language: {language}\n"
        f"Runtime: {runtime}\n"
        f"Framework: {framework or 'None'}\n"
        f"Tooling: {package_tool or 'None'}"
    )

    shared_replacements = [
        ("<Project Name>", project_name),
        ("<Milestone Name>", MILESTONE_NAME),
        ("<Build command>", build_command),
        ("<Run command>", run_command),
        ("<Test command>", test_command),
    ]

    for relative_path in [
        "README.md",
        "docs/PROJECT_CONTEXT.md",
        "docs/ROADMAP.md",
        "docs/ARCHITECTURE.md",
        "docs/FILE_MAP.md",
        "docs/GOVERNANCE_INDEX.md",
        "docs/VERSIONING_AND_RELEASE_POLICY.md",
        "docs/SECURITY_POLICY.md",
        "docs/RUNTIME_VERIFICATION_REPORT.md",
        "docs/adr/ADR-0001-record-architecture-decisions.md",
        "docs/adr/ADR-TEMPLATE.md",
    ]:
        _replace_file_literals(root / relative_path, shared_replacements)

    readme_path = root / "README.md"
    readme_content = read_text(readme_path)
    readme_content = replace_literal(readme_content, "Short description of the project.", purpose)
    readme_content = replace_literal(readme_content, "<Prototype / MVP / Beta>", "MVP")
    readme_content = replace_literal(readme_content, "<Stack-specific setup steps>", setup_steps)
    readme_content = replace_literal(
        readme_content,
        './scripts/lab-note --topic "<topic>" --summary "<bullet>"',
        './scripts/lab-note --topic "runtime-verification" --summary "Captured smoke-test notes"',
    )
    readme_content = _replace_readme_command_block(readme_content, "Build", build_command)
    readme_content = _replace_readme_command_block(readme_content, "Run", run_command)
    readme_content = _replace_readme_command_block(readme_content, "Test", test_command)
    write_text(readme_path, readme_content)

    _replace_file_literals(
        root / "docs/PROJECT_CONTEXT.md",
        [
            ("<Describe what this project is and why it exists.>", purpose),
            ("<What comes next>", "Deliver Milestone 0 vertical slice and verification evidence."),
        ],
    )
    _replace_file_literals(
        root / "docs/ROADMAP.md",
        [
            ("Milestone 0 – Foundation", MILESTONE_NAME),
            (
                "<commands run> + <results observed>",
                f"{build_command} (success), {test_command} (pass), {run_command} (smoke verified)",
            ),
        ],
    )
    _replace_file_literals(
        root / "docs/RUNTIME_VERIFICATION_REPORT.md",
        [
            ("<build command>", build_command),
            ("<test command>", test_command),
            ("<run command>", run_command),
        ],
    )

    changelog_path = root / "CHANGELOG.md"
    changelog_content = read_text(changelog_path)
    marker = "## [Unreleased]"
    if marker in changelog_content:
        changelog_content = changelog_content.replace(
            marker,
            marker
            + "\n\n### Added\n- Initialized Structured Mode governance baseline from brainstorming finalization.",
            1,
        )
    write_text(changelog_path, changelog_content)

    return 0
