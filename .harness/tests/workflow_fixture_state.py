from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRISTINE_STATE_FIXTURE = REPO_ROOT / ".harness/tests/fixtures/pristine_brainstorming_state.json"


def reset_project_state_for_workflow_tests(repo: Path) -> None:
    """Replace consumer-owned workflow state with a deterministic blank fixture."""
    fixture = json.loads(PRISTINE_STATE_FIXTURE.read_text(encoding="utf-8"))
    for relative_dir in fixture["clearDirectories"]:
        directory = repo / relative_dir
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True, exist_ok=True)
    for relative_path, content in fixture["files"].items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
