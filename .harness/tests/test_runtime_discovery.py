from __future__ import annotations

import json
import os
import stat
import sys
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / ".harness/runtime/python"))

from workflow_test_helpers import LabWorkflowTestCase  # noqa: E402

from template_cli.runtime_discovery import (  # noqa: E402
    CONFIG_ERROR_EXIT,
    FALLBACK_UNAVAILABLE_ERROR,
    MUTATING_INCOMPATIBLE_ERROR,
    READ_ONLY_FALLBACK_WARNING,
    RUNTIME_ENV,
    resolve_runtime,
)


class RuntimeDiscoveryTests(LabWorkflowTestCase):
    @unittest.skipIf(
        os.name == "nt",
        "fake installed runtime is a POSIX shebang script; PATH discovery and execution require POSIX",
    )
    def test_runtime_env_override_prefers_explicit_compatible_runtime(self) -> None:
        override = self.write_runtime("override-runtime", ["validate-governance"])
        path_runtime = self.write_runtime("path-runtime", ["validate-governance"])

        resolution = resolve_runtime(
            self.repo,
            "validate-governance",
            read_only=True,
            env={RUNTIME_ENV: override.as_posix(), "PATH": path_runtime.parent.as_posix()},
        )

        self.assertEqual(resolution.status, "installed")
        self.assertEqual(resolution.command, (override.as_posix(), "validate-governance"))
        self.assertEqual(resolution.stderr, "")

    def test_runtime_env_override_can_point_at_source_checkout(self) -> None:
        resolution = resolve_runtime(
            self.repo,
            "validate-governance",
            read_only=True,
            env={RUNTIME_ENV: self.repo.as_posix(), "PATH": ""},
        )

        self.assertEqual(resolution.status, "source-override")
        self.assertEqual(resolution.command, self.local_command("validate-governance"))

    @unittest.skipIf(
        os.name == "nt",
        "fake installed runtime is a POSIX shebang script; PATH discovery and execution require POSIX",
    )
    def test_compatible_installed_runtime_on_path_is_selected(self) -> None:
        runtime = self.write_runtime("project-harness-runtime", ["validate-governance"])

        resolution = resolve_runtime(
            self.repo,
            "validate-governance",
            read_only=True,
            env={"PATH": runtime.parent.as_posix()},
        )

        self.assertEqual(resolution.status, "installed")
        self.assertEqual(resolution.command, (runtime.as_posix(), "validate-governance"))

    def test_missing_installed_runtime_uses_local_fallback(self) -> None:
        resolution = resolve_runtime(
            self.repo,
            "validate-governance",
            read_only=True,
            env={"PATH": ""},
        )

        self.assertEqual(resolution.status, "repo-local")
        self.assertEqual(resolution.command, self.local_command("validate-governance"))

    @unittest.skipIf(
        os.name == "nt",
        "fake installed runtime is a POSIX shebang script; PATH discovery and execution require POSIX",
    )
    def test_incompatible_installed_runtime_warns_and_falls_back_for_read_only_command(self) -> None:
        runtime = self.write_runtime("project-harness-runtime", ["validate-governance"], capability_version=99)

        resolution = resolve_runtime(
            self.repo,
            "validate-governance",
            read_only=True,
            env={"PATH": runtime.parent.as_posix()},
        )

        self.assertEqual(resolution.status, "repo-local")
        self.assertEqual(resolution.command, self.local_command("validate-governance"))
        self.assertEqual(resolution.stderr, READ_ONLY_FALLBACK_WARNING)

    @unittest.skipIf(
        os.name == "nt",
        "fake installed runtime is a POSIX shebang script; PATH discovery and execution require POSIX",
    )
    def test_incompatible_installed_runtime_fails_closed_for_mutating_command(self) -> None:
        runtime = self.write_runtime("project-harness-runtime", ["sync-plugin-skills"], capability_version=99)

        resolution = resolve_runtime(
            self.repo,
            "sync-plugin-skills",
            read_only=False,
            env={"PATH": runtime.parent.as_posix()},
        )

        self.assertEqual(resolution.status, "failed")
        self.assertEqual(resolution.command, ())
        self.assertEqual(resolution.stderr, MUTATING_INCOMPATIBLE_ERROR)
        self.assertEqual(resolution.exit_code, CONFIG_ERROR_EXIT)

    def test_incompatible_read_only_runtime_fails_when_local_fallback_is_missing(self) -> None:
        runtime = self.write_runtime("project-harness-runtime", ["validate-governance"], capability_version=99)
        (self.repo / ".harness/runtime/python/cli.py").unlink()

        resolution = resolve_runtime(
            self.repo,
            "validate-governance",
            read_only=True,
            env={"PATH": runtime.parent.as_posix()},
        )

        self.assertEqual(resolution.status, "failed")
        self.assertEqual(resolution.stderr, FALLBACK_UNAVAILABLE_ERROR)
        self.assertEqual(resolution.exit_code, CONFIG_ERROR_EXIT)

    def write_runtime(
        self,
        name: str,
        supported_commands: list[str],
        *,
        capability_version: int | None = None,
    ) -> Path:
        runtime = self.tmpdir / name
        manifest = json.loads((self.repo / ".harness/commands/harness_manifest.json").read_text(encoding="utf-8"))
        compatibility = manifest["compatibility"]
        version = {
            "runtimeVersion": manifest["harnessVersion"],
            "pythonPackage": "project_harness_runtime",
            "pythonVersion": "3.12",
            "wrapperRuntimeVersion": compatibility["wrapperRuntimeVersion"],
            "capabilityVersion": capability_version or compatibility["capabilityVersion"],
            "stateSchemaVersion": compatibility["stateSchemaVersion"],
            "supportedBackendCommands": supported_commands,
        }
        runtime.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import sys

                if sys.argv[1:] == ["version", "--json"]:
                    print(json.dumps({json.dumps(version)}))
                    raise SystemExit(0)
                raise SystemExit(2)
                """
            ),
            encoding="utf-8",
        )
        runtime.chmod(runtime.stat().st_mode | stat.S_IXUSR)
        return runtime

    def local_command(self, backend_command: str) -> tuple[str, ...]:
        return (sys.executable, (self.repo / ".harness/runtime/python/cli.py").as_posix(), backend_command)


if __name__ == "__main__":
    unittest.main()
