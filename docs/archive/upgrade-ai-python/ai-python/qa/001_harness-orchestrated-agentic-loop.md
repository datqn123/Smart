# QA Spec 001 (upgrade/ai-python): Harness-Orchestrated Agentic Loop

- **SRS ref**: `docs/upgrade/ai-python/srs/002_harness-orchestrated-agentic-loop.md`
- **Tech Spec ref**: `docs/upgrade/ai-python/tech_lead/001_harness-orchestrated-agentic-loop.md`
- **Stage**: QA_SPEC_WRITER
- **Date**: 2026-06-07
- **Readiness**: QA_READY_FOR_CODING

---

## 1. Phạm vi QA

| Layer | Phạm vi |
| :-- | :-- |
| Unit | `HarnessPolicy`, `TurnScratchpad`, `ToolRegistry`, `DecisionSchema`, `fresh_turn_overlay`, tool adapters (mock subgraph) |
| Integration | `HarnessOrchestrator` end-to-end với stub tools, `LangHarnessRuntime` Strangler routing |
| Regression | Graph tuyến tính giữ nguyên hành vi khi `harness_loop_enabled=False`; SSE contract không đổi |
| Không trong phạm vi | Spring backend, FPT model thật (dùng stub LLM trong tests) |

---

## 2. Test fixtures chung

```python
# tests/conftest.py (thêm vào)
from app.harness.tool_registry import TurnContext, ToolResult

@pytest.fixture
def ctx():
    return TurnContext(
        tenant_id="t1", user_id="u1", thread_id="thread-1",
        correlation_id="corr-1", bearer_token=None, schema_version=None,
    )

@pytest.fixture
def stub_tool_ok():
    """Tool luôn thành công sau 1 bước, trả final_answer."""
    class OkTool:
        async def invoke(self, args, ctx): return ToolResult(
            ok=True, output={}, observation_text="done", sse_payload=None)
    return OkTool()

@pytest.fixture
def stub_tool_hitl():
    """Tool trả pending_hitl."""
    class HitlTool:
        async def invoke(self, args, ctx):
            from app.harness.tool_registry import HitlSpec
            return ToolResult(
                ok=True, output={}, observation_text="draft ready",
                sse_payload={"entity": "product"},
                pending_hitl=HitlSpec(event_name="draft", payload={"entity": "product"}, resume_token="thread-1"),
            )
    return HitlTool()

@pytest.fixture
def stub_llm_final(monkeypatch):
    """LLM luôn quyết định final_answer ngay bước đầu."""
    ...

@pytest.fixture
def stub_llm_tool_then_final(monkeypatch):
    """Bước 1: call_tool 'sql_query'. Bước 2: final_answer."""
    ...
```

---

## 3. P0 Tests — phải pass trước khi merge

### P0-01: Guard chặn SQL ghi

```python
# tests/test_harness_policy.py
def test_policy_blocks_delete_sql():
    from app.harness.policy import HarnessPolicy, HarnessPolicyError
    policy = HarnessPolicy()
    with pytest.raises(HarnessPolicyError, match="delete"):
        policy.check("sql_query", {"sql": "DELETE FROM orders WHERE 1=1"})

def test_policy_blocks_update_sql():
    policy = HarnessPolicy()
    with pytest.raises(HarnessPolicyError, match="update"):
        policy.check("sql_query", {"sql": "UPDATE products SET price=0"})

def test_policy_blocks_drop_sql():
    policy = HarnessPolicy()
    with pytest.raises(HarnessPolicyError, match="drop"):
        policy.check("sql_query", {"sql": "DROP TABLE cash_transactions"})

def test_policy_allows_select():
    policy = HarnessPolicy()
    policy.check("sql_query", {"sql": "SELECT id, name FROM products LIMIT 10"})  # không raise

def test_policy_unknown_tool_does_not_raise():
    policy = HarnessPolicy()
    policy.check("unknown_tool", {})  # không raise; unknown = không có capability DATA_READ
```

### P0-02: Loop dừng khi chạm `max_steps`

