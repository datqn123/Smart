from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_composer_has_followups() -> None:
    from app.graph.tools.answer_composer import AnswerComposerTool

    result = await AnswerComposerTool().invoke(
        {"observations": [{"rows": [{"revenue": 1000000}]}], "assumptions": []},
        _ctx(),
    )

    assert result.ok is True
    assert 1 <= len(result.output["follow_ups"]) <= 3
    assert "Bạn có muốn" in result.observation_text


@pytest.mark.asyncio
async def test_composer_states_assumptions() -> None:
    from app.graph.tools.answer_composer import AnswerComposerTool

    result = await AnswerComposerTool().invoke(
        {"observations": [{"rows": [{"revenue": 1000000}]}], "assumptions": ["Giả định tháng này."]},
        _ctx(),
    )

    assert "Giả định tháng này" in result.observation_text


@pytest.mark.asyncio
async def test_composer_empty_rows_guidance() -> None:
    from app.graph.tools.answer_composer import AnswerComposerTool

    result = await AnswerComposerTool().invoke({"observations": [{"rows": []}], "assumptions": []}, _ctx())

    assert "không tìm thấy dữ liệu" in result.observation_text.lower()
    assert "ví dụ" in result.observation_text.lower()


@pytest.mark.asyncio
async def test_composer_emits_delta_full_sse() -> None:
    from app.graph.tools.answer_composer import AnswerComposerTool

    result = await AnswerComposerTool().invoke(
        {"observations": [{"rows": [{"revenue": 1000000}]}], "assumptions": []},
        _ctx(),
    )

    assert result.sse_payload is not None
    assert result.sse_payload["_event"] == "delta_full"


@pytest.mark.asyncio
async def test_chart_type_by_shape() -> None:
    from app.graph.tools.build_chart import BuildChartTool

    result = await BuildChartTool().invoke(
        {"rows": [{"month": "2026-01", "revenue": 100}, {"month": "2026-02", "revenue": 120}]},
        _ctx(),
    )

    assert result.ok is True
    assert result.output["chartType"] == "line"


@pytest.mark.asyncio
async def test_erp_guide_tool_returns_observation() -> None:
    from app.graph.tools.erp_guide import ErpGuideTool

    result = await ErpGuideTool().invoke({"topic": "inventory"}, _ctx())

    assert result.ok is True
    assert result.observation_text


def _ctx():
    from app.harness.tool_registry import TurnContext

    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version=None,
    )
