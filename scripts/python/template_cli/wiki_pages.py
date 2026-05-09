from __future__ import annotations

import json
from pathlib import Path

from template_cli.io_helpers import read_text
from template_cli.wiki_config import STATE_FILE

WIKI_PAGES = {
    "Home.md": "Home",
    "Getting-Started.md": "Getting Started",
    "Architecture.md": "Architecture",
    "Roadmap.md": "Roadmap",
    "Decisions.md": "Decisions",
    "Verification.md": "Verification",
    "Release-Notes.md": "Release Notes",
}


def render_pages(root: Path) -> dict[str, str]:
    state = _state(root)
    project_name = str(state.get("projectName") or root.name)
    purpose = str(state.get("purpose") or "Project documentation and operating guidance.")
    return {
        "Home.md": _home_page(project_name, purpose),
        "Getting-Started.md": _doc_page(root, "Getting Started", "README.md"),
        "Architecture.md": _doc_page(root, "Architecture", "docs/ARCHITECTURE.md"),
        "Roadmap.md": _doc_page(root, "Roadmap", "docs/ROADMAP.md"),
        "Decisions.md": _decisions_page(root),
        "Verification.md": _doc_page(root, "Verification", "docs/RUNTIME_VERIFICATION_REPORT.md"),
        "Release-Notes.md": _doc_page(root, "Release Notes", "CHANGELOG.md"),
        "_Sidebar.md": _sidebar_page(),
    }


def _state(root: Path) -> dict:
    try:
        data = json.loads(read_text(root / STATE_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _home_page(project_name: str, purpose: str) -> str:
    return f"""# {project_name}

{purpose}

## Start Here

- [[Getting Started]]
- [[Architecture]]
- [[Roadmap]]
- [[Decisions]]
- [[Verification]]
- [[Release Notes]]

Canonical project governance remains in the repository. This wiki is the friendly reading layer for humans who want the current operating picture quickly.
"""


def _doc_page(root: Path, title: str, relative_path: str) -> str:
    source = root / relative_path
    if not source.exists():
        return f"# {title}\n\nSource document is not present yet: `{relative_path}`\n"
    content = read_text(source).strip()
    body = _without_first_heading(content)
    return f"""# {title}

Source: [{relative_path}]({relative_path})

{body}
"""


def _decisions_page(root: Path) -> str:
    adr_dir = root / "docs" / "adr"
    rows = []
    for path in sorted(adr_dir.glob("ADR-*.md")):
        title = _first_heading(path) or path.stem
        rows.append(f"- [[{title}|{path.stem}]] - source: `{path.relative_to(root).as_posix()}`")
    if not rows:
        rows.append("- No ADRs recorded yet.")
    return "# Decisions\n\n" + "\n".join(rows) + "\n"


def _sidebar_page() -> str:
    return "\n".join(f"- [[{title}|{name.removesuffix('.md')}]]" for name, title in WIKI_PAGES.items()) + "\n"


def _without_first_heading(content: str) -> str:
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return content


def _first_heading(path: Path) -> str:
    for line in read_text(path).splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return ""