```python
# tests/test_harness_orchestrator.py
@pytest.mark.asyncio
async def test_loop_stops_at_max_steps(ctx):
    """LLM không bao giờ trả final_answer → loop phải dừng sau max_steps."""
    # LLM stub: luôn trả call_tool "sql_query"
    # Tool stub: luôn trả ok=True nhưng không final_answer
    events = [e async for e in orchestrator.run(scratchpad, ctx)]
    final = [e for e in events if isinstance(e, FinalAnswerEvent)]
    assert len(final) == 1   # best-effort phát 1 lần
    # xác nhận số step không vượt max_steps=6
    progress = [e for e in events if isinstance(e, ProgressEvent)]
    assert len(progress) <= 6
```

### P0-03: HITL dừng loop và phát đúng SSE event

```python
@pytest.mark.asyncio
async def test_hitl_stops_loop_and_emits_draft(ctx, stub_tool_hitl):
    """CatalogDraftTool trả pending_hitl → loop dừng, phát SsePayloadEvent("draft", ...)."""
    ...
    sse_events = [e for e in events if isinstance(e, SsePayloadEvent) and e.event_name == "draft"]
    assert len(sse_events) == 1
    assert sse_events[0].payload == {"entity": "product"}
    hitl_events = [e for e in events if isinstance(e, PendingHitlEvent)]
    assert len(hitl_events) == 1
    # Không có FinalAnswerEvent sau HITL
    assert not any(isinstance(e, FinalAnswerEvent) for e in events)
```

### P0-04: Strangler fallback — tắt cờ → graph tuyến tính

```python
# tests/test_runtime_strangler.py
@pytest.mark.asyncio
async def test_strangler_off_uses_legacy_graph(monkeypatch):
    """harness_loop_enabled=False → legacy graph chạy, không khởi tạo orchestrator."""
    monkeypatch.setenv("HARNESS_LOOP_ENABLED", "false")
    runtime = build_test_runtime()
    # gọi stream, xác nhận không có ProgressEvent từ orchestrator
    events = [...]
    assert not any("Bước" in getattr(e, "text", "") for e in events)
```

### P0-05: `fresh_turn_overlay` xóa đúng tất cả transient keys

```python
# tests/test_state_fresh_turn.py
def test_fresh_turn_overlay_covers_all_transient_keys():
    from app.graph.state import fresh_turn_overlay, _TRANSIENT_KEYS, AgentState
    overlay = fresh_turn_overlay()
    assert set(overlay.keys()) == _TRANSIENT_KEYS
    # Mọi giá trị là None
    assert all(v is None for v in overlay.values())

def test_fresh_turn_overlay_does_not_contain_persistent_keys():
    from app.graph.state import fresh_turn_overlay
    overlay = fresh_turn_overlay()
    persistent = {"messages", "conversation_summary", "context_compact_generation",
                  "business_scope", "last_business_scope", "last_data_answer"}
    assert not any(k in overlay for k in persistent)
```

### P0-06: Policy không tương tác với `sql_safety` — defense-in-depth

```python
def test_sql_safety_still_blocks_even_if_policy_passes():
    """sql_safety.enforce_read_only_sql độc lập với HarnessPolicy — không bị tắt."""
    from app.graph.sql_safety import enforce_read_only_sql
    with pytest.raises(Exception):
        enforce_read_only_sql("DELETE FROM products")
```

---

## 4. P1 Tests — phải pass trước release

### P1-01: `TurnScratchpad.add_observation` cắt bớt observation dài

```python
def test_scratchpad_truncates_long_observation():
    from app.harness.scratchpad import TurnScratchpad, Observation
    scratchpad = TurnScratchpad(messages=[])
    long_text = "x" * 1000
    result = ToolResult(ok=True, output={}, observation_text=long_text)
    scratchpad.add_observation(result, "sql_query")
    obs = scratchpad.observations[-1]
    assert len(obs.observation_text) <= 803   # 800 + "[truncated]"
    assert obs.observation_text.endswith("[truncated]")
```

### P1-02: `TurnScratchpad.to_decision_prompt` chứa tools manifest

```python
def test_scratchpad_decision_prompt_contains_manifest():
    scratchpad = TurnScratchpad(messages=[HumanMessage("cho tôi xem doanh thu")])
    manifest_text = "sql_query: truy vấn dữ liệu ERP"
    messages = scratchpad.to_decision_prompt(manifest_text)
    content = " ".join(str(m.content) for m in messages)
    assert "sql_query" in content
    assert "truy vấn dữ liệu ERP" in content
```

