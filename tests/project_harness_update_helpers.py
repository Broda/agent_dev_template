from __future__ import annotations

import shutil
from pathlib import Path

from tests.workflow_test_helpers import LabWorkflowTestCase, run_cmd


class ProjectHarnessUpdateTestCase(LabWorkflowTestCase):
    def copy_source(self) -> Path:
        source = self.tmpdir / "source-template"
        shutil.copytree(
            self.repo,
            source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        return source

    def init_git_source(self, source: Path) -> str:
        run_cmd(["git", "init", "-b", "main"], cwd=source)
        run_cmd(["git", "config", "user.name", "Test User"], cwd=source)
        run_cmd(["git", "config", "user.email", "test@example.com"], cwd=source)
        run_cmd(["git", "add", "-A"], cwd=source)
        run_cmd(["git", "commit", "-m", "baseline"], cwd=source)
        return run_cmd(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
