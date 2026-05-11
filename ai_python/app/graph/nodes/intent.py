"""Intent routing node."""

from __future__ import annotations

import logging

from langchain_core.messages import BaseMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.registry import normalize_intent
from app.graph.state import AgentState
from app.llm.schemas import IntentOutput

logger = logging.getLogger(__name__)

# Criteria only — no few-shot utterances; model must judge from conversation.
_INTENT_CLASSIFY_SYSTEM = (
    "Bạn phân loại một lượt hội thoại trong ứng dụng ERP để hệ thống chọn nhánh xử lý.\n\n"
    "Hai loại đích:\n"
    "• general_chat — trao đổi thông thường: chào hỏi, giải thích khái niệm, "
    "hướng dẫn thao tác giao diện ở mức chung, ý kiến cá nhân, hoặc nội dung "
    "không yêu cầu đọc dữ liệu vận hành đang lưu trong kho của ứng dụng để khẳng định sự kiện.\n"
    "• system_data_query — người dùng cần câu trả lời bám dữ liệu vận hành thực "
    "(thống kê, bảng kết quả, đối chiếu, mức số liệu hiện tại trong hệ thống); "
    "gồm cả lượt tiếp theo vẫn nhắm kiểm tra hoặc sửa sai một kết luận số liệu "
    "nếu ngữ cảnh quay lại việc tra cứu dữ liệu ứng dụng.\n\n"
    "Tự suy luận từ toàn bộ ngữ cảnh được cung cấp. Không liệt kê câu hỏi mẫu. "
    "Không mô tả hay tiết lộ schema hay tên bảng database."
)

_INTENT_JSON_CONTRACT = (
    'Single JSON object with exactly one key "intent". '
    'The value must be exactly the string general_chat or exactly the string '
    "system_data_query (ASCII, lowercase, underscore as shown). "
    "No markdown fences, no other keys, no explanation text."
)

_INTENT_MESSAGE_TAIL = 24


def _messages_for_intent(state: AgentState) -> list[BaseMessage]:
    """System + recent turns; avoids dumping huge Pydantic schema on the model."""
    raw = state.get("messages") or []
    tail = raw[-_INTENT_MESSAGE_TAIL:] if len(raw) > _INTENT_MESSAGE_TAIL else list(raw)
    return [SystemMessage(content=_INTENT_CLASSIFY_SYSTEM), *tail]


def _user_question_snippet(state: AgentState, max_chars: int = 220) -> str:
    for m in reversed(state.get("messages") or []):
        c = getattr(m, "content", "")
        if c:
            t = str(c).replace("\n", " ").strip()
            if len(t) > max_chars:
                return t[:max_chars] + "…"
            return t
    return "(no user text)"


def make_intent_node(deps: GraphDeps):
    def intent(state: AgentState) -> dict:
        logger.info("node=intent action=start")
        reg = deps.llm_registry
        if reg is None:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="intent",
                phase="Kết luận (stub, không gọi LLM)",
                detail="intent=general_chat",
            )
            return {"intent": "general_chat"}
        messages = _messages_for_intent(state)
        client = reg.get("intent")
        try:
            out = client.structured_predict(
                messages,
                IntentOutput,
                json_output_contract=_INTENT_JSON_CONTRACT,
            )
            raw = out.intent
        except Exception:
            logger.warning("intent structured_predict failed; routing to general_chat", exc_info=True)
            emit_agent_trace(
                logger,
                deps.settings,
                agent="intent",
                phase="Lỗi LLM — fallback",
                detail="intent=general_chat",
            )
            return {"intent": "general_chat"}
        normalized = normalize_intent(raw)
        emit_agent_trace(
            logger,
            deps.settings,
            agent="intent",
            phase="Suy luận định tuyến (JSON từ LLM)",
            detail=(
                f"intent={normalized}\n"
                f"raw_model_intent={raw}\n"
                f"câu_hỏi={_user_question_snippet(state)}"
            ),
        )
        return {"intent": normalized}

    return intent


def route_after_intent(state: AgentState) -> str:
    intent = state.get("intent") or "general_chat"
    if intent == "system_data_query":
        return "sql_branch"
    return "chat_normal"