### P1-03: `ToolRegistry.get_impl` raise khi tool không tồn tại

```python
def test_registry_raises_on_unknown_tool():
    from app.harness.tool_registry import ToolRegistry
    registry = ToolRegistry()
    with pytest.raises(KeyError, match="nonexistent_tool"):
        registry.get_impl("nonexistent_tool")
```

### P1-04: Chuỗi 2 tools tự nhiên (schema_explore → sql_query)

```python
@pytest.mark.asyncio
async def test_two_tool_chain(ctx):
    """LLM step 1: call schema_explore. Step 2: call sql_query. Step 3: final_answer."""
    # stub_llm: bước 0 → schema_explore, bước 1 → sql_query, bước 2 → final_answer "doanh thu là 100"
    events = [e async for e in orchestrator.run(scratchpad, ctx)]
    finals = [e for e in events if isinstance(e, FinalAnswerEvent)]
    assert len(finals) == 1
    assert "doanh thu là 100" in finals[0].text
    # xác nhận 2 observation được ghi
    assert len(scratchpad.observations) == 2
    assert scratchpad.observations[0].tool_name == "schema_explore"
    assert scratchpad.observations[1].tool_name == "sql_query"
```

### P1-05: `SqlQueryTool` forward đúng `tenant_id` và `bearer_token` vào state

```python
@pytest.mark.asyncio
async def test_sql_query_tool_forwards_context(ctx, monkeypatch):
    """State gửi vào subgraph phải chứa tenant_id và spring_bearer_token từ ctx."""
    captured_state = {}
    async def fake_ainvoke(state, config):
        captured_state.update(state)
        return {"query_result": {"rows": []}, "result_ok": True}
    monkeypatch.setattr(tool._compiled, "ainvoke", fake_ainvoke)
    await tool.invoke({"query": "tổng doanh thu"}, ctx)
    assert captured_state["tenant_id"] == ctx.tenant_id
    assert captured_state["spring_bearer_token"] == ctx.bearer_token
```

### P1-06: SSE event names không đổi so với legacy — regression

```python
@pytest.mark.asyncio
async def test_sse_event_names_match_legacy_contract():
    """OrchestratorEvent → SSE: progress, delta_full, delta, chart, draft, inventory_draft, data_table, done."""
    from app.api.runtime import event_to_sse_lines
    assert event_to_sse_lines(ProgressEvent("tải schema")) == "event: progress\ndata: tải schema\n\n"
    assert event_to_sse_lines(FinalAnswerEvent("xong")) startswith "event: delta_full\n"
```

### P1-07: Policy cho `catalog_draft` không cần DATA_READ → không kiểm tra SQL

```python
def test_policy_catalog_draft_allows_arbitrary_args():
    policy = HarnessPolicy()
    policy.check("catalog_draft", {"request": "tạo sản phẩm mới DELETE FROM x"})
    # DRAFT_CREATE không có SQL check → không raise
```

### P1-08: `harness_max_steps` nhận từ config, có thể override

```python
def test_max_steps_override(ctx, monkeypatch):
    monkeypatch.setenv("HARNESS_MAX_STEPS", "2")
    settings = load_graph_settings()
    assert settings.harness_max_steps == 2
```

### P1-09: Async LLM client — `astructured_predict` trả đúng `DecisionSchema`

```python
@pytest.mark.asyncio
async def test_astructured_predict_parses_decision_schema(monkeypatch):
    """ainvoke trả JSON hợp lệ → DecisionSchema được parse."""
    raw = '{"action": "final_answer", "final_answer": "xong"}'
    # stub ChatOpenAI.ainvoke trả AIMessage(content=raw)
    ...
    result = await client.astructured_predict(messages, DecisionSchema)
    assert result.action == "final_answer"
    assert result.final_answer == "xong"
```

### P1-10: `SqlQueryTool` reset `sql_attempt_count` về 0 mỗi lần gọi

```python
@pytest.mark.asyncio
async def test_sql_tool_resets_attempt_count(ctx, monkeypatch):
    captured = {}
    async def fake_ainvoke(state, _): captured.update(state); return {"result_ok": True, "query_result": {"rows": []}}
    monkeypatch.setattr(tool._compiled, "ainvoke", fake_ainvoke)
    await tool.invoke({"query": "test"}, ctx)
    assert captured["sql_attempt_count"] == 0
    assert captured["sql_repair_max_attempts"] is not None
```

