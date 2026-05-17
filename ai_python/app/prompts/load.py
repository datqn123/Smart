"""Load runtime agent prompts from markdown playbooks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent / "agents"
_CONTRACT_HEADER = "## JSON output contract"
CATALOG_DRAFT_ENTITY_TYPES = frozenset({"product", "category", "supplier", "customer"})


@lru_cache(maxsize=64)
def load_agent_prompt(agent_id: str) -> str:
    """System prompt body (markdown before JSON contract section, or full file)."""
    text = _read_agent_file(agent_id)
    if _CONTRACT_HEADER in text:
        return text.split(_CONTRACT_HEADER, 1)[0].strip()
    return text


@lru_cache(maxsize=64)
def load_agent_json_contract(agent_id: str) -> str | None:
    """Structured-output contract appended to LLM calls when present in the .md file."""
    text = _read_agent_file(agent_id)
    if _CONTRACT_HEADER not in text:
        return None
    return text.split(_CONTRACT_HEADER, 1)[1].strip()


def list_agent_prompt_ids() -> list[str]:
    return sorted(p.stem for p in _AGENTS_DIR.glob("*.md") if p.name.upper() != "README.MD")


def catalog_draft_entity_prompt_id(entity_type: str) -> str:
    """Agent id for entity-specific catalog_draft playbook (e.g. catalog_draft_product)."""
    entity = entity_type.strip().lower()
    if entity not in CATALOG_DRAFT_ENTITY_TYPES:
        raise ValueError(f"unknown catalog entity_type: {entity_type!r}")
    return f"catalog_draft_{entity}"


@lru_cache(maxsize=16)
def load_catalog_draft_system_prompt(entity_type: str) -> str:
    """
    Base catalog_draft rules + mandatory entity playbook.
    Call before generate_catalog_draft LLM — never use load_agent_prompt('catalog_draft') alone.
    """
    entity = entity_type.strip().lower()
    base = load_agent_prompt("catalog_draft")
    entity_body = load_agent_prompt(catalog_draft_entity_prompt_id(entity))
    return (
        f"{base}\n\n---\n\n"
        f"## Playbook bắt buộc — entity `{entity}`\n\n"
        "Đọc và tuân thủ **toàn bộ** phần dưới trước khi sinh JSON. "
        "Không dùng cột hoặc quy ước của entity khác.\n\n"
        f"{entity_body}"
    ).strip()


@lru_cache(maxsize=4)
def load_catalog_draft_json_contract() -> str | None:
    return load_agent_json_contract("catalog_draft")


def _read_agent_file(agent_id: str) -> str:
    path = _AGENTS_DIR / f"{agent_id}.md"
    if not path.is_file():
        raise FileNotFoundError(f"agent prompt not found: {agent_id} ({path})")
    return path.read_text(encoding="utf-8").strip()
