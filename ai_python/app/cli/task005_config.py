"""Job config loader for the Task005 CLI.

Two JSON inputs:

- ``objects.json`` — ``{ "objects": ["reporting.x_v1", ...] }``
- ``templates.json`` — see ``app.registry.task005_templates``
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.registry.task005_templates import TemplateRegistry, load_registry_from_path


class ObjectsAllowlist(BaseModel):
    """Allowlist of MCP `sql.describe` objects."""

    model_config = ConfigDict(extra="forbid")

    objects: list[str] = Field(default_factory=list)

    @field_validator("objects")
    @classmethod
    def _strip_unique(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in value:
            stripped = raw.strip()
            if not stripped:
                raise ValueError("object name must not be blank")
            if stripped in seen:
                raise ValueError(f"duplicate object name: {stripped}")
            seen.add(stripped)
            cleaned.append(stripped)
        return cleaned


@dataclass(frozen=True)
class JobConfig:
    """Resolved CLI job configuration."""

    objects: tuple[str, ...]
    registry: TemplateRegistry
    corpus_root: Path


def load_objects_from_path(path: Path) -> ObjectsAllowlist:
    """Read + validate a JSON allowlist file."""

    raw = path.read_text(encoding="utf-8")
    return ObjectsAllowlist.model_validate(json.loads(raw))


def load_job_config(
    *, objects_path: Path, templates_path: Path, corpus_root: Path
) -> JobConfig:
    """Compose ``JobConfig`` from validated files."""

    allowlist = load_objects_from_path(objects_path)
    registry = load_registry_from_path(templates_path)
    return JobConfig(
        objects=tuple(allowlist.objects),
        registry=registry,
        corpus_root=corpus_root,
    )
