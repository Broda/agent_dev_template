from __future__ import annotations

from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_mode, read_text
from template_cli.render_ci import DEVELOPMENT_CI_TIMEOUT_MINUTES

PR_CONCURRENCY_GROUP = "  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}"
PR_ONLY_CANCELLATION = "  cancel-in-progress: ${{ github.event_name == 'pull_request' }}"


def validate_ci_efficiency_contract(root: Path, result: ValidationResult) -> None:
    mode = read_mode(root)
    if mode == "brainstorming":
        _validate_brainstorming_workflows(root, result)
    elif mode == "development":
        _validate_development_workflow(root, result)


def _validate_brainstorming_workflows(root: Path, result: ValidationResult) -> None:
    contracts = [
        (".github/workflows/ci.yml", "test-and-validate", 30, "measured Ubuntu timeout"),
        (".github/workflows/ci.yml", "windows-powershell-launchers", 60, "conservative Windows timeout"),
        (".github/workflows/governance-audit.yml", "audit", 10, "measured governance timeout"),
        (
            ".github/workflows/release-readiness.yml",
            "public-template-smoke",
            45,
            "measured release-readiness timeout",
        ),
    ]
    concurrency_checked: set[str] = set()
    for relative_path, job_name, timeout_minutes, timeout_label in contracts:
        path = root / relative_path
        if not path.exists():
            continue
        workflow_text = read_text(path)
        if relative_path not in concurrency_checked:
            _validate_concurrency(result, relative_path, workflow_text)
            concurrency_checked.add(relative_path)
        _validate_job_timeout(
            result,
            relative_path,
            workflow_text,
            job_name,
            timeout_minutes,
            timeout_label,
        )
        if relative_path == ".github/workflows/ci.yml" and job_name == "test-and-validate":
            _validate_drift_upload(result, relative_path, workflow_text, job_name, "generated artifact")


def _validate_development_workflow(root: Path, result: ValidationResult) -> None:
    relative_path = ".github/workflows/ci.yml"
    path = root / relative_path
    if not path.exists():
        return
    workflow_text = read_text(path)
    _validate_concurrency(result, relative_path, workflow_text)
    job_blocks = _job_blocks(workflow_text)
    if not job_blocks:
        _add_failure(result, relative_path, "conservative generated-job timeout")
    for job_name, job_block in job_blocks.items():
        _validate_job_block_timeout(
            result,
            relative_path,
            job_block,
            DEVELOPMENT_CI_TIMEOUT_MINUTES,
            f"conservative generated-job timeout ({job_name})",
        )
    _validate_drift_upload(result, relative_path, workflow_text, "test-and-validate", "generated intent-doc")


def _validate_concurrency(result: ValidationResult, relative_path: str, workflow_text: str) -> None:
    concurrency_block = _mapping_block(workflow_text, "concurrency", 0)
    requirements = {
        "PR-scoped concurrency group": PR_CONCURRENCY_GROUP,
        "PR-only cancellation": PR_ONLY_CANCELLATION,
    }
    for label, required_line in requirements.items():
        if required_line not in concurrency_block.splitlines():
            _add_failure(result, relative_path, label)


def _validate_job_timeout(
    result: ValidationResult,
    relative_path: str,
    workflow_text: str,
    job_name: str,
    timeout_minutes: int,
    label: str,
) -> None:
    jobs_block = _mapping_block(workflow_text, "jobs", 0)
    job_block = _mapping_block(jobs_block, job_name, 2)
    _validate_job_block_timeout(result, relative_path, job_block, timeout_minutes, label)


def _validate_job_block_timeout(
    result: ValidationResult,
    relative_path: str,
    job_block: str,
    timeout_minutes: int,
    label: str,
) -> None:
    required_line = f"    timeout-minutes: {timeout_minutes}"
    if required_line not in job_block.splitlines():
        _add_failure(result, relative_path, label)


def _validate_drift_upload(
    result: ValidationResult,
    relative_path: str,
    workflow_text: str,
    job_name: str,
    artifact_name: str,
) -> None:
    jobs_block = _mapping_block(workflow_text, "jobs", 0)
    job_block = _mapping_block(jobs_block, job_name, 2)
    step_block = _sequence_item_block(job_block, f"Upload {artifact_name} drift", 6)
    requirements = {
        "failure-only drift upload": "        if: failure()",
        "three-day diagnostic retention": "          retention-days: 3",
    }
    for label, required_line in requirements.items():
        if required_line not in step_block.splitlines():
            _add_failure(result, relative_path, label)


def _mapping_block(text: str, key: str, indent: int) -> str:
    lines = text.splitlines()
    target = f"{' ' * indent}{key}:"
    for index, line in enumerate(lines):
        if line != target:
            continue
        end = _block_end(lines, index + 1, indent)
        return "\n".join(lines[index:end])
    return ""


def _job_blocks(workflow_text: str) -> dict[str, str]:
    jobs_block = _mapping_block(workflow_text, "jobs", 0)
    job_names = [
        line.strip()[:-1]
        for line in jobs_block.splitlines()
        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":")
    ]
    return {job_name: _mapping_block(jobs_block, job_name, 2) for job_name in job_names}


def _sequence_item_block(text: str, name: str, indent: int) -> str:
    lines = text.splitlines()
    target = f"{' ' * indent}- name: {name}"
    for index, line in enumerate(lines):
        if line != target:
            continue
        end = _block_end(lines, index + 1, indent)
        return "\n".join(lines[index:end])
    return ""


def _block_end(lines: list[str], start: int, parent_indent: int) -> int:
    for index in range(start, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= parent_indent:
            return index
    return len(lines)


def _add_failure(result: ValidationResult, relative_path: str, label: str) -> None:
    result.add_failure(f"Workflow {relative_path} is missing CI-efficiency contract: {label}")
