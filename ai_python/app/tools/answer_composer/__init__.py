from __future__ import annotations
import json
import logging
from app.graph.state import ToolState
from app.tools import memory_block

log = logging.getLogger(__name__)

_PROMPT = ("{skill}\n\n--- SOAN TRA LOI ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}\nTra ve JSON {{\"answer\":\"...\"}}, "
           "ket thuc bang dong bat dau 'Gợi ý:'.")


def execute(state: ToolState, *, llm, **_) -> dict:
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(state["upstream_data"], ensure_ascii=False)[:4000],
                          memory=memory_block(state))
    raw = llm.complete(system=state["skill"], user=user, role="default").strip()
    log.debug("answer_composer LLM raw: %.300s", raw)
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    answer = parsed.get("answer", "") if isinstance(parsed, dict) else ""
    if not answer:
        log.warning("answer_composer empty answer malformed=%s", parsed is None)
    else:
        has_goi_y = "gợi ý:" in answer.lower()
        log.info("answer_composer answer_len=%d has_goi_y=%s", len(answer), has_goi_y)
        if not has_goi_y:
            log.warning("answer_composer missing 'Gợi ý:' marker — self_validate will fail")
    return {"answer": answer}


def self_validate(state: ToolState):
    answer = (state.get("output") or {}).get("answer", "")
    if not answer.strip():
        return False, "answer rong"
    if "gợi ý:" not in answer.lower():
        return False, "thieu phan gợi ý buoc tiep (marker 'Gợi ý:')"
    return True, None
