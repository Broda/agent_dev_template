from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from template_cli.io_helpers import write_text


COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
)


def run_project_harness_new(
    root: Path,
    target: str,
    *,
    origin: str = "",
    no_git: bool = False,
) -> int:
    target_path = Path(target).expanduser()
    if not target_path.is_absolute():
        target_path = (Path.cwd() / target_path).resolve()
    else:
        target_path = target_path.resolve()

    root = root.resolve()
    if target_path == root or root in target_path.parents:
        print("Refusing to create a harness inside the template repository.")
        return 1
    if target_path.exists():
        print(f"Target already exists: {target_path}")
        return 1

    shutil.copytree(root, target_path, ignore=COPY_IGNORE)
    _write_brainstorming_mode(target_path)

    if origin and no_git:
        print("--origin cannot be used with --no-git.")
        return 1

    if not no_git:
        init_result = _run(["git", "init", "-b", "main"], target_path)
        if init_result != 0:
            return init_result
        add_result = _run(["git", "add", "-A"], target_path)
        if add_result != 0:
            return add_result
        commit_result = _run(["git", "commit", "-m", "Initialize project harness"], target_path)
        if commit_result != 0:
            return commit_result
    if origin:
        origin_result = _run(["git", "remote", "add", "origin", origin], target_path)
        if origin_result != 0:
            return origin_result

    validation_result = _run(["./scripts/validate-governance"], target_path)
    if validation_result != 0:
        return validation_result

    print(f"Created project harness: {target_path}")
    if origin:
        print(f"Configured origin: {origin}")
    elif no_git:
        print("Git was not initialized because --no-git was supplied.")
    else:
        print("Initialized independent Git repository with no remote.")
    return 0


def _write_brainstorming_mode(root: Path) -> None:
    write_text(
        root / "MODE.md",
        "\n".join(
            [
                "# Repository Mode",
                "",
                "Current mode: brainstorming",
                "",
                "Allowed values:",
                "",
                "- brainstorming",
                "- development",
                "",
                "Switch modes with `./scripts/finalize-project`.",
                "",
            ]
        ),
    )


def _run(command: list[str], cwd: Path) -> int:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode
