"""Slice B — observation contract (SRS-006 FR-12, QA TC-B-001/004/006)."""

from __future__ import annotations

from app.harness.observation import ObservationEnvelope, build_observation
from app.harness.result_store import InMemoryResultRefStore
from app.harness.tool_registry import ToolResult, TurnContext


def _ctx(tenant_id: str | None = "t1") -> TurnContext:
    return TurnContext(
        tenant_id=tenant_id,
        user_id="u1",
        thread_id="th1",
        correlation_id="cid",
        bearer_token=None,
        schema_version=None,
    )


# --- TC-B-001: large result -> safe bounded observation -------------------

def test_large_result_truncated_masked_no_full_rows():
    rows = [{"id": i, "phone": f"090000{i:04d}", "name": f"sp{i}"} for i in range(100)]
    result = ToolResult(ok=True, output={"rows": rows}, observation_text="ok")
    store = InMemoryResultRefStore()

    obs = build_observation(
        tool_name="sql_query", tool_result=result, ctx=_ctx(), result_store=store
    )

    assert obs.row_count == 100
    assert len(obs.sample_rows) <= 20
    assert obs.truncated is True
    assert obs.masked is True
    # phone column masked
    assert all(r["phone"] == "***" for r in obs.sample_rows)
    # no full row set leaked — sample is strictly smaller than 100
    assert len(obs.sample_rows) < 100
    # full data is behind an opaque handle, resolvable only via the store
    assert obs.result_ref is not None
    resolved = store.get(obs.result_ref, ctx=_ctx())
    assert len(resolved.data["rows"]) == 100


# --- TC-B-004 surface: planner text has handle + counts, not row 21 -------

def test_planner_text_has_handle_not_full_rows():
    rows = [{"id": i, "v": i * 10} for i in range(30)]
    result = ToolResult(ok=True, output={"rows": rows}, observation_text="ok")
    store = InMemoryResultRefStore()
    obs = build_observation(
        tool_name="sql_query", tool_result=result, ctx=_ctx(), result_store=store
    )
    text = obs.to_planner_text()
    assert "row_count=30" in text
    assert obs.result_ref in text
    # row index 21 (value 210) must not appear in the planner-facing text
    assert '"v": 210' not in text and "210" not in text


def test_query_result_nested_rows_supported():
    rows = [{"id": 1}, {"id": 2}]
    result = ToolResult(ok=True, output={"query_result": {"rows": rows}}, observation_text="")
    obs = build_observation(tool_name="sql_query", tool_result=result, ctx=_ctx())
    assert obs.row_count == 2


def test_small_result_not_truncated():
    rows = [{"id": 1}, {"id": 2}]
    result = ToolResult(ok=True, output={"rows": rows}, observation_text="")
    obs = build_observation(tool_name="sql_query", tool_result=result, ctx=_ctx())
    assert obs.truncated is False
    assert obs.masked is False
    assert obs.row_count == 2


def test_non_tabular_result_is_text_observation():
    result = ToolResult(ok=True, output={"answer_markdown": "Xin chào"}, observation_text="Xin chào")
    obs = build_observation(tool_name="answer_composer", tool_result=result, ctx=_ctx())
    assert obs.ok is True
    assert obs.row_count is None
    assert "Xin chào" in obs.message


# --- TC-B-006: raw SQL / stack sanitized ----------------------------------

def test_error_sanitizes_raw_sql_and_stack():
    raw = (
        "psycopg2 error running SELECT * FROM financeledger WHERE x=1\n"
        'Traceback (most recent call last):\n  File "x.py", line 42, in run'
    )
    result = ToolResult(ok=False, output={}, observation_text="", error_message=raw)
    obs = build_observation(tool_name="sql_query", tool_result=result, ctx=_ctx())

    assert obs.ok is False
    assert obs.replan_required is True
    assert obs.error_kind in {"tool_error", "policy_blocked", "timeout"}
    # no raw SQL or stack content leaked
    assert "financeledger" not in obs.message
    assert "SELECT" not in obs.message.upper()
    assert "Traceback" not in obs.message
    assert "x.py" not in obs.message
    # fingerprint present for dedup, but opaque
    assert obs.failure_fingerprint
    assert "financeledger" not in obs.failure_fingerprint


def test_failure_fingerprint_is_stable_and_dedupable():
    raw = "boom on SELECT * FROM t"
    r1 = ToolResult(ok=False, output={}, observation_text="", error_message=raw)
    r2 = ToolResult(ok=False, output={}, observation_text="", error_message=raw)
    o1 = build_observation(tool_name="sql_query", tool_result=r1, ctx=_ctx())
    o2 = build_observation(tool_name="sql_query", tool_result=r2, ctx=_ctx())
    assert o1.failure_fingerprint == o2.failure_fingerprint


def test_envelope_is_pydantic_serializable():
    obs = ObservationEnvelope(tool_name="t", ok=True, row_count=0)
    dumped = obs.model_dump()
    assert dumped["tool_name"] == "t"
    assert dumped["ok"] is True
