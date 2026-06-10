# Tech Spec 001 (upgrade/ai-python): Harness-Orchestrated Agentic Loop

- **SRS ref**: `docs/upgrade/ai-python/srs/002_harness-orchestrated-agentic-loop.md`
- **Stage**: TECH_SPEC_WRITER
- **Date**: 2026-06-07
- **Readiness**: READY_FOR_CODING

---

## 0. Owner Decisions còn mở — chốt ở đây

| ID | Quyết định | Lựa chọn | Lý do |
| :-- | :-- | :-- | :-- |
| OD-5 | Decision provider | **JSON-structured qua `structured_invoke`** | Đã có `app/llm/structured.py` + `structured_predict`; tương thích mọi model OpenAI-compatible mà không cần tool-calling native. Phù hợp với stack hiện tại (FPT model). |
| OD-6 | Checkpointer async | **`AsyncSqliteSaver`** (LangGraph built-in) | Không thêm dependency; nếu Postgres cần thì swap provider sau mà không đổi orchestrator. |
| OD-7 | Trần loop | `max_steps=6` mặc định (config). Hành vi khi chạm trần: **best-effort** — phát `final_answer` từ observation cuối cùng + ghi `warn_step_budget` vào audit. |

---

## 1. Kiến trúc tổng thể sau migration

```
app/
├── harness/
│   ├── __init__.py         (export mới: HarnessOrchestrator, ToolRegistry, ...)
│   ├── runtime.py          (giữ AgentHarness KHÔNG ĐỔI — backward compat)
│   ├── orchestrator.py     ← MỚI: vòng lặp agentic async
│   ├── tool_registry.py    ← MỚI: manifest + registration
│   ├── policy.py           ← MỚI: capability guard (thay substring deny)
│   └── scratchpad.py       ← MỚI: working memory per turn
├── graph/
│   ├── tools/              ← MỚI folder: tool adapters
│   │   ├── __init__.py
│   │   ├── sql_query.py    ← wrap sql_subgraph
│   │   ├── schema_explore.py ← wrap schema_explore node
│   │   ├── catalog_draft.py  ← wrap catalog_draft_subgraph (HITL)
│   │   └── inventory_draft.py ← wrap inventory_draft_subgraph (HITL)
│   ├── main_graph.py       (KHÔNG ĐỔI — fallback Strangler)
│   └── state.py            (mở rộng nhẹ: thêm TurnScratchpad alias)
└── api/
    ├── runtime.py          (thêm LangHarnessRuntime + Strangler routing)
    └── routes.py           (KHÔNG ĐỔI SSE contract)
```

---

## 2. Data contracts

### 2.1 `ToolInput`

```python
# app/harness/tool_registry.py
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ToolInput:
    tool_name: str
    args: dict[str, Any]       # validated against tool schema
    context: "TurnContext"     # tenant_id, correlation_id, bearer_token, thread_id
```

### 2.2 `ToolResult`

```python
@dataclass
class ToolResult:
    ok: bool
    output: dict[str, Any]             # raw result từ tool (rows, draft, ...)
    observation_text: str              # text tóm tắt để LLM đọc vào scratchpad
    sse_payload: dict[str, Any] | None = None   # emit ngay nếu có (chart, draft, data_table, ...)
    pending_hitl: "HitlSpec | None" = None      # nếu set → orchestrator dừng loop
    error_message: str | None = None
```

### 2.3 `HitlSpec` (HITL signal)

```python
@dataclass
class HitlSpec:
    event_name: str        # "draft" | "inventory_draft"
    payload: dict          # payload cho SSE
    resume_token: str      # thread_id / checkpoint key để resume lượt sau
```

### 2.4 `DecisionSchema` (LLM "next-action" output)

```python
from pydantic import BaseModel

class ToolCall(BaseModel):
    tool_name: str
    args: dict[str, Any]
    reasoning: str          # không gửi FE; dùng để debug/audit

class DecisionSchema(BaseModel):
    action: Literal["call_tool", "final_answer"]
    tool_call: ToolCall | None = None
    final_answer: str | None = None
```

### 2.5 `TurnContext`

