"""sql_review skip/retry optimizations."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.config.graph_settings import GraphSettings
from app.graph.deps import GraphDeps
from app.graph.nodes.sql_pipeline import make_sql_review_node
from app.graph.sql_executor import StubSqlExecutor
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


class _SqlReviewProbe(FakeLlmClient):
    def __init__(self) -> None:
        super().__init__()
        self.sql_review_calls = 0
        self.last_max_retries = None

    def structured_predict(self, messages, schema, *, max_retries=3, json_output_contract=None):  # type: ignore[no-untyped-def]
        if schema.__name__ == "SqlReviewOutput":
            self.sql_review_calls += 1
            self.last_max_retries = max_retries
        return super().structured_predict(
            messages,
            schema,
            max_retries=max_retries,
            json_output_contract=json_output_contract,
        )


def _deps(settings: GraphSettings, probe: _SqlReviewProbe) -> GraphDeps:
    reg = LlmRegistry()
    reg.register("default", probe)
    reg.register("sql_review", probe)
    return GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=settings,
    )


def test_sql_review_skips_low_risk_query_mode() -> None:
    probe = _SqlReviewProbe()
    node = make_sql_review_node(_deps(GraphSettings(sql_review_skip_low_risk=True), probe))
    out = node(
        {
            "intent": "system_data_query",
            "generated_sql": "SELECT id FROM customers LIMIT 10",
            "messages": [HumanMessage(content="liệt kê mã khách hàng")],
        }
    )
    assert out["sql_review_ok"] is True
    assert probe.sql_review_calls == 0


def test_sql_review_calls_llm_for_non_generic_domain() -> None:
    probe = _SqlReviewProbe()
    node = make_sql_review_node(
        _deps(
            GraphSettings(sql_review_skip_low_risk=True, sql_review_max_retries=2),
            probe,
        )
    )
    out = node(
        {
            "intent": "system_data_query",
            "generated_sql": "SELECT SUM(amount) FROM financeledger LIMIT 10",
            "messages": [HumanMessage(content="doanh thu tháng này")],
        }
    )
    assert out["sql_review_ok"] is True
    assert probe.sql_review_calls == 1
    assert probe.last_max_retries == 2
