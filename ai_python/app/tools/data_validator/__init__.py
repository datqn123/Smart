from __future__ import annotations
import json
from app.graph.state import ToolState

_PROMPT = ("{skill}\n\n--- KIEM DINH ---\nraw_require: {raw_require}\n"
           "data: {data}\n\nTra ve JSON {{\"verdict\":\"pass|fail\",\"reason\":\"...\"}}.")


def execute(state: ToolState, *, llm, **_) -> dict:
    data = state["upstream_data"]
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(data, ensure_ascii=False)[:4000])
    raw = llm.complete(system=state["skill"], user=user, role="default").strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):
        # verdict=None -> self_validate fail -> SM retry (khong sap run_session).
        return {"verdict": None, "reason": "LLM output khong hop le (khong parse duoc JSON)"}
    return {"verdict": parsed.get("verdict"), "reason": parsed.get("reason", "")}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("verdict") not in ("pass", "fail"):
        return False, f"verdict khong hop le: {out.get('verdict')!r}"
    return True, None
