from __future__ import annotations
import json
import logging
from app.graph.state import ToolState
from app.harness.think_log import think
from app.tools import memory_block

log = logging.getLogger(__name__)

_PROMPT = ("{skill}\n\n--- KIEM DINH ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}\nTra ve JSON {{\"verdict\":\"pass|fail\",\"reason\":\"...\"}}.")


def execute(state: ToolState, *, llm, **_) -> dict:
    data = state["upstream_data"]
    n_rows = len(data.get("rows", [])) if isinstance(data, dict) else 0
    think("data_validator", 'soi ket qua (%d dong) xem co du va dung de tra loi "%.100s" khong',
          n_rows, state["raw_require"])
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(data, ensure_ascii=False)[:4000],
                          memory=memory_block(state))
    raw = llm.complete(system=state["skill"], user=user, role="default").strip()
    log.debug("data_validator LLM raw: %.300s", raw)
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):
        log.warning("data_validator LLM output malformed raw_preview=%.200s", raw[:200])
        think("data_validator", "-> khong doc duoc ket luan tu LLM, bao loi de SM thu lai")
        return {"verdict": None, "reason": "LLM output khong hop le (khong parse duoc JSON)"}
    verdict = parsed.get("verdict")
    reason = parsed.get("reason", "")
    log.info("data_validator verdict=%s reason=%.120s", verdict, reason)
    if verdict == "pass":
        think("data_validator", "-> dat: %s", reason or "du lieu du de tra loi")
    else:
        think("data_validator", "-> KHONG dat: %s", reason)
    return {"verdict": verdict, "reason": reason}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("verdict") not in ("pass", "fail"):
        return False, f"verdict khong hop le: {out.get('verdict')!r}"
    return True, None
