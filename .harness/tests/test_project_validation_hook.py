from __future__ import annotations

import os
import stat
import sys
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from workflow_test_helpers import REPO_ROOT, LabWorkflowTestCase

SCRIPT_ROOT = REPO_ROOT / ".harness/runtime/python"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from template_cli.validation_hook import (  # noqa: E402
    HOOK_ACTIVE_ENV,
    HOOK_STDERR_LIMIT,
    HOOK_STDOUT_LIMIT,
    run_project_validation_hook,
)
from template_cli.validators import run_validate_governance  # noqa: E402


@unittest.skipUnless(sys.platform == "linux", "project validation hooks require Linux /proc containment")
class ProjectValidationHookContractTests(LabWorkflowTestCase):
    def test_absent_hook_succeeds_without_warning(self) -> None:
        result = self._run_hook()
        self.assertEqual([], result.failures)
        self.assertEqual([], result.warnings)

    def test_success_uses_strict_arguments_cwd_and_sanitized_environment(self) -> None:
        expected_root = str(self.repo)
        self._write_hook(
            f"""
import argparse
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["brainstorming", "development"], required=True)
parser.add_argument(
    "--command",
    choices=["validate-brainstorming", "validate-development", "validate-governance"],
    required=True,
)
parser.add_argument("--json", action="store_true", required=True)
args = parser.parse_args()
failures = []
if args.mode != "brainstorming" or args.command != "validate-governance":
    failures.append("wrong arguments")
if str(Path.cwd()) != {expected_root!r}:
    failures.append("wrong cwd")
if os.environ.get("PROJECT_HARNESS_TEST_SECRET"):
    failures.append("environment was not sanitized")
print(json.dumps({{"failures": failures, "warnings": ["hook warning"]}}))
"""
        )

        with mock.patch.dict(os.environ, {"PROJECT_HARNESS_TEST_SECRET": "do-not-inherit"}):
            result = self._run_hook()

        self.assertEqual([], result.failures)
        self.assertEqual(["hook warning"], result.warnings)

    def test_hook_reported_failures_and_warnings_are_preserved(self) -> None:
        self._write_payload({"failures": ["project failure"], "warnings": ["project warning"]})
        result = self._run_hook()
        self.assertEqual(["project failure"], result.failures)
        self.assertEqual(["project warning"], result.warnings)

    def test_closed_json_contract_rejects_adversarial_payloads(self) -> None:
        cases = {
            "empty": "",
            "malformed": "{bad",
            "scalar": '"text"',
            "array": "[]",
            "missing": '{"failures": []}',
            "extra": '{"failures": [], "warnings": [], "schema": "unexpected"}',
            "wrong failures": '{"failures": "bad", "warnings": []}',
            "wrong warnings": '{"failures": [], "warnings": [1]}',
            "multiple": '{"failures": [], "warnings": []} {"failures": [], "warnings": []}',
            "trailing": '{"failures": [], "warnings": []} trailing',
        }
        for label, output in cases.items():
            with self.subTest(label=label):
                self._write_hook(f"import sys\nsys.stdout.write({output!r})\n")

                result = self._run_hook()

                self.assertTrue(result.failures, label)

    def test_invalid_utf8_is_rejected(self) -> None:
        self._write_hook("import sys\nsys.stdout.buffer.write(b'\\xff')\n")
        result = self._run_hook()
        self.assertIn("not valid UTF-8", result.failures[0])

    def test_nonzero_exit_is_rejected(self) -> None:
        self._write_hook("import sys\nprint('hook detail', file=sys.stderr)\nraise SystemExit(7)\n")

        result = self._run_hook()

        self.assertIn("exited with status 7: hook detail", result.failures[0])

    def test_oversized_stdout_and_stderr_are_rejected(self) -> None:
        cases = {
            "stdout": f"import sys\nsys.stdout.write('x' * {HOOK_STDOUT_LIMIT + 1})\n",
            "stderr": (
                "import json, sys\n"
                f"sys.stderr.write('x' * {HOOK_STDERR_LIMIT + 1})\n"
                "print(json.dumps({'failures': [], 'warnings': []}))\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                self._write_hook(source)

                result = self._run_hook()

                self.assertIn("size limit", result.failures[0])

    def test_spawn_error_is_rejected(self) -> None:
        self._write_payload({"failures": [], "warnings": []})
        ledger = mock.Mock()
        ledger.changed_paths.return_value = []

        with (
            mock.patch("template_cli.validation_hook.ProtectedStateLedger.capture", return_value=ledger),
            mock.patch(
                "template_cli.validation_hook.subprocess.Popen",
                side_effect=OSError("spawn denied"),
            ),
        ):
            result = self._run_hook()

        self.assertIn("could not start: spawn denied", result.failures[0])

    def test_direct_child_timeout_is_absolute(self) -> None:
        self._write_hook("import time\ntime.sleep(30)\n")

        started = time.monotonic()
        result = self._run_hook(timeout_seconds=0.15)

        self.assertLess(time.monotonic() - started, 2)
        self.assertIn("timed out after 0.15 seconds", result.failures[0])

    def test_descendant_process_is_terminated_on_timeout(self) -> None:
        marker = self.tmpdir / "descendant-survived"
        child = f"import pathlib,time;time.sleep(0.8);pathlib.Path({str(marker)!r}).write_text('bad', encoding='utf-8')"
        self._write_hook(
            f"import subprocess,sys,time\nsubprocess.Popen([sys.executable, '-c', {child!r}])\ntime.sleep(30)\n"
        )

        result = self._run_hook(timeout_seconds=0.15)
        time.sleep(1)

        self.assertIn("timed out", result.failures[0])
        self.assertFalse(marker.exists())

    def test_detached_descendant_is_terminated_on_timeout_before_delayed_writes(self) -> None:
        marker = self.tmpdir / "detached-timeout-survived"
        readme = self.repo / "README.md"
        before = readme.read_bytes()
        child = self._delayed_mutating_child(marker)
        self._write_hook(
            "import subprocess, sys, time\n"
            f"subprocess.Popen([sys.executable, '-c', {child!r}], "
            "start_new_session=True, stdin=subprocess.DEVNULL, "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            "time.sleep(30)\n"
        )

        result = self._run_hook(timeout_seconds=0.15)
        time.sleep(1)

        self.assertTrue(any("timed out after 0.15 seconds" in value for value in result.failures))
        self.assertFalse(marker.exists())
        self.assertEqual(before, readme.read_bytes())

    def test_success_return_with_detached_descendant_fails_and_prevents_delayed_writes(self) -> None:
        marker = self.tmpdir / "detached-success-survived"
        readme = self.repo / "README.md"
        before = readme.read_bytes()
        child = self._delayed_mutating_child(marker)
        self._write_hook(
            "import json, subprocess, sys\n"
            f"subprocess.Popen([sys.executable, '-c', {child!r}], "
            "start_new_session=True, stdin=subprocess.DEVNULL, "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            "print(json.dumps({'failures': [], 'warnings': []}))\n"
        )

        result = self._run_hook()
        time.sleep(1)

        self.assertIn("Project validation hook left descendant processes running.", result.failures)
        self.assertFalse(marker.exists())
        self.assertEqual(before, readme.read_bytes())

    def test_short_lived_child_that_exits_before_hook_is_allowed(self) -> None:
        self._write_hook(
            "import json, subprocess, sys\n"
            "subprocess.run([sys.executable, '-c', 'import time; time.sleep(0.05)'], check=True)\n"
            "print(json.dumps({'failures': [], 'warnings': []}))\n"
        )

        result = self._run_hook()

        self.assertEqual([], result.failures)

    def test_recursive_invocation_is_rejected(self) -> None:
        self._write_payload({"failures": [], "warnings": []})

        with mock.patch.dict(os.environ, {HOOK_ACTIVE_ENV: "1"}):
            result = self._run_hook()

        self.assertEqual(["Project validation hook recursion is not allowed."], result.failures)

    def test_recursive_governance_rejection_precedes_generic_validator_body(self) -> None:
        output = StringIO()
        with (
            mock.patch.dict(os.environ, {HOOK_ACTIVE_ENV: "1"}),
            mock.patch(
                "template_cli.validators.read_mode",
                side_effect=AssertionError("generic validator body was reached"),
            ),
            redirect_stdout(output),
        ):
            returncode = run_validate_governance(self.repo)

        self.assertEqual(1, returncode)
        self.assertIn("Project validation hook recursion is not allowed.", output.getvalue())

    def test_hook_cannot_recursively_invoke_governance_validation(self) -> None:
        self._write_hook(
            "import json\n"
            "import subprocess\n"
            "import sys\n"
            "nested = subprocess.run(\n"
            "    [sys.executable, '.harness/runtime/python/cli.py', 'validate-governance'],\n"
            "    capture_output=True,\n"
            "    text=True,\n"
            "    check=False,\n"
            ")\n"
            "failures = ['nested validation recursion was rejected'] if nested.returncode else "
            "['nested validation recursion unexpectedly succeeded']\n"
            "print(json.dumps({'failures': failures, 'warnings': []}))\n"
        )

        started = time.monotonic()
        result = self._run_hook(timeout_seconds=1)

        self.assertLess(time.monotonic() - started, 0.75)
        self.assertEqual(["nested validation recursion was rejected"], result.failures)

    def test_hook_mutation_is_detected_restored_and_reported(self) -> None:
        readme = self.repo / "README.md"
        before = readme.read_bytes()
        self._write_hook(
            "import json\n"
            "from pathlib import Path\n"
            "Path('README.md').write_text('mutated', encoding='utf-8')\n"
            "print(json.dumps({'failures': ['hook failed'], 'warnings': []}))\n"
        )

        result = self._run_hook()

        self.assertTrue(any("mutated protected worktree paths: README.md" in value for value in result.failures))
        self.assertIn("hook failed", result.failures)
        self.assertEqual(before, readme.read_bytes())

    def test_ignored_project_file_mutation_is_detected_and_restores_bytes_and_mode(self) -> None:
        ignored = self.repo / ".project-local/ignored.txt"
        ignored.parent.mkdir()
        ignored.write_text("preserve ignored bytes\n", encoding="utf-8")
        ignored.chmod(0o640)
        exclude = self.repo / ".git/info/exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write("\n.project-local/\n")
        before = ignored.read_bytes()
        before_mode = stat.S_IMODE(ignored.stat().st_mode)
        self._write_hook(
            "import json\n"
            "from pathlib import Path\n"
            "path = Path('.project-local/ignored.txt')\n"
            "path.write_text('mutated ignored bytes\\n', encoding='utf-8')\n"
            "path.chmod(0o777)\n"
            "print(json.dumps({'failures': [], 'warnings': []}))\n"
        )

        result = self._run_hook()

        self.assertTrue(
            any("mutated protected worktree paths: .project-local/ignored.txt" in value for value in result.failures)
        )
        self.assertEqual(before, ignored.read_bytes())
        self.assertEqual(before_mode, stat.S_IMODE(ignored.stat().st_mode))

    def _run_hook(self, *, timeout_seconds: float = 2):
        return run_project_validation_hook(
            self.repo,
            mode="brainstorming",
            command="validate-governance",
            timeout_seconds=timeout_seconds,
        )

    def _write_payload(self, payload: object) -> None:
        self._write_hook(f"import json\nprint(json.dumps({payload!r}))\n")

    @staticmethod
    def _delayed_mutating_child(marker: Path) -> str:
        return (
            "from pathlib import Path;import time;time.sleep(0.8);"
            f"Path({str(marker)!r}).write_text('bad', encoding='utf-8');"
            "Path('README.md').write_text('mutated', encoding='utf-8')"
        )

    def _write_hook(self, source: str) -> Path:
        path = self.repo / "scripts/project_harness_validation.py"
        path.write_text(source.lstrip(), encoding="utf-8")
        return path


class ProjectValidationHookPlatformTests(LabWorkflowTestCase):
    def test_present_hook_fails_closed_without_linux_proc_containment(self) -> None:
        hook = self.repo / "scripts/project_harness_validation.py"
        hook.write_text(
            "import json\nprint(json.dumps({'failures': [], 'warnings': []}))\n",
            encoding="utf-8",
        )

        with mock.patch("template_cli.validation_hook_process.sys.platform", "darwin"):
            result = run_project_validation_hook(
                self.repo,
                mode="brainstorming",
                command="validate-governance",
            )

        self.assertEqual(1, len(result.failures))
        self.assertIn("strong descendant containment is supported only on Linux with /proc", result.failures[0])


if __name__ == "__main__":
    unittest.main()
