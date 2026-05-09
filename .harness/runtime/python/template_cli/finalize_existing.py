from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from template_cli.finalize_helpers import existing_state_value


@dataclass(frozen=True)
class ExistingFinalizeValues:
    project_name: str
    purpose: str
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
    problem_statement: str
    target_users: str
    why_now: str
    expected_value: str
    solution_summary: str
    mvp_scope: str
    out_of_scope: str
    assumptions: str
    non_goals: str
    key_decisions: str
    top_risks: str
    mitigation_plans: str
    contingencies: str
    remaining_risks: str
    latest_review_outcome: str
    latest_review_session: str


def _load_existing_finalize_values(root: Path) -> ExistingFinalizeValues:
    return ExistingFinalizeValues(
        project_name=existing_state_value(root, "projectName"),
        purpose=existing_state_value(root, "purpose"),
        project_type=existing_state_value(root, "projectType"),
        language=existing_state_value(root, "techStack.language"),
        runtime=existing_state_value(root, "techStack.runtime"),
        framework=existing_state_value(root, "techStack.framework"),
        package_tool=existing_state_value(root, "techStack.packageTool"),
        persistence=existing_state_value(root, "persistence"),
        authentication=existing_state_value(root, "authentication"),
        determinism=existing_state_value(root, "determinism"),
        packaging=existing_state_value(root, "packaging"),
        constraints=existing_state_value(root, "constraints"),
        build_command=existing_state_value(root, "commands.build"),
        run_command=existing_state_value(root, "commands.run"),
        test_command=existing_state_value(root, "commands.test"),
        problem_statement=existing_state_value(root, "product.problemStatement"),
        target_users=existing_state_value(root, "product.targetUsers"),
        why_now=existing_state_value(root, "product.whyNow"),
        expected_value=existing_state_value(root, "product.expectedValue"),
        solution_summary=existing_state_value(root, "product.solutionSummary"),
        mvp_scope=existing_state_value(root, "product.mvpScope"),
        out_of_scope=existing_state_value(root, "product.outOfScope"),
        assumptions=existing_state_value(root, "product.assumptions"),
        non_goals=existing_state_value(root, "product.nonGoals"),
        key_decisions=existing_state_value(root, "governance.keyDecisions"),
        top_risks=existing_state_value(root, "governance.topRisks"),
        mitigation_plans=existing_state_value(root, "governance.mitigationPlans"),
        contingencies=existing_state_value(root, "governance.contingencies"),
        remaining_risks=existing_state_value(root, "governance.remainingAcceptedRisks"),
        latest_review_outcome=existing_state_value(root, "governance.latestReviewOutcome"),
        latest_review_session=existing_state_value(root, "governance.latestReviewSession"),
    )
