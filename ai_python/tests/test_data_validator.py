from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_validator_negative_value_fails() -> None:
    from app.graph.tools.data_validator import DataValidatorTool

    result = await DataValidatorTool().invoke(
        {"rows": [{"revenue": -1}], "required_data": ["revenue"]},
        _ctx(),
    )

    assert result.ok is False
    assert result.output["severity"] == "fail"
    assert "negative_value" in result.output["issues"]


@pytest.mark.asyncio
async def test_validator_missing_column_fails() -> None:
    from app.graph.tools.data_validator import DataValidatorTool

    result = await DataValidatorTool().invoke(
        {"rows": [{"amount": 100}], "required_data": ["revenue"]},
        _ctx(),
    )

    assert result.ok is False
    assert "missing_column:revenue" in result.output["issues"]


@pytest.mark.asyncio
async def test_validator_pass_routes_to_composer() -> None:
    from app.graph.tools.data_validator import DataValidatorTool

    result = await DataValidatorTool().invoke(
        {"rows": [{"revenue": 100}], "required_data": ["revenue"]},
        _ctx(),
    )

    assert result.ok is True
    assert result.output["severity"] == "info"


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
