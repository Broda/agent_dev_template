from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text


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
