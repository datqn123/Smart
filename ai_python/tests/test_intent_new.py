"""Tests for new intent recognition (IntentDecision + IntentClassifier)."""

import pytest
from unittest.mock import AsyncMock
from app.harness.intent import IntentDecision, IntentClassifier


class TestIntentDecision:
    def test_direct_answer(self):
        d = IntentDecision(
            action="direct_answer",
            goal_text="",
            answer="Xin chào! Tôi có thể giúp gì cho bạn?",
            reasoning="User is greeting",
        )
        assert d.action == "direct_answer"
        assert d.tool_name is None
        assert d.answer == "Xin chào! Tôi có thể giúp gì cho bạn?"

    def test_call_tool(self):
        d = IntentDecision(
            action="call_tool",
            goal_text="User muốn xem doanh thu theo tháng",
            tool_name="sql_query",
            tool_args={"query": "SELECT ..."},
            reasoning="User wants revenue report",
        )
        assert d.action == "call_tool"
        assert d.tool_name == "sql_query"
        assert d.tool_args == {"query": "SELECT ..."}

    def test_final_answer(self):
        d = IntentDecision(
            action="final_answer",
            goal_text="User muốn xem doanh thu",
            answer="Doanh thu Q1 là 1 tỷ VNĐ",
            reasoning="Data gathered, composing answer",
        )
        assert d.action == "final_answer"
        assert d.answer == "Doanh thu Q1 là 1 tỷ VNĐ"

    def test_clarify(self):
        d = IntentDecision(
            action="clarify",
            goal_text="User muốn tạo sản phẩm",
            clarify_questions=["Bạn muốn tạo sản phẩm nào?"],
            reasoning="Missing product name",
        )
        assert d.action == "clarify"
        assert len(d.clarify_questions) == 1

    def test_validation_rejects_invalid_action(self):
        with pytest.raises(Exception):
            IntentDecision(action="invalid", goal_text="test")


class TestIntentClassifier:
    @pytest.mark.asyncio
    async def test_classify_direct_answer(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=IntentDecision(
            action="direct_answer",
            goal_text="",
            answer="Xin chào!",
            reasoning="Greeting",
        ))
        classifier = IntentClassifier(llm_client=mock_llm, skill_path="nonexistent_skill.md")
        result = await classifier.classify(
            question="Xin chào",
            context={"schema_text": "", "system_info": ""},
        )
        assert result.action == "direct_answer"
        assert result.answer == "Xin chào!"

    @pytest.mark.asyncio
    async def test_classify_call_tool(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=IntentDecision(
            action="call_tool",
            goal_text="Xem doanh thu Q1",
            tool_name="sql_query",
            tool_args={"query": "SELECT * FROM revenue"},
            reasoning="Revenue query",
        ))
        classifier = IntentClassifier(llm_client=mock_llm, skill_path="nonexistent_skill.md")
        result = await classifier.classify(
            question="Cho tôi xem doanh thu Q1",
            context={"schema_text": "revenue table...", "system_info": "ERP"},
        )
        assert result.action == "call_tool"
        assert result.tool_name == "sql_query"