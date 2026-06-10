from __future__ import annotations
import json
from app.graph.state import ToolState

_PROMPT = ("{skill}\n\n--- SOAN TRA LOI ---\nraw_require: {raw_require}\n"
           "data: {data}\n\nTra ve JSON {{\"answer\":\"...\"}}, "
           "ket thuc bang dong bat dau 'Gợi ý:'.")


def execute(state: ToolState, *, llm, **_) -> dict:
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(state["upstream_data"], ensure_ascii=False)[:4000])
    raw = llm.complete(system=state["skill"], user=user, role="default").strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    # answer="" -> self_validate fail -> SM retry (khong sap run_session).
    answer = parsed.get("answer", "") if isinstance(parsed, dict) else ""
    return {"answer": answer}


def self_validate(state: ToolState):
    answer = (state.get("output") or {}).get("answer", "")
    if not answer.strip():
        return False, "answer rong"
    if "gợi ý:" not in answer.lower():
        return False, "thieu phan gợi ý buoc tiep (marker 'Gợi ý:')"
    return True, None
