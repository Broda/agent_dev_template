from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import write_text
from template_cli.wiki_config import STATE_FILE, default_wiki_config, wiki_config
from template_cli.wiki_git import changed_repo_files, ensure_wiki_checkout, git_output, is_wiki_relevant
from template_cli.wiki_pages import render_pages


def run_lab_wiki_render(root: Path) -> int:
    config = wiki_config(root)
    if not config["enabled"]:
        print("Wiki tooling is disabled for this project.")
        print(f"Enable it with {STATE_FILE}: documentation.wiki.enabled = true")
        return 0

    wiki_dir = ensure_wiki_checkout(root, config)
    if wiki_dir is None:
        return 1

    pages = render_pages(root)
    for name, content in pages.items():
        write_text(wiki_dir / name, content)
    print(f"Rendered {len(pages)} wiki pages into {wiki_dir}")
    print("Review, commit, and push the wiki checkout when ready.")
    return 0


def run_lab_wiki_check(root: Path) -> int:
    config = wiki_config(root)
    if not config["enabled"]:
        print("Wiki tooling is disabled for this project.")
        return 0

    wiki_dir = ensure_wiki_checkout(root, config)
    if wiki_dir is None:
        return 1

    changed = changed_repo_files(root)
    relevant = [path for path in changed if is_wiki_relevant(path)]
    if not relevant:
        print("wiki check ok: no user-facing repo changes detected")
        return 0

    wiki_status = git_output(["git", "status", "--porcelain"], cwd=wiki_dir)
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


__all__ = [
    "default_wiki_config",
    "run_lab_wiki_check",
    "run_lab_wiki_render",
]
