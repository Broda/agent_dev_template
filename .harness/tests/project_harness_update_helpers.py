from __future__ import annotations

import json
import shutil
from pathlib import Path

from workflow_test_helpers import REPO_ROOT, LabWorkflowTestCase, run_cmd


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

    def install_finalized_cli_project(self, project: Path) -> None:
        fixture_path = REPO_ROOT / ".harness/tests/fixtures/finalized_state_cli_data_pipeline_v2.json"
        state = json.loads(fixture_path.read_text(encoding="utf-8"))
        history_root = project / ".harness/history"
        (history_root / "sessions").mkdir(parents=True, exist_ok=True)
        (history_root / "notes").mkdir(parents=True, exist_ok=True)
        (history_root / "ideas").mkdir(parents=True, exist_ok=True)
        (history_root / "exports").mkdir(parents=True, exist_ok=True)
        session_files = []
        for relative_path in state["artifacts"]["sessionFiles"] + [state["artifacts"]["finalizationSession"]]:
            if not relative_path:
                continue
            archived = f".harness/history/{relative_path}"
            session_files.append(archived)
            session_path = project / archived
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session_path.write_text("# Finalized Session\n\n- Status: finalized\n", encoding="utf-8")
        state["artifacts"]["sessionFiles"] = session_files
        state["artifacts"]["finalizationSession"] = session_files[-1]
        state["governance"]["latestReviewSession"] = session_files[0]
        (history_root / "IDEA_CATALOG.md").write_text(
            "# Idea Catalog\n\n| ID | Title | Status | Owner | Sessions | Export | Notes |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| {state['ideaId']} | {state['projectName']} | finalized | Test User | `{session_files[0]}` | _n/a_ | _none_ |\n",
            encoding="utf-8",
        )
        (history_root / "NOTES_CATALOG.md").write_text(
            "# Notes Catalog\n\n| ID | Title | Date | Idea | Source | Path | Tags |\n|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        (project / "state/project-init.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        (project / "MODE.md").write_text(
            "# Repository Mode\n\nCurrent mode: development\n\nAllowed values:\n\n- brainstorming\n- development\n\n"
            "Switch modes with `./scripts/finalize-project`.\n",
            encoding="utf-8",
        )
        run_cmd(["./scripts/render-development-docs"], cwd=project)
