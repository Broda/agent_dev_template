from __future__ import annotations

import json

from workflow_test_helpers import LabWorkflowTestCase, run_cmd


class DevelopmentDomainTermsTests(LabWorkflowTestCase):
    def test_render_and_validate_development_allows_trading_domain_terms(self) -> None:
        self.write_render_fixture("finalized_state_web_app_v2.json")
        state_path = self.repo / "state/project-init.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projectName"] = "Trading Desk"
        state["projectType"] = "Web trading app"
        state["purpose"] = "Help traders monitor market conditions and portfolio risk."
        state["product"]["problemStatement"] = (
            "Trading teams need market data, position visibility, and onboarding for new accounts."
        )
        state["product"]["solutionSummary"] = (
            "Build a web app for market watchlists, order review, and trading workflow coordination."
        )
        state["product"]["mvpScope"] = "Ship market overview, account onboarding, and economy indicator screens."
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        run_cmd(["./scripts/render-development-docs"], cwd=self.repo)
        run_cmd(["./scripts/validate-development"], cwd=self.repo)

        readme = (self.repo / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("market conditions", readme)
        self.assertIn("trading workflow", readme)