```python
@dataclass(frozen=True)
class TurnContext:
    tenant_id: str | None
    user_id: str | None
    thread_id: str | None
    correlation_id: str
    bearer_token: str | None
    schema_version: str | None
```

### 2.6 `TurnScratchpad`

```python
# app/harness/scratchpad.py
from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage

@dataclass
class Observation:
    tool_name: str
    observation_text: str      # ≤ 800 chars; cắt bớt nếu dài hơn (tránh nổ context)
    ok: bool

@dataclass
class TurnScratchpad:
    messages: list[BaseMessage]    # lịch sử hội thoại (từ checkpointer)
    observations: list[Observation] = field(default_factory=list)
    step: int = 0

    def add_observation(self, result: ToolResult, tool_name: str) -> None: ...
    def to_decision_prompt(self, tools_manifest: str) -> list[BaseMessage]: ...
    def observation_summary(self) -> str: ...
```

**Quy tắc tóm tắt observation**: nếu `observation_text` > 800 chars → cắt ở 800 + thêm `"[truncated]"`. SQL rows > 20 rows → chỉ giữ 5 rows đầu + ghi `"... N rows total"`.

---

## 3. `HarnessPolicy` — capability guard

```python
# app/harness/policy.py

class Capability(str, Enum):
    DATA_READ    = "data_read"     # SQL SELECT, schema read
    DRAFT_CREATE = "draft_create"  # catalog/inventory draft POST to Spring
    CHAT         = "chat"          # text generation, no side-effect

TOOL_CAPABILITIES: dict[str, set[Capability]] = {
    "sql_query":         {Capability.DATA_READ},
    "schema_explore":    {Capability.DATA_READ},
    "catalog_draft":     {Capability.DRAFT_CREATE},
    "inventory_draft":   {Capability.DRAFT_CREATE},
    "chat_normal":       {Capability.CHAT},
}

DENIED_SQL_KEYWORDS = frozenset(["delete", "update", "insert", "drop", "truncate", "alter", "create"])

class HarnessPolicy:
    def check(self, tool_name: str, args: dict) -> None:
        """Raise HarnessPolicyError nếu vi phạm. Gọi trước mọi tool-call."""
        caps = TOOL_CAPABILITIES.get(tool_name, set())
        if Capability.DATA_READ in caps:
            sql = (args.get("sql") or args.get("query") or "").lower()
            for kw in DENIED_SQL_KEYWORDS:
                if kw in sql:
                    raise HarnessPolicyError(f"SQL write keyword blocked: {kw}")
        # có thể mở rộng: tenant whitelist, rate limit per tool, ...
```

**Quan trọng**: `HarnessPolicy.check` **thay thế** phần deny trong `AgentHarness._is_denied_tool` (substring) và bổ sung vào `sql_safety.enforce_read_only_sql`. Hai lớp không xung đột: `policy.py` ở mức orchestrator (trước khi tool chạy), `sql_safety` vẫn ở mức executor (defense in depth).

---

## 4. `ToolRegistry` — manifest

```python
# app/harness/tool_registry.py

@dataclass(frozen=True)
class ToolManifest:
    name: str
    description: str               # LLM đọc để chọn tool
    args_schema: str               # JSON Schema string
    has_hitl: bool = False         # tool có thể trả pending_hitl

class ToolRegistry:
    def register(self, manifest: ToolManifest, impl: "AsyncTool") -> None: ...
    def get_impl(self, name: str) -> "AsyncTool": ...
    def tools_manifest_text(self) -> str:
        """Format danh sách tool thành text cho prompt LLM decision."""
        ...

# Protocol
class AsyncTool(Protocol):
    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult: ...
```

---

## 5. `HarnessOrchestrator` — vòng lặp agentic

