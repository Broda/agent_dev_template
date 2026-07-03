from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

GENERATED_ARTIFACT_PATHS = [
    ".harness/commands/CONVERSATIONAL_MODE.md",
    ".harness/commands/COMMANDS.md",
    ".harness/commands/harness_manifest.json",
    ".agents/plugins/marketplace.json",
    ".agents/skills/",
    ".harness/plugins/project-lifecycle-lab/skills/",
    ".harness/development/templates/docs/",
    ".harness/tests/fixtures/finalized_state_v2.json",
    ".harness/tests/fixtures/finalized_state_web_app_v2.json",
    ".harness/tests/fixtures/finalized_state_with_persistence_v2.json",
]


def run_harness_release_check(root: Path) -> int:
    steps = [
        ("Verify generated artifacts are in sync", _check_generated_artifacts),
        ("Run governance validation", _check_governance),
        ("Run Ruff lint and format checks", _check_ruff),
        ("Run full unit suite", _check_full_unit_suite),
        ("Run plugin package smoke", _check_plugin_package),
        ("Run fresh copy smoke", _check_fresh_copy),
        ("Run finalize and render fixture smoke", _check_finalize_render_fixtures),
        ("Run update dry-run and apply smoke", _check_update_smoke),
    ]

    print("Harness release check")
    for label, check in steps:
        print()
        print(f"==> {label}")
        result = check(root)
        if result != 0:
            print()
            print(f"FAILED: {label}")
            return result

    print()
    print("PASS: local harness release checks completed.")
    return 0


def _check_generated_artifacts(root: Path) -> int:
    before = _git_diff(root, GENERATED_ARTIFACT_PATHS)
    for command in [["./scripts/render-intent-docs"], ["./scripts/sync-plugin-skills"]]:
        result = _run(command, root)
        if result != 0:
            return result
    after = _git_diff(root, GENERATED_ARTIFACT_PATHS)
    if before != after:
        print("Generated artifacts changed after maintenance commands.")
        print("Review the diff, then rerun ./scripts/harness-release-check.")
        _run(["git", "diff", "--", *GENERATED_ARTIFACT_PATHS], root)
        return 1
    print("Generated artifacts are in sync.")
    return 0


def _check_governance(root: Path) -> int:
    return _run(["./scripts/validate-governance"], root)


def _check_ruff(root: Path) -> int:
    ruff_command = _ruff_command(root)
    if not ruff_command:
        print("Ruff was not found. Install it with pipx or run: python3 -m pip install -r requirements-dev.txt")
        return 1
    for args in [["check", "."], ["format", "--check", "."]]:
        result = _run([*ruff_command, *args], root)
        if result != 0:
            return result
    return 0


def _check_full_unit_suite(root: Path) -> int:
    return _run([sys.executable, "-m", "unittest", "discover", "-s", ".harness/tests", "-v"], root)


def _check_plugin_package(root: Path) -> int:
    return _run(
        [
            sys.executable,
            ".harness/plugins/project-lifecycle-lab/smoke_package.py",
            ".harness/plugins/project-lifecycle-lab",
        ],
        root,
    )


def _check_fresh_copy(root: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="harness-release-check.") as tmpdir:
        target = Path(tmpdir) / "harness-smoke"
        result = _run(["./scripts/project-harness", "new", target.as_posix(), "--no-git"], root)
        if result != 0:
            return result
        return _run(["./scripts/validate-governance"], target)


def _check_finalize_render_fixtures(root: Path) -> int:
    for pattern in ["test_finalization_regression.py", "test_development_rendering.py"]:
        result = _run(
            [sys.executable, "-m", "unittest", "discover", "-s", ".harness/tests", "-p", pattern, "-v"],
            root,
        )
        if result != 0:
            return result
    return 0


def _check_update_smoke(root: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="harness-release-update.") as tmpdir:
        base = Path(tmpdir)
        source = base / "source" / "template"
        project = base / "project" / "harness-smoke"
        shutil.copytree(root, source, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        result = _run([source / "scripts/project-harness", "new", project.as_posix(), "--no-git"], source)
        if result != 0:
            return result
        shutil.copy2(source / "MODE.md", project / "MODE.md")
        lab_wrapper = source / "scripts/lab.sh"
        lab_wrapper.write_text(
            lab_wrapper.read_text(encoding="utf-8") + "\n# release readiness update smoke\n",
            encoding="utf-8",
        )
        for command in [
            ["./scripts/project-harness", "update", "--dry-run", "--source-path", source.as_posix()],
            ["./scripts/project-harness", "update", "--apply", "--source-path", source.as_posix(), "--yes"],
            ["./scripts/validate-governance"],
        ]:
            result = _run(command, project)
            if result != 0:
                return result
    return 0


def _ruff_command(root: Path) -> list[str]:
    module_check = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if module_check.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    executable = shutil.which("ruff")
    return [executable] if executable else []


def _run(command: Sequence[object], cwd: Path) -> int:
    display = " ".join(str(part) for part in command)
    print(f"$ {display}")
    return subprocess.run([str(part) for part in command], cwd=cwd, check=False).returncode


def _git_diff(root: Path, paths: list[str]) -> str:
    result = subprocess.run(
        ["git", "diff", "--binary", "--", *paths],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""
