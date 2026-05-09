from __future__ import annotations

from dataclasses import dataclass

from template_cli.finalize_existing import ExistingFinalizeValues
from template_cli.finalize_helpers import (
    ask_non_empty,
    choose_from_list,
    choose_project_type,
    infer_project_type,
    summarize_decisions,
)
from template_cli.finalize_validation import _pick_noninteractive_choice, _required_value


@dataclass(frozen=True)
class FinalizeProjectSettings:
    project_type: str
    language: str
    runtime: str
    framework: str
    package_tool: str
    persistence: str
    authentication: str
    determinism: str
    packaging: str
    constraints: str
    build_command: str
    run_command: str
    test_command: str
    key_decisions: str


def _collect_finalize_project_settings(
    existing: ExistingFinalizeValues,
    *,
    project_name: str,
    objective: str,
    constraints_source: str,
    interactive: bool,
    missing_fields: list[str],
) -> FinalizeProjectSettings:
    if interactive:
        project_type = choose_project_type(existing.project_type or infer_project_type(project_name, objective))
        language = ask_non_empty("Language", existing.language)
        runtime = ask_non_empty("Runtime", existing.runtime)
        framework = ask_non_empty("Framework (if any, else 'None')", existing.framework or "None")
        package_tool = ask_non_empty(
            "Package manager/build tool (if any, else 'None')", existing.package_tool or "None"
        )
        persistence = choose_from_list(
            "Persistence",
            existing.persistence,
            ["None", "File-based (JSON/YAML/etc.)", "SQLite", "Postgres/MySQL/Other RDBMS"],
        )
        authentication = choose_from_list(
            "Authentication", existing.authentication, ["None", "Local users", "External auth provider"]
        )
        determinism = choose_from_list(
            "Determinism/correctness sensitivity", existing.determinism, ["Normal", "High"]
        )
        packaging = choose_from_list(
            "Packaging/distribution planned",
            existing.packaging,
            ["None", "Yes (desktop installers / containers / artifacts)"],
        )
        constraints = ask_non_empty("Constraints (comma-separated; use 'None' if none)", constraints_source or "None")
        build_command = ask_non_empty("Build command", existing.build_command)
        run_command = ask_non_empty("Run command", existing.run_command)
        test_command = ask_non_empty("Test command", existing.test_command)
    else:
        project_type = _pick_noninteractive_choice(
            existing.project_type or infer_project_type(project_name, objective),
            "project type",
            missing_fields,
        )
        language = _required_value(existing.language, "language", missing_fields)
        runtime = _required_value(existing.runtime, "runtime", missing_fields)
        framework = _required_value(existing.framework or "None", "framework", missing_fields)
        package_tool = _required_value(existing.package_tool or "None", "package manager/build tool", missing_fields)
        persistence = _pick_noninteractive_choice(existing.persistence, "persistence", missing_fields)
        authentication = _pick_noninteractive_choice(existing.authentication, "authentication", missing_fields)
        determinism = _pick_noninteractive_choice(existing.determinism, "determinism/correctness sensitivity", missing_fields)
        packaging = _pick_noninteractive_choice(existing.packaging, "packaging/distribution planned", missing_fields)
        constraints = _required_value(constraints_source or "None", "constraints", missing_fields)
        build_command = _required_value(existing.build_command, "build command", missing_fields)
        run_command = _required_value(existing.run_command, "run command", missing_fields)
        test_command = _required_value(existing.test_command, "test command", missing_fields)

    key_decisions = existing.key_decisions or summarize_decisions(
        project_type, persistence, authentication, determinism, packaging
    )
    return FinalizeProjectSettings(
        project_type=project_type,
        language=language,
        runtime=runtime,
        framework=framework,
        package_tool=package_tool,
        persistence=persistence,
        authentication=authentication,
        determinism=determinism,
        packaging=packaging,
        constraints=constraints,
        build_command=build_command,
        run_command=run_command,
        test_command=test_command,
        key_decisions=key_decisions,
    )