```python
# app/harness/orchestrator.py

class HarnessOrchestrator:
    def __init__(
        self,
        *,
        llm_registry: LlmRegistry,
        tool_registry: ToolRegistry,
        policy: HarnessPolicy,
        settings: GraphSettings,
        harness: AgentHarness,        # giữ audit/lifecycle hooks
    ) -> None: ...

    async def run(
        self,
        scratchpad: TurnScratchpad,
        ctx: TurnContext,
    ) -> AsyncIterator[OrchestratorEvent]:
        """
        Phát OrchestratorEvent (progress | sse_payload | final_answer | error).
        Caller (api/runtime.py) dịch sang SSE.
        """
        max_steps = self._settings.harness_max_steps   # default 6
        for step in range(max_steps):
            scratchpad.step = step
            # 1. LLM decide
            decision = await self._decide(scratchpad)
            yield ProgressEvent(f"Bước {step+1}: {decision.action}")

            # 2. Final?
            if decision.action == "final_answer":
                yield FinalAnswerEvent(decision.final_answer or "")
                return

            # 3. Policy check
            self._policy.check(decision.tool_call.tool_name, decision.tool_call.args)

            # 4. Execute tool
            tool_inp = ToolInput(
                tool_name=decision.tool_call.tool_name,
                args=decision.tool_call.args,
                context=ctx,
            )
            result = await self._harness_run_tool_async(tool_inp)
            self._audit_tool_call(step, decision, result, ctx)

            # 5. HITL interrupt
            if result.pending_hitl:
                if result.sse_payload:
                    yield SsePayloadEvent(result.pending_hitl.event_name, result.sse_payload)
                yield PendingHitlEvent(result.pending_hitl)
                return

            # 6. Emit SSE payload nếu có (chart, data_table, ...)
            if result.sse_payload:
                yield SsePayloadEvent(result.sse_payload.get("_event", "data"), result.sse_payload)

            # 7. Ghi observation
            scratchpad.add_observation(result, tool_inp.tool_name)

        # step budget exhausted → best-effort
        self._audit_warn("step_budget_exhausted", ctx)
        yield FinalAnswerEvent(scratchpad.observation_summary())
```

### 5.1 `_decide` — LLM "next-action"

```python
async def _decide(self, scratchpad: TurnScratchpad) -> DecisionSchema:
    client = self._llm_registry.get("harness_planner")   # role mới; fallback "planner"
    messages = scratchpad.to_decision_prompt(
        self._tool_registry.tools_manifest_text()
    )
    return await client.astructured_predict(messages, DecisionSchema)
    # astructured_predict = async wrap của structured_invoke hiện có
```

### 5.2 `OrchestratorEvent` hierarchy

```python
@dataclass
class ProgressEvent:    text: str
@dataclass
class SsePayloadEvent:  event_name: str; payload: dict
@dataclass
class FinalAnswerEvent: text: str
@dataclass
class PendingHitlEvent: spec: HitlSpec
@dataclass
class ErrorEvent:       message: str; code: str
```

---

## 6. Tool adapters — bọc subgraph LangGraph

Mỗi adapter: compile subgraph tương ứng, gọi `compiled.ainvoke(state, config)`, map kết quả → `ToolResult`.

### 6.1 `SqlQueryTool`

```python
# app/graph/tools/sql_query.py
class SqlQueryTool:
    """Wraps build_sql_subgraph. Nhận natural language query → trả rows + observation."""
    manifest = ToolManifest(
        name="sql_query",
        description=(
            "Truy vấn dữ liệu ERP bằng SQL. Dùng khi người dùng hỏi về số liệu, "
            "báo cáo, thống kê, danh sách. Input: câu hỏi tự nhiên hoặc SQL draft."
        ),
        args_schema='{"query": "string (natural language hoặc SQL draft)"}',
    )
    async def invoke(self, args: dict, ctx: TurnContext) -> ToolResult:
        state = _build_sql_state(args["query"], ctx)
        config = _build_config(ctx)
        out = await self._compiled.ainvoke(state, config)
        rows = (out.get("query_result") or {}).get("rows", [])
        ok = bool(out.get("result_ok"))
        obs = _format_rows_observation(rows)   # cắt bớt > 20 rows
        sse = _maybe_data_table_sse(out)       # query_table_sse nếu có
        return ToolResult(ok=ok, output=out, observation_text=obs, sse_payload=sse)
```

### 6.2 `SchemaExploreTool`

