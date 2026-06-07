from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage


def test_scratchpad_truncates_long_observation() -> None:
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolResult

    scratchpad = TurnScratchpad(messages=[])
    result = ToolResult(ok=True, output={}, observation_text="x" * 1000)

    scratchpad.add_observation(result, "sql_query")

    obs = scratchpad.observations[-1]
    assert len(obs.observation_text) <= 811
    assert obs.observation_text.endswith("[truncated]")


def test_scratchpad_decision_prompt_contains_manifest() -> None:
    from app.harness.scratchpad import TurnScratchpad

    scratchpad = TurnScratchpad(messages=[HumanMessage(content="cho tôi xem doanh thu")])
    messages = scratchpad.to_decision_prompt("sql_query: truy vấn dữ liệu ERP")
    content = " ".join(str(msg.content) for msg in messages)

    assert "sql_query" in content
    assert "truy vấn dữ liệu ERP" in content


def test_registry_raises_on_unknown_tool() -> None:
    from app.harness.tool_registry import ToolRegistry

    registry = ToolRegistry()

    with pytest.raises(KeyError, match="nonexistent_tool"):
        registry.get_impl("nonexistent_tool")
