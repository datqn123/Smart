"""Load runtime agent prompts from markdown playbooks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent / "agents"
_CONTRACT_HEADER = "## JSON output contract"


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


def _read_agent_file(agent_id: str) -> str:
    path = _AGENTS_DIR / f"{agent_id}.md"
    if not path.is_file():
        raise FileNotFoundError(f"agent prompt not found: {agent_id} ({path})")
    return path.read_text(encoding="utf-8").strip()