```python
# app/graph/tools/schema_explore.py
class SchemaExploreTool:
    manifest = ToolManifest(
        name="schema_explore",
        description=(
            "Khám phá schema DB (bảng, cột, mối quan hệ). Dùng khi chưa biết "
            "bảng nào cần join hoặc tên cột chính xác."
        ),
        args_schema='{"topic": "string (chủ đề hoặc domain cần tìm hiểu schema)"}',
    )
    async def invoke(self, args: dict, ctx: TurnContext) -> ToolResult:
        # Gọi trực tiếp schema_explore node function (không cần full subgraph)
        state = _build_explore_state(args["topic"], ctx)
        out = await self._node_fn(state)       # node function đã được make_schema_explore_node
        obs = str(out.get("runtime_schema_artifact", {}).get("summary", "schema loaded"))
        return ToolResult(ok=True, output=out, observation_text=obs)
```

### 6.3 `CatalogDraftTool` (HITL)

```python
# app/graph/tools/catalog_draft.py
class CatalogDraftTool:
    manifest = ToolManifest(
        name="catalog_draft",
        description="Tạo nháp sản phẩm/danh mục (HITL). Trả pending_hitl → FE hiển thị form xác nhận.",
        args_schema='{"request": "string (mô tả sản phẩm muốn tạo)"}',
        has_hitl=True,
    )
    async def invoke(self, args: dict, ctx: TurnContext) -> ToolResult:
        state = _build_catalog_state(args["request"], ctx)
        out = await self._compiled.ainvoke(state, _build_config(ctx))
        draft_sse = out.get("catalog_draft_sse")
        if draft_sse:
            return ToolResult(
                ok=True, output=out, observation_text="Catalog draft ready — awaiting user confirmation.",
                sse_payload=draft_sse,
                pending_hitl=HitlSpec(
                    event_name="draft",
                    payload=draft_sse,
                    resume_token=ctx.thread_id or ctx.correlation_id,
                ),
            )
        return ToolResult(ok=False, output=out, observation_text="Catalog draft failed.")
```

### 6.4 `InventoryDraftTool` (HITL) — pattern giống CatalogDraftTool, SSE event `"inventory_draft"`

---

## 7. Async migration — danh sách thay đổi chính xác

| File | Thay đổi |
| :-- | :-- |
| `app/llm/openai_compatible.py` | Thêm `ainvoke_text`, `astream_text`, `astructured_predict` dùng `self._chat.ainvoke` / `astream` |
| `app/llm/protocol.py` | Thêm `async` vào protocol methods |
| `app/graph/sql_executor.py` | `HttpSpringSqlExecutor`: thêm `async def aexecute` dùng `httpx.AsyncClient` |
| `app/graph/checkpointing.py` | Thêm `build_async_checkpointer` trả `AsyncSqliteSaver` |
| `app/api/runtime.py` | `LangHarnessRuntime.stream` → `async generator`; `get_graph_runtime` giữ nguyên (Strangler cờ) |

**Giữ sync fallback**: các method sync (`invoke_text`, `execute`) **không xóa** — graph tuyến tính fallback vẫn cần.

---

## 8. Strangler routing

```python
# app/api/runtime.py — thêm vào LangHarnessRuntime

HARNESS_LOOP_INTENTS = frozenset({
    "sql_query", "data_query", "schema_explore",
    "catalog_draft", "inventory_draft",
})

class LangHarnessRuntime:
    """Strangler: route sang orchestrator loop hoặc graph tuyến tính."""
    def __init__(self, compiled_graph, orchestrator, *, graph_settings): ...

    async def astream(self, request, *, correlation_id, bearer_token=None):
        if not graph_settings.harness_loop_enabled:   # cờ mới
            yield from self._legacy_stream(request, ...)
            return

        # Fast-path: domain reject, chat_normal → graph tuyến tính
        quick_intent = _quick_classify(request.message)
        if quick_intent not in HARNESS_LOOP_INTENTS:
            yield from self._legacy_stream(request, ...)
            return

        # Loop path
        scratchpad = _build_scratchpad(request, checkpointer)
        ctx = _build_turn_context(request, correlation_id, bearer_token)
        async for event in self._orchestrator.run(scratchpad, ctx):
            yield _event_to_sse(event)   # giữ đúng SSE event names
```

