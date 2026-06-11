from __future__ import annotations
import json
import logging
from typing import Literal
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError
from app.graph.state import ToolState
from app.harness.think_log import think
from app.tools import memory_block

log = logging.getLogger(__name__)


class ValidatorVerdict(BaseModel):
    """Ket luan du lieu co du va dung de tra loi raw_require khong."""
    verdict: Literal["pass", "fail"]
    reason: str


_PROMPT = ("{skill}\n\n--- KIEM DINH ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}")


def execute(state: ToolState, *, llm, **_) -> dict:
    data = state["upstream_data"]
    n_rows = len(data.get("rows", [])) if isinstance(data, dict) else 0
    think("data_validator", 'soi ket qua (%d dong) xem co du va dung de tra loi "%.100s" khong',
          n_rows, state["raw_require"])
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(data, ensure_ascii=False)[:4000],
                          memory=memory_block(state))
    try:
        v = llm.complete_structured(system=state["skill"], user=user,
                                    output_model=ValidatorVerdict)
    except StructuredOutputError as exc:
        log.warning("data_validator structured output failed: %s", exc)
        think("data_validator", "-> khong doc duoc ket luan tu LLM, bao loi de SM thu lai")
        return {"verdict": None, "reason": f"LLM output khong hop le: {exc}"}
    log.info("data_validator verdict=%s reason=%.120s", v.verdict, v.reason)
    if v.verdict == "pass":
        think("data_validator", "-> dat: %s", v.reason or "du lieu du de tra loi")
    else:
        think("data_validator", "-> KHONG dat: %s", v.reason)
    return {"verdict": v.verdict, "reason": v.reason}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("verdict") not in ("pass", "fail"):
        return False, f"verdict khong hop le: {out.get('verdict')!r}"
    return True, None
