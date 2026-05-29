"""Fake LlmClient for offline tests."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FakeLlmClient:
    """Deterministic stub implementing :class:`app.llm.protocol.LlmClient`."""

    def __init__(
        self,
        *,
        reply: str = "ok",
        stream_parts: list[str] | None = None,
        intent: str | None = None,
        planner_strategy: str | None = None,
        planner_intent: str | None = None,
        planner_confidence: float = 0.0,
        sql_review_failures: int = 0,
        table_pick: list[str] | None = None,
    ) -> None:
        self._reply = reply
        self._stream_parts = stream_parts or ["hel", "lo"]
        self._intent = intent
        self._planner_strategy = planner_strategy
        self._planner_intent = planner_intent
        self._planner_confidence = planner_confidence
        self._sql_review_fail_left = sql_review_failures
        self._table_pick = table_pick
        self.invoke_count = 0
        self.last_invoke_text: str | None = None

    def invoke_text(self, user: str, *, system: str | None = None) -> str:
        self.invoke_count += 1
        self.last_invoke_text = user
        return self._reply

    def stream_text(self, user: str, *, system: str | None = None) -> Iterator[str]:
        yield from self._stream_parts

    def structured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
        json_output_contract: str | None = None,
    ) -> T:
        if schema.__name__ == "IntentOutput":
            intent_val = self._intent if self._intent is not None else "general_chat"
            return schema.model_validate({"intent": intent_val})  # type: ignore[return-value]
        if schema.__name__ == "AgentPlannerOutput":
            strategy = self._planner_strategy or "defer_to_intent"
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "strategy": strategy,
                    "intent": self._planner_intent,
                    "reason": "fake planner",
                    "confidence": self._planner_confidence,
                    "need_clarification": False,
                },
            )
        if schema.__name__ == "IdeaPlannerOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "data_request": {
                        "entity": "orders",
                        "metric": "count",
                        "expected_result_shape": "single_kpi",
                    },
                    "chart_idea": {"chart_type": "bar", "title_hint": "Thống kê"},
                },
            )
        if schema.__name__ == "ChartReadinessOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {"ok": True, "issues": [], "retry_hint": "", "warnings": []},
            )
        if schema.__name__ == "ChartSpecDraftOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {"chart_type": "bar", "x_key": "_stub", "y_key": "sql_ok", "title": "Test chart"},
            )
        if schema.__name__ == "ChartReviewOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "chart_type": "bar",
                    "x_key": "_stub",
                    "y_key": "sql_ok",
                    "title": "Test chart",
                    "final_answer": "Biểu đồ từ dữ liệu stub.",
                },
            )
        if schema.__name__ == "SqlReviewOutput":
            if self._sql_review_fail_left > 0:
                self._sql_review_fail_left -= 1
                return schema.model_validate(  # type: ignore[return-value]
                    {
                        "ok": False,
                        "issues": ["forced fail"],
                        "retry_hint": "Use allowlisted tables only; add LIMIT.",
                        "suggested_tables": [],
                    }
                )
            return schema.model_validate({"ok": True, "issues": []})  # type: ignore[return-value]
        if schema.__name__ == "SqlTablePickOutput":
            picks = self._table_pick if self._table_pick else ["customers"]
            return schema.model_validate({"tables": picks})  # type: ignore[return-value]
        if schema.__name__ == "SchemaPlanOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "metric_id": "ledger_revenue",
                    "tables": ["financeledger"],
                    "dimensions": [],
                    "ambiguity_note": None,
                },
            )
        if schema.__name__ == "CatalogEntityPickOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {"entity_type": "product", "row_count_hint": 2},
            )
        if schema.__name__ == "CatalogDraftGenerateOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "columns": [
                        {"key": "skuCode", "label": "Mã SKU", "type": "string", "required": True},
                        {"key": "name", "label": "Tên", "type": "string", "required": True},
                    ],
                    "rows": [
                        {
                            "rowId": "r1",
                            "values": {
                                "skuCode": "T-1",
                                "name": "Test",
                                "baseUnitName": "Cái",
                                "costPrice": 10000,
                                "salePrice": 15000,
                            },
                        },
                    ],
                },
            )
        raise NotImplementedError(schema)
