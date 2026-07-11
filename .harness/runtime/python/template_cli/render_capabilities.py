from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from template_cli.render_helpers import MILESTONE_NAME, _state_list, _state_value


@dataclass(frozen=True)
class ProjectProfile:
    project_type: str
    has_authentication: bool
    has_web_ui: bool
    has_api: bool
    has_admin: bool
    uses_javascript: bool
    is_cli: bool
    is_data_pipeline: bool

    @property
    def interface_label(self) -> str:
        if self.is_cli and self.is_data_pipeline:
            return "CLI and data pipeline"
        if self.is_cli:
            return "CLI"
        if self.has_web_ui:
            return "web interface"
        return "operator interface"


def finalized_contract(state: dict) -> dict[str, Any]:
    contract = state.get("finalizedContract", {})
    return contract if isinstance(contract, dict) else {}


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = _format_mapping(item)
            else:
                text = str(item).strip()
            if text:
                values.append(text)
        return values
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _format_mapping(value: dict[str, Any]) -> str:
    preferred = [
        "name",
        "contract",
        "boundary",
        "invariant",
        "format",
        "domain",
        "description",
        "summary",
        "path",
    ]
    parts: list[str] = []
    for key in preferred:
        text = str(value.get(key, "") or "").strip()
        if text:
            parts.append(text)
    if not parts:
        parts = [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
    return " - ".join(parts)


def contract_list(state: dict, key: str) -> list[str]:
    contract = finalized_contract(state)
    return _string_list(contract.get(key))


def contract_milestones(state: dict) -> list[dict[str, Any]]:
    raw = finalized_contract(state).get("milestones", [])
    if not isinstance(raw, list):
        return []
    milestones: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if isinstance(item, str):
            milestones.append({"id": f"M{index}", "name": item, "tasks": [], "gates": []})
            continue
        if not isinstance(item, dict):
            continue
        milestone_id = str(item.get("id", "") or f"M{index}").strip()
        name = str(item.get("name", "") or item.get("title", "") or milestone_id).strip()
        tasks = _task_items(item.get("tasks", []))
        gates = _string_list(item.get("gates", []))
        milestones.append(
            {
                "id": milestone_id,
                "name": name,
                "goal": str(item.get("goal", "") or "").strip(),
                "tasks": tasks,
                "gates": gates,
            }
        )
    return milestones


def _task_items(value: Any) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    if not isinstance(value, list):
        return tasks
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                tasks.append({"area": "", "text": text})
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "") or item.get("task", "") or item.get("description", "") or "").strip()
        if not text:
            continue
        tasks.append({"area": str(item.get("area", "") or "").strip(), "text": text})
    return tasks


def active_milestone_name(state: dict) -> str:
    milestones = contract_milestones(state)
    if not milestones:
        return MILESTONE_NAME
    first = milestones[0]
    return f"{first['id']} - {first['name']}" if first["id"] != first["name"] else first["name"]


def milestone_summary_lines(state: dict) -> list[str]:
    lines: list[str] = []
    for milestone in contract_milestones(state):
        goal = milestone.get("goal", "")
        suffix = f" - {goal}" if goal else ""
        lines.append(f"{milestone['id']}: {milestone['name']}{suffix}")
    return lines


def project_profile(state: dict) -> ProjectProfile:
    contract = finalized_contract(state)
    capabilities = contract.get("capabilities", {})
    if not isinstance(capabilities, dict):
        capabilities = {}
    project_type = str(state.get("projectType", "") or "")
    project_text = " ".join([project_type, *contract_list(state, "capabilities")]).lower()
    interface_text = " ".join(_string_list(capabilities.get("interfaces"))).lower()
    surface_text = " ".join(_string_list(capabilities.get("surfaces"))).lower()
    stack_text = " ".join(
        [
            _state_value(state, "techStack.language"),
            _state_value(state, "techStack.runtime"),
            _state_value(state, "techStack.framework"),
            _state_value(state, "techStack.packageTool"),
        ]
    ).lower()
    auth_text = str(capabilities.get("authentication", state.get("authentication", "")) or "").strip().lower()

    is_cli = "cli" in project_text or "cli" in interface_text
    is_data_pipeline = "data pipeline" in project_text or "pipeline" in project_text or "pipeline" in surface_text
    web_signals = ["web", "browser", "react", "vite", "frontend"]
    api_signals = ["api", "http", "rest", "graphql", "endpoint", "axum", "fastapi"]
    admin_signals = ["admin", "editor", "privileged"]
    explicit_cli_only = is_cli and not any(token in interface_text for token in ["web", "api", "admin", "editor"])

    has_web_ui = not explicit_cli_only and any(token in " ".join([project_text, interface_text, stack_text]) for token in web_signals)
    has_api = not explicit_cli_only and any(token in " ".join([project_text, interface_text, surface_text, stack_text]) for token in api_signals)
    has_admin = not explicit_cli_only and any(token in " ".join([project_text, interface_text, surface_text]) for token in admin_signals)
    uses_javascript = any(token in stack_text for token in ["javascript", "typescript", "node", "npm", "pnpm", "yarn"])
    has_authentication = auth_text not in {"", "none", "no", "n/a", "_none_", "not applicable"}

    return ProjectProfile(
        project_type=project_type,
        has_authentication=has_authentication,
        has_web_ui=has_web_ui,
        has_api=has_api,
        has_admin=has_admin,
        uses_javascript=uses_javascript,
        is_cli=is_cli,
        is_data_pipeline=is_data_pipeline,
    )


def structured_domain_concepts(state: dict) -> list[str]:
    direct = contract_list(state, "domainConcepts")
    if direct:
        return direct
    model = contract_list(state, "domainModel") + contract_list(state, "dataModel")
    if model:
        return model[:6]
    legacy = _state_list(state, "implementation.domainConcepts") + _state_list(state, "mvpContract.domainConcepts")
    return legacy[:6]
