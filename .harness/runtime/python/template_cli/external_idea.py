from __future__ import annotations

import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from template_cli.workflow_data import normalize_idea_id

MAX_TEXT_LENGTH = 4000


def _clean_text(value: str, *, default: str = "") -> str:
    text = (value or default).strip()
    if "\x00" in text:
        raise ValueError("external idea fields cannot contain NUL bytes")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"external idea fields cannot exceed {MAX_TEXT_LENGTH} characters")
    return text


def _clean_identifier(value: str, *, default: str = "external") -> str:
    text = _clean_text(value, default=default)
    if "\n" in text:
        raise ValueError("external idea identifiers cannot contain newlines")
    return text or default


@dataclass(frozen=True)
class ExternalIdeaPayload:
    idea_id: str
    title: str
    summary: str = ""
    source: str = "external"
    source_id: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not _clean_text(self.idea_id):
            raise ValueError("idea_id is required")
        if not _clean_text(self.title):
            raise ValueError("title is required")
        object.__setattr__(self, "idea_id", _clean_identifier(self.idea_id, default="idea"))
        object.__setattr__(self, "title", _clean_text(self.title))
        object.__setattr__(self, "summary", _clean_text(self.summary))
        object.__setattr__(self, "source", _clean_identifier(self.source, default="external"))
        object.__setattr__(self, "source_id", _clean_identifier(self.source_id, default="") if self.source_id else "")
        cleaned_tags = [_clean_text(tag) for tag in self.tags]
        if any(not tag or "\n" in tag for tag in cleaned_tags):
            raise ValueError("external idea payload tags must be non-empty single-line strings")
        object.__setattr__(self, "tags", cleaned_tags)

    @property
    def normalized_idea_id(self) -> str:
        return normalize_idea_id(self.idea_id)


@dataclass(frozen=True)
class ExternalIdeaImportResult:
    ok: bool
    idea_id: str
    title: str
    status: str
    source: str
    source_id: str
    session_path: str = ""
    changed_files: list[str] = field(default_factory=list)
    readiness: str = "unknown"
    target_created: bool = False
    target_path: str = ""
    commit: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "ok": self.ok,
            "idea_id": self.idea_id,
            "title": self.title,
            "status": self.status,
            "source": self.source,
            "source_id": self.source_id,
            "session_path": self.session_path,
            "changed_files": self.changed_files,
            "readiness": self.readiness,
        }
        if self.target_created:
            data["target_created"] = True
        if self.target_path:
            data["target_path"] = self.target_path
        if self.commit:
            data["commit"] = self.commit
        return data


def external_idea_error_json(code: str, error: str) -> dict[str, str | bool]:
    return {"ok": False, "code": code, "error": error}


def external_idea_error_code(error: Exception) -> str:
    if isinstance(error, FileNotFoundError):
        return "payload_file_not_found"
    if isinstance(error, JSONDecodeError):
        return "invalid_json"
    if isinstance(error, ValueError):
        message = str(error)
        if "schema_version" in message:
            return "unsupported_schema"
        if "tags" in message:
            return "invalid_tags"
        if "required" in message:
            return "missing_required_field"
        if "NUL" in message or "newline" in message or "exceed" in message:
            return "invalid_field"
        return "invalid_payload"
    return "external_idea_error"


def load_external_idea_payload(path: Path) -> ExternalIdeaPayload:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("external idea payload must be a JSON object")
    if data.get("schema_version", 1) != 1:
        raise ValueError("unsupported external idea payload schema_version")
    return payload_from_mapping(data)


def payload_from_mapping(data: dict[str, Any]) -> ExternalIdeaPayload:
    tags = data.get("tags") or []
    if not isinstance(tags, list):
        raise ValueError("external idea payload tags must be a list")
    return ExternalIdeaPayload(
        idea_id=str(data.get("idea_id") or ""),
        title=str(data.get("title") or ""),
        summary=str(data.get("summary") or ""),
        source=str(data.get("source") or "external"),
        source_id=str(data.get("source_id") or ""),
        tags=[str(tag) for tag in tags],
    )
