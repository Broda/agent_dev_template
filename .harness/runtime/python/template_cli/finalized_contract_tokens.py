from __future__ import annotations

import re
from typing import Any

INTERFACE_TOKENS = {"cli", "api", "web_ui", "admin_ui", "worker", "library"}
SURFACE_TOKENS = {
    "cli_commands",
    "http_api",
    "browser_ui",
    "admin_ui",
    "data_pipeline",
    "local_files",
    "sqlite",
    "database",
    "library_api",
}
AUTHENTICATION_TOKENS = {"none", "local", "external", "unknown"}

_INTERFACE_ALIASES = {
    "cli": "cli",
    "command line": "cli",
    "command-line": "cli",
    "api": "api",
    "http api": "api",
    "rest api": "api",
    "web": "web_ui",
    "web ui": "web_ui",
    "browser": "web_ui",
    "browser ui": "web_ui",
    "admin": "admin_ui",
    "admin ui": "admin_ui",
    "worker": "worker",
    "job": "worker",
    "library": "library",
    "sdk": "library",
}
_SURFACE_ALIASES = {
    "cli": "cli_commands",
    "cli command": "cli_commands",
    "cli commands": "cli_commands",
    "command surface": "cli_commands",
    "api": "http_api",
    "http": "http_api",
    "http api": "http_api",
    "api endpoints": "http_api",
    "rest": "http_api",
    "web": "browser_ui",
    "web ui": "browser_ui",
    "browser": "browser_ui",
    "browser ui": "browser_ui",
    "admin": "admin_ui",
    "admin ui": "admin_ui",
    "data pipeline": "data_pipeline",
    "pipeline": "data_pipeline",
    "local files": "local_files",
    "file io": "local_files",
    "filesystem": "local_files",
    "sqlite": "sqlite",
    "database": "database",
    "db": "database",
    "library": "library_api",
    "library api": "library_api",
}
_AUTH_ALIASES = {
    "": "none",
    "none": "none",
    "no": "none",
    "n/a": "none",
    "_none_": "none",
    "not applicable": "none",
    "local": "local",
    "local users": "local",
    "external": "external",
    "oauth": "external",
    "sso": "external",
    "unknown": "unknown",
}


def normalize_capabilities(capabilities: dict[str, Any], state: dict) -> dict[str, Any]:
    interfaces = _token_list(capabilities.get("interfaces"), _INTERFACE_ALIASES, INTERFACE_TOKENS)
    surfaces = _token_list(capabilities.get("surfaces"), _SURFACE_ALIASES, SURFACE_TOKENS)
    authentication = _normalize_token(capabilities.get("authentication", state.get("authentication", "")), _AUTH_ALIASES)
    if not interfaces:
        interfaces = _infer_interfaces(state)
    if not surfaces:
        surfaces = _infer_surfaces(state, interfaces)
    if not authentication:
        authentication = "none"
    return {
        "interfaces": sorted(interfaces),
        "surfaces": sorted(surfaces),
        "authentication": authentication,
    }


def _infer_interfaces(state: dict) -> set[str]:
    text = " ".join([str(state.get("projectType", "") or ""), str(state.get("purpose", "") or "")])
    interfaces: set[str] = set()
    if _contains_word(text, "cli") or _contains_phrase(text, "command line"):
        interfaces.add("cli")
    if _contains_word(text, "api"):
        interfaces.add("api")
    if _contains_word(text, "web") or _contains_word(text, "browser"):
        interfaces.add("web_ui")
    if _contains_word(text, "library") or _contains_word(text, "sdk"):
        interfaces.add("library")
    return interfaces or {"cli"}


def _infer_surfaces(state: dict, interfaces: set[str]) -> set[str]:
    text = " ".join(
        [
            str(state.get("projectType", "") or ""),
            str(state.get("purpose", "") or ""),
            str(state.get("persistence", "") or ""),
        ]
    )
    surfaces: set[str] = set()
    if "cli" in interfaces:
        surfaces.add("cli_commands")
    if "api" in interfaces:
        surfaces.add("http_api")
    if "web_ui" in interfaces:
        surfaces.add("browser_ui")
    if "library" in interfaces:
        surfaces.add("library_api")
    if _contains_phrase(text, "data pipeline") or _contains_word(text, "pipeline"):
        surfaces.add("data_pipeline")
    if _contains_word(text, "sqlite"):
        surfaces.add("sqlite")
    elif _contains_word(text, "database"):
        surfaces.add("database")
    return surfaces or {"cli_commands"}


def _token_list(value: Any, aliases: dict[str, str], allowed: set[str]) -> set[str]:
    if not isinstance(value, list):
        value = [value] if value else []
    tokens: set[str] = set()
    for item in value:
        token = _normalize_token(item, aliases)
        if token in allowed:
            tokens.add(token)
    return tokens


def _normalize_token(value: Any, aliases: dict[str, str]) -> str:
    text = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    return aliases.get(text, text.replace(" ", "_"))


def _contains_word(text: str, token: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(token.lower())}(?![a-z0-9])", text.lower()))


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(phrase.lower())}(?![a-z0-9])", text.lower()))
