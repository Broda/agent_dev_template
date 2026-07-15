from __future__ import annotations

import json
import shutil
from pathlib import Path

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


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

    def mark_state_schema_project_owned(self, project: Path) -> None:
        manifest_path = project / ".harness/commands/harness_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifactInventory"]["harnessOwned"].remove("state/project-init.schema.v2.json")
        manifest["artifactInventory"]["projectOwned"].append("state/project-init.schema.v2.json")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
