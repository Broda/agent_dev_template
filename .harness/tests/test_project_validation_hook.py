from __future__ import annotations

import os
import sys
import time
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

    def test_recursive_invocation_is_rejected(self) -> None:
        self._write_payload({"failures": [], "warnings": []})

        with mock.patch.dict(os.environ, {HOOK_ACTIVE_ENV: "1"}):
            result = self._run_hook()

        self.assertEqual(["Project validation hook recursion is not allowed."], result.failures)

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

        result = self._run_hook(timeout_seconds=10)

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

    def _run_hook(self, *, timeout_seconds: float = 2):
        return run_project_validation_hook(
            self.repo,
            mode="brainstorming",
            command="validate-governance",
            timeout_seconds=timeout_seconds,
        )

    def _write_payload(self, payload: object) -> None:
        self._write_hook(f"import json\nprint(json.dumps({payload!r}))\n")

    def _write_hook(self, source: str) -> Path:
        path = self.repo / "scripts/project_harness_validation.py"
        path.write_text(source.lstrip(), encoding="utf-8")
        return path


if __name__ == "__main__":
    import unittest

    unittest.main()
