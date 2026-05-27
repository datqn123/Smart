from __future__ import annotations

from app.api.runtime import _build_state
from app.api.schemas import ChatMetadata, ChatOptions, ChatRequest
from app.config.graph_settings import GraphSettings


def test_build_state_does_not_reset_last_data_answer() -> None:
    req = ChatRequest(
        message="liệt kê đi",
        metadata=ChatMetadata(
            user_id="u1",
            tenant_id="t1",
            thread_id="th1",
            schema_version="v1",
        ),
        options=ChatOptions(interaction_mode="auto"),
    )
    state = _build_state(
        request=req,
        correlation_id="cid-1",
        graph_settings=GraphSettings(),
        bearer_token=None,
    )
    assert "last_data_answer" not in state