### 8.1 Config mới cần thêm vào `graph_settings.py`

```python
harness_loop_enabled: bool = Field(default=False, ...)   # Strangler gate
harness_max_steps: int     = Field(default=6, ge=1, le=20, ...)
harness_loop_intents: list[str] = Field(default_factory=list, ...)  # override HARNESS_LOOP_INTENTS
harness_planner_role: str  = Field(default="harness_planner", ...)
```

---

## 9. State refactor — minimal, không phá checkpoint cũ

**Không xóa `AgentState`** — graph tuyến tính (fallback) vẫn dùng. Thay vào đó:

1. Thêm comment `# TRANSIENT — cleared each turn` vào mỗi key transient trong `state.py`.
2. Tạo `fresh_turn_overlay()` trong `state.py`:

```python
_TRANSIENT_KEYS = frozenset({
    "query_result", "generated_sql", "final_answer", "error_payload",
    "intent", "route_source", "sql_review_ok", "sql_valid", "result_ok",
    "result_empty", "runtime_schema_artifact", "selected_tables",
    "sql_gen_mode", "sql_attempt_history", "sql_local_pool",
    "idea_data_request", "idea_chart_idea", "chart_spec_draft", "chart_spec_final",
    "schema_plan", "ledger_metric_id", "schema_join_hints", "chart_brief",
    "chart_thread_context", "chart_data_ok", "chart_data_issues", "chart_warnings",
    "chart_retry_hint", "chart_result_profile", "chart_degraded",
    "catalog_entity_type", "catalog_row_count_hint", "catalog_draft_slots",
    "catalog_draft_payload", "catalog_draft_id", "catalog_draft_sse",
    "inventory_doc_type", "inventory_line_count_hint", "inventory_draft_slots",
    "inventory_draft_payload", "inventory_draft_id", "inventory_draft_sse",
    "domain_guard_action", "normalized_user_question", "domain_context",
    "domain_clarify_sse", "pending_clarification", "clarification_applied_context",
    "show_query_table", "query_table_sse", "planner_strategy", "planner_reason",
    "planner_confidence", "planner_doc_refs", "progress_text",
})

def fresh_turn_overlay() -> dict:
    return {k: None for k in _TRANSIENT_KEYS}
```

3. Trong `api/runtime.py` thay toàn bộ khối `state["key"] = None` (dòng 102–167) bằng `state.update(fresh_turn_overlay())`. Một dòng.

---

## 10. SSE contract (không đổi với FE)

Bảng map từ `OrchestratorEvent` → SSE event name (giống `_iter_chat_sse_events` hiện tại):

| `OrchestratorEvent` | SSE event name | Ghi chú |
| :-- | :-- | :-- |
| `ProgressEvent` | `progress` | Giữ nguyên |
| `FinalAnswerEvent` | `delta_full` + `delta` (diff) | Giữ nguyên logic delta |
| `SsePayloadEvent("chart", ...)` | `chart` | Giữ nguyên |
| `SsePayloadEvent("draft", ...)` | `draft` | Giữ nguyên |
| `SsePayloadEvent("inventory_draft", ...)` | `inventory_draft` | Giữ nguyên |
| `SsePayloadEvent("data_table", ...)` | `data_table` | Giữ nguyên |
| `PendingHitlEvent` | phát SSE rồi dừng (không `done` sớm) | HITL giữ nguyên flow FE |
| `ErrorEvent` | `error` | Giữ nguyên |
| end of stream | `done` | Luôn phát cuối |

---

## 11. Implementation slices (thứ tự thực thi)

### Phase 1 — Foundation (thứ tự quan trọng)

