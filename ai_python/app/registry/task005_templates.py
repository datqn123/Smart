"""Template registry loader for Task005 (file-only).

Registry shape (JSON):

```json
{
  "templates": [
    {
      "template_id": "sales_by_day_v1",
      "intent": "report",
      "description": "Daily sales rollup.",
      "params": { "date_from": "2026-04-01", "date_to": "2026-04-07" },
      "smoke_safe": true
    }
  ]
}
```
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SmokeTemplate(BaseModel):
    """One template registry entry consumed by smoke + future Chat Agent."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    intent: str = Field(min_length=1)
    description: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)
    params_schema: dict[str, Any] = Field(default_factory=dict)
    smoke_safe: bool = False

    @field_validator("template_id")
    @classmethod
    def _strip_template_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("template_id must not be blank")
        return cleaned


class TemplateRegistry(BaseModel):
    """Top-level template registry."""

    model_config = ConfigDict(extra="forbid")

    templates: list[SmokeTemplate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_template_ids(self) -> TemplateRegistry:
        seen: set[str] = set()
        for tpl in self.templates:
            if tpl.template_id in seen:
                raise ValueError(f"duplicate template_id: {tpl.template_id}")
            seen.add(tpl.template_id)
        return self

    def smoke_safe_templates(self) -> list[SmokeTemplate]:
        return [tpl for tpl in self.templates if tpl.smoke_safe]


def load_registry_from_dict(payload: dict[str, Any]) -> TemplateRegistry:
    """Validate a parsed JSON / YAML dict as a TemplateRegistry."""

    return TemplateRegistry.model_validate(payload)


def load_registry_from_path(path: Path) -> TemplateRegistry:
    """Read a JSON registry file and validate it (UTF-8 only)."""

    raw = path.read_text(encoding="utf-8")
    return load_registry_from_dict(json.loads(raw))
