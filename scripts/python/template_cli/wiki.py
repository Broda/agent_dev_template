from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from template_cli.io_helpers import read_text, write_text


STATE_FILE = "state/project-init.json"
WIKI_ENV_DEFAULT = "PROJECT_HARNESS_WIKI_DIR"
WIKI_PAGES = {
    "Home.md": "Home",
    "Getting-Started.md": "Getting Started",
    "Architecture.md": "Architecture",
    "Roadmap.md": "Roadmap",
    "Decisions.md": "Decisions",
    "Verification.md": "Verification",
    "Release-Notes.md": "Release Notes",
}
WIKI_RELEVANT_PREFIXES = (
    "docs/",
    "harness_commands/",
    "development/templates/",
    "scripts/python/template_cli/",
    "src/",
    "app/",
    "lib/",
    "crates/",
)
WIKI_RELEVANT_FILES = {
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "state/project-init.json",
}


def run_lab_wiki_render(root: Path) -> int:
    config = _wiki_config(root)
    if not config["enabled"]:
        print("Wiki tooling is disabled for this project.")
        print(f"Enable it with {STATE_FILE}: documentation.wiki.enabled = true")
        return 0

    wiki_dir = _ensure_wiki_checkout(root, config)
    if wiki_dir is None:
        return 1

    pages = _render_pages(root)
    for name, content in pages.items():
        write_text(wiki_dir / name, content)
    print(f"Rendered {len(pages)} wiki pages into {wiki_dir}")
    print("Review, commit, and push the wiki checkout when ready.")
    return 0


def run_lab_wiki_check(root: Path) -> int:
    config = _wiki_config(root)
    if not config["enabled"]:
        print("Wiki tooling is disabled for this project.")
        return 0

    wiki_dir = _ensure_wiki_checkout(root, config)
    if wiki_dir is None:
        return 1

    changed = _changed_repo_files(root)
    relevant = [path for path in changed if _is_wiki_relevant(path)]
    if not relevant:
        print("wiki check ok: no user-facing repo changes detected")
        return 0

    wiki_status = _git_output(["git", "status", "--porcelain"], cwd=wiki_dir)
    if wiki_status.strip():
        print("wiki check ok: user-facing repo changes are paired with wiki checkout changes")
        print(wiki_status.strip())
        return 0

    print("wiki check failed: user-facing repo changes detected, but the wiki checkout is clean")
    print()
    print("repo changes:")
    for path in relevant:
        print(f"  {path}")
    print()
    print(f"wiki checkout: {wiki_dir}")
    print("Run ./scripts/lab wiki-render, then review and commit the wiki checkout.")
    return 1


def default_wiki_config(root: Path) -> dict:
    return {
        "enabled": False,
        "pathEnv": WIKI_ENV_DEFAULT,
        "defaultCheckout": f"../{root.name}.wiki",
        "remote": "",
    }


def _wiki_config(root: Path) -> dict:
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


def _ensure_wiki_checkout(root: Path, config: dict) -> Path | None:
    wiki_dir = _wiki_dir(root, config)
    if (wiki_dir / ".git").is_dir():
        return wiki_dir

    remote = str(config.get("remote") or "").strip() or _infer_wiki_remote(root)
    if not remote:
        print("Cannot clone wiki checkout because no git origin remote is configured.")
        print(f"Set documentation.wiki.remote in {STATE_FILE}, or add an origin remote.")
        return None

    print(f"Wiki checkout not found at {wiki_dir}")
    print(f"Cloning wiki remote: {remote}")
    result = subprocess.run(
        ["git", "clone", remote, str(wiki_dir)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return wiki_dir

    print("Could not clone the GitHub Wiki repository.")
    if result.stderr.strip():
        print(result.stderr.strip())
    print()
    print("Make sure the repository wiki is enabled and has its first page created on GitHub.")
    print("Then rerun ./scripts/lab wiki-render or ./scripts/lab wiki-check.")
    return None


def _wiki_dir(root: Path, config: dict) -> Path:
    env_name = str(config.get("pathEnv") or WIKI_ENV_DEFAULT)
    override = os.environ.get(env_name, "").strip()
    raw_path = override or str(config.get("defaultCheckout") or f"../{root.name}.wiki")
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _infer_wiki_remote(root: Path) -> str:
    origin = _git_output(["git", "remote", "get-url", "origin"], cwd=root).strip()
    if not origin:
        return ""
    if origin.endswith(".git"):
        return origin.removesuffix(".git") + ".wiki.git"
    return origin.rstrip("/") + ".wiki.git"


def _changed_repo_files(root: Path) -> list[str]:
    outputs = [
        _git_output(["git", "diff", "--name-only"], cwd=root),
        _git_output(["git", "diff", "--cached", "--name-only"], cwd=root),
        _git_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root),
    ]
    paths = sorted({line.strip() for output in outputs for line in output.splitlines() if line.strip()})
    return paths


def _is_wiki_relevant(path: str) -> bool:
    if path in WIKI_RELEVANT_FILES:
        return True
    if path.startswith(WIKI_RELEVANT_PREFIXES):
        return True
    return path.endswith((".py", ".js", ".ts", ".tsx", ".rs", ".go", ".java", ".cs"))


def _git_output(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout


def _render_pages(root: Path) -> dict[str, str]:
    state = _state(root)
    project_name = str(state.get("projectName") or root.name)
    purpose = str(state.get("purpose") or "Project documentation and operating guidance.")
    pages = {
        "Home.md": _home_page(project_name, purpose),
        "Getting-Started.md": _doc_page(root, "Getting Started", "README.md"),
        "Architecture.md": _doc_page(root, "Architecture", "docs/ARCHITECTURE.md"),
        "Roadmap.md": _doc_page(root, "Roadmap", "docs/ROADMAP.md"),
        "Decisions.md": _decisions_page(root),
        "Verification.md": _doc_page(root, "Verification", "docs/RUNTIME_VERIFICATION_REPORT.md"),
        "Release-Notes.md": _doc_page(root, "Release Notes", "CHANGELOG.md"),
        "_Sidebar.md": _sidebar_page(),
    }
    return pages


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
