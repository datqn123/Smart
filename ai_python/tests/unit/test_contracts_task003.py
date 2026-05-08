import pytest

from app.contracts import ChatStateTask003, McpToolError


def test_chat_state_requires_slice_intents() -> None:
    with pytest.raises(ValueError):
        ChatStateTask003(user_message="hello", intent="write")  # type: ignore[arg-type]


def test_chat_state_accumulates_chunk_ids_without_dupes() -> None:
    c = ChatStateTask003(user_message="ok")
    c.apply_rag_chunks(chunk_ids=["a", "a", "b"], namespaces=["docs", "docs"])  # type: ignore[arg-type]
    assert c.rag_context_ids == ["a", "b"]
    assert c.rag_namespaces_hit == ["docs"]


def test_mcp_tool_error_model() -> None:
    err = McpToolError(code="DB_TIMEOUT", message="boom", correlation_id="c1")
    assert err.retryable is False
    dumped = err.model_dump()
    assert dumped["correlation_id"] == "c1"
