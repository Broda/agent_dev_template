from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_mode, read_text
from template_cli.validator_manifest import load_harness_manifest

PYTHON_COMMAND_LAUNCHERS = {
    "finalize-project": "finalize-project",
    "lab-note": "lab-note",
    "lab-sync": "lab-sync",
    "project-harness": "project-harness-new",
    "render-development-docs": "render-development-docs",
    "render-intent-docs": "render-intent-docs",
    "sync-plugin-skills": "sync-plugin-skills",
    "validate-brainstorming": "validate-brainstorming",
    "validate-development": "validate-development",
    "validate-governance": "validate-governance",
}


def validate_python_launchers(root: Path, result: ValidationResult) -> None:
    for script_name, cli_command in PYTHON_COMMAND_LAUNCHERS.items():
        _validate_bare_launcher(root, result, script_name)
        _validate_shell_launcher(root, result, script_name, cli_command)
        _validate_powershell_launcher(root, result, script_name, cli_command)
    _validate_lab_launcher(root, result)
    _validate_project_harness_update_launcher(root, result)
    _validate_shell_launchers_are_portable(root, result)
    _validate_windows_ci_launcher_job(root, result)
    _validate_release_readiness_workflow(root, result)


def _validate_bare_launcher(root: Path, result: ValidationResult, script_name: str) -> None:
    path = root / "scripts" / script_name
    if not path.exists():
        return
    text = read_text(path)
    if f"{script_name}.sh" not in text:
        result.add_failure(f"Launcher scripts/{script_name} must delegate to scripts/{script_name}.sh.")


