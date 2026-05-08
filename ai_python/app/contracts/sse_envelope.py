"""Design-aligned SSE payloads (SRS §10)."""

from typing import Any, Literal

from pydantic import BaseModel, field_validator


class TokenPayload(BaseModel):
    delta: str


class ToolCallPayload(BaseModel):
    name: str
    args: dict[str, Any]
    status: str = "started"


class ToolResultPayload(BaseModel):
    name: str
    ok: bool
    summary: str


class ErrorPayload(BaseModel):
    message: str
    code: str


class UsagePayload(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


class DonePayload(BaseModel):
    usage: UsagePayload


SseEventName = Literal["token", "tool_call", "tool_result", "ui", "error", "done"]


class SseEnvelope(BaseModel):
    event: SseEventName
    payload: dict[str, Any]

    @field_validator("event")
    @classmethod
    def known_events(cls, v: str) -> str:
        allowed = {"token", "tool_call", "tool_result", "ui", "error", "done"}
        if v not in allowed:
            raise ValueError(f"Unsupported SSE event: {v}")
        return v

    def to_wire_json(self) -> str:
        return self.model_dump_json(exclude_none=True)


def sse_error_message_for_mcp(code: str, fallback: str) -> str:
    """User-safe synopsis for SSE error payloads (SRS AC-4)."""
    canned: dict[str, str] = {
        "DB_QUERY_REJECTED": "Truy vấn read-only không được áp dụng với tham số này.",
        "DB_TIMEOUT": "Đã hết thời gian chờ truy vấn đọc. Thử lại sau.",
        "DB_UPSTREAM_ERROR": "Đọc ERP tạm thời không khả dụng.",
        "RAG_TIMEOUT": "Tìm kiến thức mất quá lâu. Thử lại sau.",
        "RAG_BAD_FILTER": "Bộ lọc RAG không hợp lệ.",
        "RAG_UPSTREAM_ERROR": "Dịch vụ tra cứu tri thức tạm thời lỗi.",
    }
    return canned.get(code, fallback)


def map_guard_refusal(code: str) -> str:
    if code == "POLICY_EMPTY":
        return "Vui lòng nhập một câu hỏi cụ thể hơn."
    if code == "POLICY_REFUSE_WRITE":
        return "Tôi không thể chạy thao tác ghi (INSERT/UPDATE/DELETE). Slice này chỉ đọc/tra cứu."
    if code == "POLICY_REFUSE_SECRET":
        return (
            "Tôi không thể chia sẻ chuỗi kết nối hay thông tin bí mật. "
            "Hãy dùng công cụ quản trị vault an toàn."
        )
    if code == "POLICY_AMBIGUOUS":
        return (
            "Bạn có thể làm rõ bạn đang hỏi doanh thu theo SKU hay theo đơn hàng "
            "(hoặc mục báo cáo khác)?"
        )
    return "Yêu cầu này nằm ngoài phạm vi read-only của trợ lý."
