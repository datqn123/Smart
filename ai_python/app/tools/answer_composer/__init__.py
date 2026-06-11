from __future__ import annotations
import json
import logging
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError
from app.graph.state import ToolState
from app.harness.think_log import think
from app.tools import memory_block

log = logging.getLogger(__name__)


class ComposerAnswer(BaseModel):
    """Cau tra loi cuoi cho user, ket thuc bang dong bat dau 'Gợi ý:'."""
    answer: str


_PROMPT = ("{skill}\n\n--- SOAN TRA LOI ---\nraw_require: {raw_require}\n"
           "data: {data}\n{memory}\nKet thuc answer bang dong bat dau 'Gợi ý:'.")


def execute(state: ToolState, *, llm, **_) -> dict:
    think("answer_composer", 'du lieu da duoc duyet, soan cau tra loi tieng Viet cho "%.100s"',
          state["raw_require"])
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          data=json.dumps(state["upstream_data"], ensure_ascii=False)[:4000],
                          memory=memory_block(state))
    try:
        out = llm.complete_structured(system=state["skill"], user=user,
                                      output_model=ComposerAnswer)
        answer = out.answer.strip()
    except StructuredOutputError as exc:
        log.warning("answer_composer structured output failed: %s", exc)
        answer = ""
    if not answer:
        think("answer_composer", "-> LLM tra answer rong/khong doc duoc, de SM thu lai")
    else:
        think("answer_composer", "-> soan xong cau tra loi %d ky tu", len(answer))
        if "gợi ý:" not in answer.lower():
            log.warning("answer_composer missing 'Gợi ý:' marker — self_validate will fail")
    return {"answer": answer}


def self_validate(state: ToolState):
    answer = (state.get("output") or {}).get("answer", "")
    if not answer.strip():
        return False, "answer rong"
    if "gợi ý:" not in answer.lower():
        return False, "thieu phan gợi ý buoc tiep (marker 'Gợi ý:')"
    return True, None
