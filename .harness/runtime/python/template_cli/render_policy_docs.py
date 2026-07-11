from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import read_text, write_text
from template_cli.render_capabilities import ProjectProfile


def apply_capability_policy_docs(root: Path, profile: ProjectProfile) -> None:
    if not profile.has_api:
        _replace(
            root / "docs/SECURITY_POLICY.md",
            [
                ("- API endpoints\n- CLI commands", "- CLI commands"),
                ("- API endpoints", "- Boundary commands and imports"),
                ("- Avoid exposing debug or internal endpoints.", "- Avoid exposing debug or internal commands."),
            ],
        )
        _replace(
            root / "docs/VERSIONING_AND_RELEASE_POLICY.md",
            [
                ("- API/IPC/DTO change\n", ""),
                ("- New endpoint\n", ""),
                ("- API endpoints\n- IPC channels\n- DTO structures\n", ""),
                ("- Preserve DTO shapes.\n", ""),
                ("- Must NOT change DTO shapes.\n", ""),
            ],
        )
        _replace(
            root / "docs/RUNTIME_VERIFICATION_REPORT.md",
            [
                ("- [ ] API endpoints unchanged (unless expected)\n", ""),
                ("- [ ] DTO structures unchanged (unless versioned)\n", ""),
            ],
        )
    if not profile.has_authentication:
        _replace(
            root / "docs/SECURITY_POLICY.md",
            [
                (
                    "# 3. Authentication & Authorization (If Applicable)\n\nIf authentication exists:",
                    "# 3. Authentication & Authorization\n\nAuthentication is not part of the current finalized scope. If it is added later:",
                ),
                ("- Not remove authentication checks.", "- Not add authentication scope without an ADR."),
                ("- Not bypass authorization checks.", "- Not add authorization scope without an ADR."),
            ],
        )
    if not profile.uses_javascript:
        _replace(
            root / "docs/RUNTIME_VERIFICATION_REPORT.md",
            [("- [ ] No unhandled promise exceptions", "- [ ] No uncaught runtime exceptions")],
        )


def _replace(path: Path, replacements: list[tuple[str, str]]) -> None:
    if not path.exists():
        return
    content = read_text(path)
    for old, new in replacements:
        content = content.replace(old, new)
    write_text(path, content)
