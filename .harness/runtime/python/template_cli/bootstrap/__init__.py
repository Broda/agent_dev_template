"""Project harness bootstrap and update package.

Re-exports the project-creation CLI entry points; internal helpers live in the
submodules. The re-exports are lazy (PEP 562) so importing an update submodule
does not eagerly initialize the whole package.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from template_cli.bootstrap.projects import (
        run_project_harness_new,
        run_project_harness_new_from_idea,
        run_project_harness_validate,
    )

__all__ = [
    "run_project_harness_new",
    "run_project_harness_new_from_idea",
    "run_project_harness_validate",
]


def __getattr__(name: str) -> object:
    # Forward to the projects module's namespace, matching the old flat
    # template_cli.bootstrap module.
    # importlib avoids re-entering this __getattr__ the way a from-import would.
    import importlib

    projects = importlib.import_module("template_cli.bootstrap.projects")
    try:
        return getattr(projects, name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
