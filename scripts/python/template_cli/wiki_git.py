from __future__ import annotations

import subprocess
from pathlib import Path

from template_cli.wiki_config import STATE_FILE, wiki_dir


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


def ensure_wiki_checkout(root: Path, config: dict) -> Path | None:
    checkout = wiki_dir(root, config)
    if (checkout / ".git").is_dir():
        return checkout

    remote = str(config.get("remote") or "").strip() or infer_wiki_remote(root)
    if not remote:
        print("Cannot clone wiki checkout because no git origin remote is configured.")
        print(f"Set documentation.wiki.remote in {STATE_FILE}, or add an origin remote.")
        return None

    print(f"Wiki checkout not found at {checkout}")
    print(f"Cloning wiki remote: {remote}")
    result = subprocess.run(
        ["git", "clone", remote, str(checkout)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return checkout

    print("Could not clone the GitHub Wiki repository.")
    if result.stderr.strip():
        print(result.stderr.strip())
    print()
    print("Make sure the repository wiki is enabled and has its first page created on GitHub.")
    print("Then rerun ./scripts/lab wiki-render or ./scripts/lab wiki-check.")
    return None


def infer_wiki_remote(root: Path) -> str:
    origin = git_output(["git", "remote", "get-url", "origin"], cwd=root).strip()
    if not origin:
        return ""
    if origin.endswith(".git"):
        return origin.removesuffix(".git") + ".wiki.git"
    return origin.rstrip("/") + ".wiki.git"


def changed_repo_files(root: Path) -> list[str]:
    outputs = [
        git_output(["git", "diff", "--name-only"], cwd=root),
        git_output(["git", "diff", "--cached", "--name-only"], cwd=root),
        git_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root),
    ]
    return sorted({line.strip() for output in outputs for line in output.splitlines() if line.strip()})


def is_wiki_relevant(path: str) -> bool:
    if path in WIKI_RELEVANT_FILES:
        return True
    if path.startswith(WIKI_RELEVANT_PREFIXES):
        return True
    return path.endswith((".py", ".js", ".ts", ".tsx", ".rs", ".go", ".java", ".cs"))


def git_output(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout
