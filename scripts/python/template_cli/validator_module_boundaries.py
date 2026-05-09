from __future__ import annotations

import ast
from pathlib import Path

from template_cli.io_helpers import ValidationResult, read_text


ALLOWED_FINALIZE_IMPORTS = {"run_finalize_project"}
WORKFLOW_MODULES = [
    "scripts/python/template_cli/workflow.py",
    "scripts/python/template_cli/workflow_catalog.py",
    "scripts/python/template_cli/workflow_commands.py",
    "scripts/python/template_cli/workflow_data.py",
    "scripts/python/template_cli/workflow_development_status.py",
    "scripts/python/template_cli/workflow_idea_commands.py",
    "scripts/python/template_cli/workflow_readiness.py",
    "scripts/python/template_cli/workflow_status.py",
]
DISALLOWED_MODULE_IMPORTS = {
    "scripts/python/template_cli/bootstrap_update_source.py": {"template_cli.bootstrap_update"},
}


def validate_module_boundaries(root: Path, result: ValidationResult) -> None:
    for relative_path in WORKFLOW_MODULES:
        path = root / relative_path
        if not path.exists():
            continue
        _validate_finalize_imports(path, relative_path, result)
    for relative_path, disallowed_modules in DISALLOWED_MODULE_IMPORTS.items():
        path = root / relative_path
        if not path.exists():
            continue
        _validate_disallowed_imports(path, relative_path, disallowed_modules, result)


def _validate_finalize_imports(path: Path, relative_path: str, result: ValidationResult) -> None:
    tree = ast.parse(read_text(path), filename=relative_path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "template_cli.finalize":
            continue
        imported_names = {alias.name for alias in node.names}
        disallowed = sorted(imported_names - ALLOWED_FINALIZE_IMPORTS)
        for name in disallowed:
            result.add_failure(
                f"Workflow module must import finalize helper '{name}' from a helper module, not template_cli.finalize: "
                f"{relative_path}"
            )


def _validate_disallowed_imports(
    path: Path,
    relative_path: str,
    disallowed_modules: set[str],
    result: ValidationResult,
) -> None:
    tree = ast.parse(read_text(path), filename=relative_path)
    for node in ast.walk(tree):
        imported_module = ""
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_module = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in disallowed_modules:
                    imported_module = alias.name
                    break
        if imported_module in disallowed_modules:
            result.add_failure(f"Module boundary violation: {relative_path} must not import {imported_module}.")
