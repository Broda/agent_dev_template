from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from template_cli.validator_manifest import load_harness_manifest


RUNTIME_ENV = "PROJECT_HARNESS_RUNTIME"
RUNTIME_COMMAND = "project-harness-runtime"
CONFIG_ERROR_EXIT = 78
READ_ONLY_FALLBACK_WARNING = (
    "harness-runtime warning: installed runtime is incompatible; "
    "using repo-local fallback at scripts/python/cli.py"
)
FALLBACK_UNAVAILABLE_ERROR = (
    "harness-runtime error: installed runtime is incompatible and repo-local fallback is unavailable"
)
MUTATING_INCOMPATIBLE_ERROR = (
    "harness-runtime error: installed runtime is incompatible for mutating command; refusing to continue"
)


@dataclass(frozen=True)
class RuntimeResolution:
    status: str
    command: tuple[str, ...]
    stderr: str = ""
    exit_code: int | None = None


def resolve_runtime(
    root: Path,
    backend_command: str,
    *,
    read_only: bool,
    env: Mapping[str, str] | None = None,
) -> RuntimeResolution:
    runtime_env = dict(os.environ if env is None else env)
    manifest = load_harness_manifest(root)
    override = runtime_env.get(RUNTIME_ENV, "").strip()

    if override:
        override_path = Path(override)
        if override_path.is_dir():
            return _source_checkout_resolution(override_path, backend_command)
        runtime_path = override
    else:
        runtime_path = shutil.which(RUNTIME_COMMAND, path=runtime_env.get("PATH"))

    if not runtime_path:
        return _repo_local_resolution(root, backend_command)

    if _runtime_is_compatible(runtime_path, manifest, backend_command):
        return RuntimeResolution("installed", (runtime_path, backend_command))

    local_resolution = _repo_local_resolution(root, backend_command)
    if read_only and local_resolution.status == "repo-local":
        return RuntimeResolution(
            "repo-local",
            local_resolution.command,
            stderr=READ_ONLY_FALLBACK_WARNING,
        )
    if read_only:
        return RuntimeResolution("failed", (), stderr=FALLBACK_UNAVAILABLE_ERROR, exit_code=CONFIG_ERROR_EXIT)
    return RuntimeResolution("failed", (), stderr=MUTATING_INCOMPATIBLE_ERROR, exit_code=CONFIG_ERROR_EXIT)


def _source_checkout_resolution(source_root: Path, backend_command: str) -> RuntimeResolution:
    cli_path = source_root / "scripts/python/cli.py"
    if not cli_path.exists():
        return RuntimeResolution("failed", (), stderr=FALLBACK_UNAVAILABLE_ERROR, exit_code=CONFIG_ERROR_EXIT)
    return RuntimeResolution("source-override", (sys.executable, cli_path.as_posix(), backend_command))


def _repo_local_resolution(root: Path, backend_command: str) -> RuntimeResolution:
    cli_path = root / "scripts/python/cli.py"
    if not cli_path.exists():
        return RuntimeResolution("failed", (), stderr=FALLBACK_UNAVAILABLE_ERROR, exit_code=CONFIG_ERROR_EXIT)
    return RuntimeResolution("repo-local", (sys.executable, cli_path.as_posix(), backend_command))


def _runtime_is_compatible(runtime_path: str, manifest: dict, backend_command: str) -> bool:
    version = _runtime_version(runtime_path)
    if not version:
        return False

    compatibility = manifest.get("compatibility", {})
    expected = {
        "wrapperRuntimeVersion": compatibility.get("wrapperRuntimeVersion"),
        "capabilityVersion": compatibility.get("capabilityVersion"),
        "stateSchemaVersion": compatibility.get("stateSchemaVersion"),
    }
    for key, value in expected.items():
        if version.get(key) != value:
            return False

    supported_commands = version.get("supportedBackendCommands")
    return isinstance(supported_commands, list) and backend_command in supported_commands


def _runtime_version(runtime_path: str) -> dict | None:
    completed = subprocess.run(
        [runtime_path, "version", "--json"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    try:
        version = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    return version if isinstance(version, dict) else None
