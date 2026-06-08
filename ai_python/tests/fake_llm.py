"""Fake LlmClient for offline tests."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from app.llm.openai_compatible import InvokeUsage

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
        intent_confidence: float = 0.95,
        intent_missing: list[str] | None = None,
        intent_entity_score: float = 0.95,
        intent_mode: str = "run",
        sql_review_failures: int = 0,
        table_pick: list[str] | None = None,
        plan_nodes: list[dict] | None = None,
        compose_followups: int = 2,
    ) -> None:
        self._reply = reply
        self._stream_parts = stream_parts or ["hel", "lo"]
        self._intent = intent
        self._planner_strategy = planner_strategy
        self._planner_intent = planner_intent
        self._planner_confidence = planner_confidence
        self._intent_confidence = intent_confidence
        self._intent_missing = intent_missing or []
        self._intent_entity_score = intent_entity_score
        self._intent_mode = intent_mode
        self._sql_review_fail_left = sql_review_failures
        self._table_pick = table_pick
        self._plan_nodes = plan_nodes
        self._compose_followups = compose_followups
        self.invoke_count = 0
        self.last_invoke_text: str | None = None
        self.last_usage = InvokeUsage(prompt_tokens=50, completion_tokens=50, cost_usd=0.001)

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
        if schema.__name__ == "IntentAnalysisResult":
            intent_val = self._intent if self._intent is not None else "data_query"
            # Derive mode from intent state
            if self._intent_missing:
                mode = "clarify"
                clarify_questions = ["Bạn muốn xem trong khoảng thời gian nào?"]
            elif self._intent_entity_score < 0.6:
                mode = "clarify"
                clarify_questions = ["Bạn muốn dùng chính xác đối tượng nào?"]
            elif self._intent_confidence < 0.9:
                mode = "auto_assume"
                clarify_questions = []
            else:
                mode = self._intent_mode
                clarify_questions = []
            required = [
                {"field": "revenue", "source": "orders", "required": True, "resolved": not bool(self._intent_missing)}
            ]
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "goal": "fake goal",
                    "intent_type": intent_val,
                    "required_data": required,
                    "resolved_entities": [
                        {"raw": "x", "matched": "y", "score": self._intent_entity_score}
                    ],
                    "confidence": self._intent_confidence,
                    "ambiguities": [],
                    "mode": mode,
                    "clarify_questions": clarify_questions,
                    "assumptions": [],
                    "reasoning": "fake reasoning",
                    "schema_refs": ["orders"],
                    "missing_required": self._intent_missing,
                }
            )
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
        if schema.__name__ == "PlanGraphOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "nodes": self._plan_nodes
                    or [
                        {
                            "id": "n1",
                            "tool": "sql_query",
                            "needs": [],
                            "input_spec": {"query": "revenue"},
                            "output_expect": "rows",
                        },
                        {
                            "id": "n2",
                            "tool": "sql_query",
                            "needs": [],
                            "input_spec": {"query": "inventory"},
                            "output_expect": "rows",
                        },
                    ]
                }
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
        if schema.__name__ == "AnswerComposerOutput":
            return schema.model_validate(  # type: ignore[return-value]
                {
                    "answer_markdown": "Doanh thu: 100đ",
                    "assumptions": [],
                    "follow_ups": [
                        "Xem theo tuần?",
                        "So với tháng trước?",
                        "Xem theo sản phẩm?",
                    ][: self._compose_followups],
                }
            )
        raise NotImplementedError(schema)

    async def astructured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
        json_output_contract: str | None = None,
    ) -> T:
        return self.structured_predict(
            messages,
            schema,
            max_retries=max_retries,
            json_output_contract=json_output_contract,
        )
