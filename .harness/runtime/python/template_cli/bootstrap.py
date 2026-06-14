from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from template_cli.external_idea import ExternalIdeaImportResult, ExternalIdeaPayload, load_external_idea_payload
from template_cli.io_helpers import read_mode, write_text
from template_cli.workflow_idea_commands import import_external_idea
from template_cli.validator_manifest import stamp_harness_manifest

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
    stamp_harness_manifest(target_path, root)

    if origin and no_git:
        print("--origin cannot be used with --no-git.")
        return 1

    if not no_git:
        init_result = _run(["git", "init", "-b", "main"], target_path)
        if init_result != 0:
            return init_result
        identity_result = _ensure_initial_commit_identity(target_path)
        if identity_result != 0:
            return identity_result
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

    validation_result = _run(_template_cli_command("validate-governance"), target_path)
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



def _run_maybe_quiet(command: list[str], cwd: Path, *, quiet: bool) -> int:
    if not quiet:
        return _run(command, cwd)
    with contextlib.redirect_stdout(io.StringIO()):
        return _run(command, cwd)


def _call_maybe_quiet(func, *args, quiet: bool, **kwargs) -> int:
    if not quiet:
        return func(*args, **kwargs)
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


def run_project_harness_new_from_idea(
    root: Path,
    target: str,
    *,
    idea_id: str = "",
    title: str = "",
    summary: str = "",
    source: str = "external",
    source_id: str = "",
    payload_file: str = "",
    activate: bool = False,
    commit: bool = False,
    no_git: bool = False,
    json_output: bool = False,
) -> int:
    if payload_file:
        payload = load_external_idea_payload(Path(payload_file).expanduser())
    else:
        payload = ExternalIdeaPayload(
            idea_id=idea_id,
            title=title,
            summary=summary,
            source=source,
            source_id=source_id,
        )

    create_result = _call_maybe_quiet(run_project_harness_new, root, target, no_git=True, quiet=json_output)
    if create_result != 0:
        return create_result
    target_path = Path(target).expanduser()
    if not target_path.is_absolute():
        target_path = (Path.cwd() / target_path).resolve()
    else:
        target_path = target_path.resolve()

    import_result = import_external_idea(
        target_path,
        payload,
        activate=activate or True,
        create_session=True,
        path_note="Imported from an external idea source.",
        no_sync=True,
    )

    commit_sha = ""
    if not no_git:
        init_result = _run_maybe_quiet(["git", "init", "-b", "main"], target_path, quiet=json_output)
        if init_result != 0:
            return init_result
        identity_result = _ensure_initial_commit_identity(target_path)
        if identity_result != 0:
            return identity_result
        add_result = _run_maybe_quiet(["git", "add", "-A"], target_path, quiet=json_output)
        if add_result != 0:
            return add_result
        message = "Initialize project harness"
        if commit:
            message = f"brainstorm: import external idea {import_result.idea_id}"
        commit_result = _run_maybe_quiet(["git", "commit", "-m", message], target_path, quiet=json_output)
        if commit_result != 0:
            return commit_result
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=target_path, text=True, capture_output=True, check=False)
        if rev.returncode == 0:
            commit_sha = rev.stdout.strip()

    validation_result = _run_maybe_quiet(_template_cli_command("validate-governance"), target_path, quiet=json_output)
    if validation_result != 0:
        return validation_result

    result = ExternalIdeaImportResult(
        ok=True,
        idea_id=import_result.idea_id,
        title=import_result.title,
        status=import_result.status,
        source=import_result.source,
        source_id=import_result.source_id,
        session_path=import_result.session_path,
        changed_files=import_result.changed_files,
        readiness=import_result.readiness,
        target_created=True,
        target_path=str(target_path),
        commit=commit_sha,
    )
    if json_output:
        print(json.dumps(result.to_json_dict(), sort_keys=True))
    else:
        print(f"Created project harness from external idea: {target_path}")
        print(f"Idea: {result.idea_id}")
        if result.session_path:
            print(f"Session: {result.session_path}")
    return 0

def run_project_harness_validate(root: Path) -> int:
    commands = [("validate-governance", "./scripts/validate-governance")]
    if read_mode(root) == "development":
        commands.append(("validate-development", "./scripts/validate-development"))

    for cli_command, display_command in commands:
        print(f"Running: {display_command}")
        result = _run(_template_cli_command(cli_command), root)
        print(f"Exit code: {result}")
        if result != 0:
            return result
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


def _template_cli_command(command: str) -> list[str]:
    return [sys.executable, str(Path(".harness") / "runtime" / "python" / "cli.py"), command]


def _ensure_initial_commit_identity(root: Path) -> int:
    if not _git_config_value(root, "user.name"):
        name_result = _run(["git", "config", "user.name", "Project Harness"], root)
        if name_result != 0:
            return name_result
    if not _git_config_value(root, "user.email"):
        email_result = _run(["git", "config", "user.email", "project-harness@example.invalid"], root)
        if email_result != 0:
            return email_result
    return 0


def _git_config_value(root: Path, key: str) -> str:
    result = subprocess.run(
        ["git", "config", "--get", key],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
