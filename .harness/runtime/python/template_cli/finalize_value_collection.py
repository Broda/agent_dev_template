from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from template_cli.finalize_existing import ExistingFinalizeValues
from template_cli.finalize_helpers import first_value_for_label, is_placeholder_value, latest_session_path


@dataclass(frozen=True)
class HydratedFinalizeValues:
    objective: str
    problem_statement: str
    target_users: str
    why_now: str
    expected_value: str
    solution_summary: str
    mvp_scope: str
    out_of_scope: str
    assumptions: str
    non_goals: str
    top_risks: str
    mitigation_plans: str
    contingencies: str
    remaining_risks: str
    latest_review_outcome: str
    latest_review_session: str
    constraints_source: str


def _hydrate_finalize_values(
    existing: ExistingFinalizeValues,
    hydrate_files: list[Path],
    session_paths: list[str],
) -> HydratedFinalizeValues:
    objective = existing.purpose or ""
    if not objective:
        for label in [
            "One-sentence objective",
            "Problem statement",
            "Value hypothesis",
            "Summary rationale",
            "Situation summary",
        ]:
            objective = first_value_for_label(hydrate_files, label)
            if objective:
                break

    constraints_source = existing.constraints if not is_placeholder_value(existing.constraints) else ""
    if not constraints_source:
        constraints_source = first_value_for_label(hydrate_files, "Constraints")

    return HydratedFinalizeValues(
        objective=objective,
        problem_statement=existing.problem_statement or first_value_for_label(hydrate_files, "Problem statement"),
        target_users=existing.target_users
        or first_value_for_label(hydrate_files, "Affected users/personas")
        or first_value_for_label(hydrate_files, "Target users"),
        why_now=existing.why_now or first_value_for_label(hydrate_files, "Why now"),
        expected_value=existing.expected_value
        or first_value_for_label(hydrate_files, "Expected value")
        or first_value_for_label(hydrate_files, "Value hypothesis"),
        solution_summary=existing.solution_summary or first_value_for_label(hydrate_files, "Solution summary"),
        mvp_scope=existing.mvp_scope or first_value_for_label(hydrate_files, "MVP scope"),
        out_of_scope=existing.out_of_scope or first_value_for_label(hydrate_files, "Out of scope"),
        assumptions=existing.assumptions or first_value_for_label(hydrate_files, "Assumptions"),
        non_goals=existing.non_goals or first_value_for_label(hydrate_files, "Non-goals"),
        top_risks=existing.top_risks
        or first_value_for_label(hydrate_files, "Top risks")
        or first_value_for_label(hydrate_files, "Top risks (link to risk entries)"),
        mitigation_plans=existing.mitigation_plans
        or first_value_for_label(hydrate_files, "Mitigation plans")
        or first_value_for_label(hydrate_files, "Preventive mitigation"),
        contingencies=existing.contingencies or first_value_for_label(hydrate_files, "Contingency plan"),
        remaining_risks=existing.remaining_risks or first_value_for_label(hydrate_files, "Remaining accepted risks"),
        latest_review_outcome=existing.latest_review_outcome
        or first_value_for_label(hydrate_files, "Latest review outcome")
        or first_value_for_label(hydrate_files, "Result"),
        latest_review_session=existing.latest_review_session or latest_session_path(session_paths),
        constraints_source=constraints_source,
    )
