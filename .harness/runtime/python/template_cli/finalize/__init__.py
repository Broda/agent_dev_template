"""In-place finalization package.

`run_finalize_project` is the only public entry point; workflow modules must
import it from here and everything else from the specific submodule.

The re-export is lazy (PEP 562) so importing a finalize submodule does not
eagerly initialize the whole package — several submodules are also imported by
workflow modules that this package's orchestration depends on.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from template_cli.finalize.project import run_finalize_project

__all__ = ["run_finalize_project"]


def __getattr__(name: str) -> object:
    # Forward to the orchestration module's namespace, matching the old flat
    # template_cli.finalize module. The module-boundary validator, not this
    # shim, is what forbids workflow modules from importing helpers this way.
    # importlib avoids re-entering this __getattr__ the way a from-import would.
    import importlib

    project = importlib.import_module("template_cli.finalize.project")
    try:
        return getattr(project, name)
    except AttributeError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