| Slice | File(s) | Nội dung | Depends on |
| :-- | :-- | :-- | :-- |
| S-1 | `app/harness/scratchpad.py` | `TurnScratchpad`, `Observation`, `to_decision_prompt`, `add_observation` | — |
| S-2 | `app/harness/policy.py` | `HarnessPolicy`, `Capability`, `TOOL_CAPABILITIES`, `HarnessPolicyError` | — |
| S-3 | `app/harness/tool_registry.py` | `ToolManifest`, `ToolRegistry`, `AsyncTool`, `ToolInput`, `ToolResult`, `HitlSpec`, `TurnContext`, `DecisionSchema` | — |
| S-4 | `app/graph/tools/sql_query.py` | `SqlQueryTool` | S-3, sql_subgraph |
| S-5 | `app/graph/tools/schema_explore.py` | `SchemaExploreTool` | S-3 |
| S-6 | `app/graph/tools/catalog_draft.py` | `CatalogDraftTool` | S-3 |
| S-7 | `app/graph/tools/inventory_draft.py` | `InventoryDraftTool` | S-3 |
| S-8 | `app/harness/orchestrator.py` | `HarnessOrchestrator`, `OrchestratorEvent` hierarchy | S-1..S-7 |

### Phase 2 — Async migration

| Slice | File(s) | Nội dung |
| :-- | :-- | :-- |
| S-9 | `app/llm/openai_compatible.py`, `app/llm/protocol.py` | Thêm `ainvoke_text`, `astream_text`, `astructured_predict` |
| S-10 | `app/graph/sql_executor.py` | Thêm `async def aexecute` với `httpx.AsyncClient` |
| S-11 | `app/graph/checkpointing.py` | Thêm `build_async_checkpointer` → `AsyncSqliteSaver` |

### Phase 3 — State cleanup

| Slice | File(s) | Nội dung |
| :-- | :-- | :-- |
| S-12 | `app/graph/state.py` | Thêm `_TRANSIENT_KEYS`, `fresh_turn_overlay()` |
| S-13 | `app/api/runtime.py` | Thay khối ~60 dòng null bằng `state.update(fresh_turn_overlay())` |

### Phase 4 — Strangler integration

| Slice | File(s) | Nội dung |
| :-- | :-- | :-- |
| S-14 | `app/config/graph_settings.py` | Thêm 4 config field: `harness_loop_enabled`, `harness_max_steps`, `harness_loop_intents`, `harness_planner_role` |
| S-15 | `app/api/runtime.py` | Thêm `LangHarnessRuntime`, Strangler routing trong `get_graph_runtime` |
| S-16 | `app/llm/registry.py` | Đăng ký role `"harness_planner"` (fallback → `"planner"`) |
| S-17 | `app/harness/__init__.py` | Export mới: `HarnessOrchestrator`, `ToolRegistry`, `HarnessPolicy`, `TurnScratchpad` |

---

## 12. Horizontal analysis — điểm cần chú ý khi coding

1. **`app/graph/progress.py` / `wrap_node_with_stream_progress`** — subgraph vẫn dùng khi compile; tool adapter cần đảm bảo progress event từ subgraph được forward qua `ToolResult.sse_payload` hoặc bỏ qua (không double-emit).
2. **`app/graph/nodes/sql_pipeline.py` `_load_schema_artifact` (line 316)** — có thể gọi DB mỗi lần compile state; tool adapter phải forward `schema_version` và `tenant_id` đúng để cache hit.
3. **`app/graph/checkpointing.py:16`** — `SqliteSaver` sync dùng 1 connection; khi chuyển async cần `AsyncSqliteSaver` riêng instance cho orchestrator path.
4. **`spring_bearer_token`** trong `AgentState` — tool adapters phải forward từ `TurnContext.bearer_token` vào state trước khi gọi subgraph.
5. **`sql_attempt_count` / `sql_repair_max_attempts`** — reset về `0` / `None` trong mỗi `SqlQueryTool.invoke` state build để không kế thừa lượt trước.

---

## 13. Files KHÔNG được sửa (per AGENTS.md)

- `app/graph/main_graph.py` — fallback graph tuyến tính, Strangler giữ nguyên
- `app/graph/nodes/` toàn bộ — các node hiện hữu là implementation, không đổi logic
- Bất kỳ test file nào cho graph tuyến tính (chỉ thêm test mới, không xóa)

---

> **Readiness**: READY_FOR_CODING — 17 slices, 4 phases, không có blocker. OD-5/6/7 đã chốt.