def _validate_shell_launcher(root: Path, result: ValidationResult, script_name: str, cli_command: str) -> None:
    path = root / "scripts" / f"{script_name}.sh"
    if not path.exists():
        return
    text = read_text(path)
    required_snippets = [
        "set -euo pipefail",
        'python/cli.py"',
        f" {cli_command}",
        "command -v python3",
        "command -v python",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            result.add_failure(f"Shell launcher scripts/{script_name}.sh is missing expected snippet: {snippet}")


def _validate_powershell_launcher(root: Path, result: ValidationResult, script_name: str, cli_command: str) -> None:
    path = root / "scripts" / f"{script_name}.ps1"
    if not path.exists():
        return
    text = read_text(path)
    required_snippets = [
        "Set-StrictMode -Version Latest",
        'py -3 "$scriptDir/python/cli.py"',
        f" {cli_command}",
        'python "$scriptDir/python/cli.py"',
    ]
    for snippet in required_snippets:
        if snippet not in text:
            result.add_failure(f"PowerShell launcher scripts/{script_name}.ps1 is missing expected snippet: {snippet}")


def _validate_lab_launcher(root: Path, result: ValidationResult) -> None:
    shell_path = root / "scripts/lab.sh"
    if shell_path.exists():
        text = read_text(shell_path)
        for snippet in [
            "Usage: ./scripts/lab <command> [args]",
            "Run ./scripts/lab <command> --help",
            'subcommand="${1:-}"',
            '"lab-$subcommand"',
            'python/cli.py"',
        ]:
            if snippet not in text:
                result.add_failure(f"Shell launcher scripts/lab.sh is missing expected snippet: {snippet}")

    powershell_path = root / "scripts/lab.ps1"
    if powershell_path.exists():
        text = read_text(powershell_path)
        for snippet in [
            "Set-StrictMode -Version Latest",
            "Usage: ./scripts/lab <command> [args]",
            "Run ./scripts/lab <command> --help",
            'py -3 "$scriptDir/python/cli.py"',
            '("lab-" + $subcommand)',
        ]:
            if snippet not in text:
                result.add_failure(f"PowerShell launcher scripts/lab.ps1 is missing expected snippet: {snippet}")


def _validate_project_harness_update_launcher(root: Path, result: ValidationResult) -> None:
    for relative_path in ["scripts/project-harness.sh", "scripts/project-harness.ps1"]:
        path = root / relative_path
        if not path.exists():
            continue
        text = read_text(path)
        if "project-harness-update" not in text:
            result.add_failure(f"Launcher {relative_path} is missing project-harness update delegation.")
        _validate_project_harness_help(root, result, relative_path, text)


def _validate_project_harness_help(
    root: Path,
    result: ValidationResult,
    relative_path: str,
    text: str,
) -> None:
    if "Usage: ./scripts/project-harness <command> [args]" not in text:
        result.add_failure(f"Launcher {relative_path} is missing project-harness usage help.")
        return

    for subcommand in _project_harness_manifest_subcommands(root):
        if not re.search(rf"^\s+{re.escape(subcommand)}\b", text, flags=re.MULTILINE):
            result.add_failure(
                f"Launcher {relative_path} help is missing project-harness subcommand from manifest: {subcommand}"
            )

    for backend_command, subcommand in [
        ("project-harness-new", "new"),
        ("project-harness-update", "update"),
    ]:
        for option in _cli_help_options(root, backend_command):
            if option == "--help":
                continue
            if option not in text:
                result.add_failure(
                    f"Launcher {relative_path} help for project-harness {subcommand} "
                    f"is missing CLI parser option: {option}"
                )


def _project_harness_manifest_subcommands(root: Path) -> set[str]:
    try:
        manifest = load_harness_manifest(root)
    except (FileNotFoundError, ValueError):
        return set()
    for wrapper in manifest.get("stableWrappers", []):
        if not isinstance(wrapper, dict) or wrapper.get("path") != "scripts/project-harness":
            continue
        subcommands: set[str] = set()
        backend_command = str(wrapper.get("backendCommand", ""))
        for raw_backend in backend_command.split("|"):
            backend = raw_backend.strip()
            if backend.startswith("project-harness-"):
                subcommands.add(backend.removeprefix("project-harness-"))
        return subcommands
    return set()


def _cli_help_options(root: Path, backend_command: str) -> set[str]:
    cli_path = root / "scripts/python/cli.py"
    if not cli_path.exists():
        return set()
    completed = subprocess.run(
        [sys.executable, str(cli_path), backend_command, "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    return set(re.findall(r"--[a-z][a-z0-9-]*", output))


def _validate_shell_launchers_are_portable(root: Path, result: ValidationResult) -> None:
    forbidden_patterns = {
        r"\breadlink\s+-f\b": "GNU readlink -f",
        r"\brealpath\b": "realpath availability differs across macOS versions",
        r"\bsed\s+-i\b": "sed -i semantics differ on macOS",
        r"\bgrep\s+-P\b": "GNU grep -P",
        r"\bxargs\s+-r\b": "GNU xargs -r",
        r"/proc/": "Linux /proc filesystem",
        r"\bapt(?:-get)?\b": "Ubuntu package manager",
    }
    for path in sorted((root / "scripts").glob("*.sh")):
        text = read_text(path)
        relative_path = path.relative_to(root).as_posix()
        for pattern, label in forbidden_patterns.items():
            if re.search(pattern, text):
                result.add_failure(f"Shell launcher {relative_path} uses non-portable macOS pattern: {label}")


def _validate_windows_ci_launcher_job(root: Path, result: ValidationResult) -> None:
    if read_mode(root) != "brainstorming":
        return
    ci_path = root / ".github/workflows/ci.yml"
    if not ci_path.exists():
        return
    ci_text = read_text(ci_path)
    required_snippets = {
        "Windows runner": "runs-on: windows-latest",
        "PowerShell shell": "shell: pwsh",
        "launcher smoke tests": "python -m unittest tests.test_lab_launcher tests.test_project_harness_bootstrap -v",
        "PowerShell update smoke": "Run PowerShell project-harness update smoke",
        "PowerShell update help": "./scripts/project-harness.ps1 update --help",
        "PowerShell update diagnostics": "Invoke-SmokeCommand",
        "PowerShell update dry run": "./scripts/project-harness.ps1 update --dry-run --source-path $source",
        "PowerShell update apply": "./scripts/project-harness.ps1 update --apply --source-path $source --yes",
        "PowerShell update backup assertion": "Backup directory:",
        "PowerShell generated artifact smoke": "Run PowerShell generated artifact launcher smoke",
        "PowerShell render intent launcher": "./scripts/render-intent-docs.ps1",
        "PowerShell sync plugin launcher": "./scripts/sync-plugin-skills.ps1",
        "PowerShell render development launcher": "./scripts/render-development-docs.ps1",
        "PowerShell sync plugin drift repair": "stale plugin copy",
        "PowerShell generated artifact idempotence": "Assert-UnchangedHashes",
        "PowerShell governance launcher": "./scripts/validate-governance.ps1",
    }
    for label, snippet in required_snippets.items():
        if snippet not in ci_text:
            result.add_failure(f"CI workflow is missing Windows PowerShell launcher coverage: {label}")


def _validate_release_readiness_workflow(root: Path, result: ValidationResult) -> None:
    if read_mode(root) != "brainstorming":
        return
    workflow_path = root / ".github/workflows/release-readiness.yml"
    if not workflow_path.exists():
        result.add_failure("Missing release-readiness workflow: .github/workflows/release-readiness.yml")
        return
    workflow_text = read_text(workflow_path)
    if "\n  pull_request:" in workflow_text or "\n  push:" in workflow_text:
        result.add_failure("Release-readiness workflow must stay manual-only until it proves stable.")
    required_snippets = {
        "manual dispatch": "workflow_dispatch:",
        "governance validation": "./scripts/validate-governance",
        "full unit suite": "python3 -m unittest discover -s tests -v",
        "plugin package smoke": "python3 plugins/project-lifecycle-lab/smoke_package.py plugins/project-lifecycle-lab",
        "fresh copy": './scripts/project-harness new "$tmpdir/harness-smoke" --no-git',
        "fresh copy validation": '"$tmpdir/harness-smoke/scripts/validate-governance"',
        "finalize/render fixture smoke": (
            "python3 -m unittest tests.test_finalization_regression tests.test_development_rendering -v"
        ),
        "update dry run": './scripts/project-harness update --dry-run --source-path "$source/template"',
        "update apply": './scripts/project-harness update --apply --source-path "$source/template" --yes',
        "generated intent docs": "./scripts/render-intent-docs",
        "plugin mirror sync": "./scripts/sync-plugin-skills",
    }
    for label, snippet in required_snippets.items():
        if snippet not in workflow_text:
            result.add_failure(f"Release-readiness workflow is missing checklist coverage: {label}")
