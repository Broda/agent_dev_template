from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from template_cli.io_helpers import ValidationResult
from template_cli.validation_hook_state import ProtectedStateLedger

HOOK_PATH = Path("scripts/project_harness_validation.py")
HOOK_TIMEOUT_SECONDS = 60.0
HOOK_STDOUT_LIMIT = 64 * 1024
HOOK_STDERR_LIMIT = 64 * 1024
HOOK_ACTIVE_ENV = "PROJECT_HARNESS_VALIDATION_HOOK_ACTIVE"
HOOK_SKIP_ENV = "PROJECT_HARNESS_VALIDATION_HOOK_SKIP"
HOOK_COMMANDS = {
    "validate-brainstorming",
    "validate-development",
    "validate-governance",
}
HOOK_MODES = {"brainstorming", "development"}
_ENV_ALLOWLIST = {
    "CI",
    "HOME",
    "LANG",
    "LC_ALL",
    "LOGNAME",
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "USER",
    "VIRTUAL_ENV",
    "WINDIR",
}


def run_project_validation_hook(
    root: Path,
    *,
    mode: str,
    command: str,
    timeout_seconds: float = HOOK_TIMEOUT_SECONDS,
) -> ValidationResult:
    result = ValidationResult()
    root = root.resolve()
    hook_path = root / HOOK_PATH
    if not hook_path.is_file():
        return result
    if os.environ.get(HOOK_SKIP_ENV) == "1":
        return result
    if os.environ.get(HOOK_ACTIVE_ENV) == "1":
        result.add_failure("Project validation hook recursion is not allowed.")
        return result
    if mode not in HOOK_MODES or command not in HOOK_COMMANDS:
        result.add_failure(f"Project validation hook received unsupported mode/command: {mode}/{command}")
        return result

    try:
        ledger = ProtectedStateLedger.capture(root)
    except (OSError, RuntimeError) as exc:
        result.add_failure(f"Project validation hook protected-state capture failed: {exc}")
        return result

    command_line = [
        sys.executable,
        str(HOOK_PATH),
        "--mode",
        mode,
        "--command",
        command,
        "--json",
    ]
    process_result = _run_bounded_process(
        command_line,
        root,
        timeout_seconds=timeout_seconds,
    )
    changed_paths = ledger.changed_paths()
    if changed_paths:
        restore_failures = ledger.restore(changed_paths)
        display = ", ".join(changed_paths[:10])
        suffix = "" if len(changed_paths) <= 10 else f", and {len(changed_paths) - 10} more"
        result.add_failure(f"Project validation hook mutated protected worktree paths: {display}{suffix}")
        for failure in restore_failures:
            result.add_failure(f"Project validation hook mutation rollback failed: {failure}")
    if isinstance(process_result, str):
        result.add_failure(process_result)
        return result
    return _parse_hook_payload(process_result, result)


def add_project_validation_hook_result(
    root: Path,
    result: ValidationResult,
    *,
    mode: str,
    command: str,
) -> None:
    hook_result = run_project_validation_hook(root, mode=mode, command=command)
    result.failures.extend(hook_result.failures)
    result.warnings.extend(hook_result.warnings)


def hook_suppressed_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment[HOOK_SKIP_ENV] = "1"
    return environment


def _run_bounded_process(
    command: list[str],
    root: Path,
    *,
    timeout_seconds: float,
) -> tuple[int, bytes, bytes] | str:
    environment = {key: value[:8192] for key, value in os.environ.items() if key in _ENV_ALLOWLIST and value}
    environment["PYTHONIOENCODING"] = "utf-8"
    environment[HOOK_ACTIVE_ENV] = "1"
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
            creationflags=creation_flags,
        )
    except OSError as exc:
        return f"Project validation hook could not start: {exc}"

    stdout = bytearray()
    stderr = bytearray()
    overflow = threading.Event()
    readers = [
        threading.Thread(
            target=_read_limited,
            args=(process.stdout, stdout, HOOK_STDOUT_LIMIT, overflow),
            daemon=True,
        ),
        threading.Thread(
            target=_read_limited,
            args=(process.stderr, stderr, HOOK_STDERR_LIMIT, overflow),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + max(0.01, min(timeout_seconds, HOOK_TIMEOUT_SECONDS))
    failure = ""
    while process.poll() is None or any(reader.is_alive() for reader in readers):
        if overflow.is_set():
            failure = "Project validation hook exceeded the stdout/stderr size limit."
            break
        if time.monotonic() >= deadline:
            failure = f"Project validation hook timed out after {timeout_seconds:g} seconds."
            break
        time.sleep(0.01)
    if overflow.is_set() and not failure:
        failure = "Project validation hook exceeded the stdout/stderr size limit."
    if failure:
        _terminate_process_tree(process)
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
    for reader in readers:
        reader.join(timeout=1)
    for stream in [process.stdout, process.stderr]:
        if stream is not None:
            stream.close()
    if any(reader.is_alive() for reader in readers):
        return failure or "Project validation hook output streams did not close."
    if failure:
        return failure
    return process.returncode, bytes(stdout), bytes(stderr)


def _read_limited(stream, target: bytearray, limit: int, overflow: threading.Event) -> None:
    if stream is None:
        return
    while True:
        chunk = stream.read(8192)
        if not chunk:
            return
        remaining = limit + 1 - len(target)
        if remaining > 0:
            target.extend(chunk[:remaining])
        if len(target) > limit:
            overflow.set()
            return


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        try:
            process.kill()
        except OSError:
            pass


def _parse_hook_payload(process_result: tuple[int, bytes, bytes], result: ValidationResult) -> ValidationResult:
    returncode, stdout, stderr = process_result
    if returncode != 0:
        detail = _decode_detail(stderr) or _decode_detail(stdout)
        suffix = f": {detail}" if detail else ""
        result.add_failure(f"Project validation hook exited with status {returncode}{suffix}")
        return result
    try:
        text = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        result.add_failure(f"Project validation hook stdout is not valid UTF-8: {exc}")
        return result
    if not text.strip():
        result.add_failure("Project validation hook produced empty stdout.")
        return result
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        result.add_failure(f"Project validation hook stdout must be exactly one JSON object: {exc}")
        return result
    if not isinstance(payload, dict):
        result.add_failure("Project validation hook JSON root must be an object.")
        return result
    required = {"failures", "warnings"}
    if set(payload) != required:
        result.add_failure("Project validation hook JSON must contain only failures and warnings.")
        return result
    valid_fields = True
    for field in sorted(required):
        values = payload[field]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            result.add_failure(f"Project validation hook {field} must be an array of strings.")
            valid_fields = False
    if not valid_fields:
        return result
    result.failures.extend(payload["failures"])
    result.warnings.extend(payload["warnings"])
    return result


def _decode_detail(value: bytes) -> str:
    return value.decode("utf-8", errors="replace").strip()[:500]