---

## 5. Unit tests cho `fresh_turn_overlay` (quan trọng — ngăn bleed regression)

```python
# tests/test_state_fresh_turn.py

def test_fresh_turn_does_not_bleed_sql_state():
    """Sau fresh_turn, mọi SQL channel về None — không kế thừa lượt trước."""
    state = {"generated_sql": "SELECT 1", "query_result": {"rows": [1, 2]}, **fresh_turn_overlay()}
    assert state["generated_sql"] is None
    assert state["query_result"] is None

def test_fresh_turn_does_not_bleed_chart_state():
    state = {"chart_spec_final": {"type": "bar"}, **fresh_turn_overlay()}
    assert state["chart_spec_final"] is None

def test_fresh_turn_does_not_bleed_draft_state():
    state = {"catalog_draft_sse": {"entity": "product"}, **fresh_turn_overlay()}
    assert state["catalog_draft_sse"] is None

def test_fresh_turn_preserves_messages():
    """messages và conversation_summary KHÔNG bị xóa."""
    state = {"messages": [HumanMessage("hi")], "conversation_summary": "prev"}
    state.update(fresh_turn_overlay())
    assert state["messages"] == [HumanMessage("hi")]
    assert state["conversation_summary"] == "prev"
```

---

## 6. Regression tests — graph tuyến tính

```python
# tests/test_regression_legacy_graph.py

@pytest.mark.asyncio
async def test_legacy_graph_chat_normal_unchanged(monkeypatch):
    """harness_loop_enabled=False → chat_normal vẫn chạy đúng."""
    monkeypatch.setenv("HARNESS_LOOP_ENABLED", "false")
    ...

@pytest.mark.asyncio
async def test_legacy_graph_sql_branch_unchanged(monkeypatch):
    """harness_loop_enabled=False → sql_branch vẫn chạy như trước."""
    ...

@pytest.mark.asyncio
async def test_legacy_graph_catalog_draft_hitl_unchanged(monkeypatch):
    """harness_loop_enabled=False → catalog_draft SSE vẫn phát đúng."""
    ...
```

---

## 7. Failure mode matrix

| Failure | Expected behavior | Test |
| :-- | :-- | :-- |
| LLM trả JSON không parse được `DecisionSchema` | Retry 1 lần (từ `structured_invoke` max_retries=3); nếu vẫn lỗi → `ErrorEvent` → SSE `error` | P1-09 |
| Tool raise exception | `ToolResult(ok=False, error_message=...)` → observation ghi lỗi → LLM tiếp tục quyết định | P0-02 implicit |
| Policy block | `HarnessPolicyError` → loop dừng → SSE `error` ngay (không retry) | P0-01 |
| `max_steps` chạm trần | `FinalAnswerEvent(observation_summary())` → SSE `delta_full` → SSE `done` | P0-02 |
| HITL trigger | Loop dừng, SSE `draft`/`inventory_draft`, SSE `done` **không** phát (FE chờ resume) | P0-03 |
| Async LLM timeout | `asyncio.TimeoutError` → wrap → `ErrorEvent` | P1-09 (extend) |
| `harness_loop_enabled=False` với intent data-query | Fallback graph tuyến tính, kết quả giống legacy | P0-04, regression |

---

## 8. Test execution checklist

- [ ] P0-01 đến P0-06 đều pass (gate để bắt đầu merge bất kỳ slice nào)
- [ ] P1-01 đến P1-10 pass trước release Strangler
- [ ] 4 regression tests pass với cờ OFF
- [ ] `fresh_turn_overlay` unit tests pass (5 tests)
- [ ] `pytest tests/ -k "harness or fresh_turn or strangler or regression_legacy"` xanh
- [ ] Không có blocking call trong event loop (đo bằng `asyncio.get_event_loop().is_running()` + profiling nếu cần)

---

> **Readiness**: QA_READY_FOR_CODING — 6 P0 tests, 10 P1 tests, 4 regression tests, 5 unit fresh_turn, failure matrix đầy đủ.
