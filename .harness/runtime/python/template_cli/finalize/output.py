from __future__ import annotations

from template_cli.finalize.helpers import STATE_FILE


def _print_finalization_result(session_path: str, export_path: str, *, write_export: bool) -> None:
    print(f"Canonical state saved: {STATE_FILE}")
    print(f"Finalization session log: {session_path}")
    if write_export:
        print(f"Optional project summary written: {export_path}")
    print("The repository has been successfully finalized into development mode.")
