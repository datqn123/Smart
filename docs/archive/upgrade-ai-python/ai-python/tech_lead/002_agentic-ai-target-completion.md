# Tech Spec 002 (upgrade/ai-python): Hoàn thiện Agentic AI theo Target Design

- **SRS ref**: `docs/upgrade/ai-python/srs/004_agentic-ai-target-completion.md`
- **Nối tiếp**: Tech Spec 001 (`docs/upgrade/ai-python/tech_lead/001_harness-orchestrated-agentic-loop.md`)
- **Stage**: TECH_SPEC_WRITER (writing-plans)
- **Date**: 2026-06-07
- **CodeGraph**: status (876 files) + context(harness loop) + explore(orchestrator/tool_registry/scratchpad/runtime) — đã chạy
- **Readiness**: **READY_WITH_RISKS** (OQ-1/OQ-2 Spring confirm endpoint mở → nhánh confirm thật dùng stub; mọi phase khác READY_FOR_CODING với mock)

---

## 0. Owner Decisions — chốt ở đây

Kế thừa OD-5 (JSON-structured `astructured_predict`), OD-6 (`AsyncSqliteSaver`), OD-7 (best-effort khi chạm trần) từ Tech Spec 001. Chốt thêm:

| ID | Quyết định | Lựa chọn | Lý do |
| :-- | :-- | :-- | :-- |
| OD-8 | Plan-driven vs reactive | **Reactive-loop là mặc định; PlanGraph (P2) là chế độ opt-in qua cờ `agentic_plan_dag_enabled`** | Loop 002 đã chạy ổn; PlanGraph chỉ bật cho intent cần fan-out (vd chart_report cần 2 SQL). Giảm rủi ro. |
| OD-9 | Semantic store | **Protocol `SemanticStore` + `InMemorySemanticStore` (default) + `PgVectorSemanticStore` (khi `SEMANTIC_STORE_MODE=pg`)** | Test tất định không cần pgvector; prod swap qua env. |
| OD-10 | Spring confirm endpoint | **CHƯA chốt (OQ-1/OQ-2)** → P4/HITL confirm code path `_confirm_via_spring()` nhưng gọi qua `CatalogDraftClient.confirm()` đã có nếu tồn tại; nếu chưa → raise `NotImplementedError("OQ-1")` được bắt và trả observation stub, đánh dấu TODO | Không chặn toàn run; nhánh generate + pending_hitl vẫn test được đầy đủ. |
| OD-11 | Cấu trúc subagent mới | **Mỗi subagent là 1 class trong `app/harness/` (intent, plan, compact, model_router) hoặc `app/graph/tools/` (data_validator, answer_composer, build_chart, erp_guide)** | Giữ tách biệt: harness = điều phối/quyết định; tools = tích hợp scoped. |

---

## 1. Kiến trúc file sau SRS-004

```
app/
├── harness/
│   ├── orchestrator.py     (mở rộng: budget, intent gate, plan mode, model_router, cache, observability)
│   ├── tool_registry.py    (mở rộng TurnContext: intent_object, memory, role)
│   ├── scratchpad.py       (đính kèm IntentObject + working memory vào prompt)
│   ├── policy.py           (P6: capability matrix + sensitive mask + anti-injection)
│   ├── runtime.py          (AgentHarness: thêm arun_tool async + token/cost audit)
│   ├── budget.py           ← MỚI P0: TurnBudget + BudgetExceeded
│   ├── intent.py           ← MỚI P1: IntentObject, IntentSubagent, EntityResolver
│   ├── plan_graph.py       ← MỚI P2: PlanNode, PlanGraph, PlanExecutor, PlannerSubagent
│   ├── memory.py           ← MỚI P5: WorkingMemory, EpisodicMemory, SemanticStore (+InMemory/PgVector)
│   ├── compact.py          ← MỚI P5: CompactSubagent
│   ├── capability.py       ← MỚI P6: CapabilityMatrix, sensitive-column masking
│   ├── model_router.py     ← MỚI P7: ModelRouter
│   ├── cache.py            ← MỚI P7: SemanticCache (+InMemory)
│   └── observability.py    ← MỚI P8: TraceRecorder, TurnMetrics
├── graph/
│   ├── tools/
│   │   ├── sql_query.py        (P3: budget regen/retry + dedup + degrade)
│   │   ├── data_validator.py   ← MỚI P3
│   │   ├── answer_composer.py  ← MỚI P4
│   │   ├── build_chart.py      ← MỚI P4
│   │   └── erp_guide.py        ← MỚI P4
│   ├── nodes/sql_pipeline.py   (P3: tách sql_raw/sql_review/execute, giữ public API)
│   └── checkpointing.py        (P5: persist pending_hitl theo thread_id)
├── llm/
│   ├── openai_compatible.py    (P0: ainvoke/astream + InvokeUsage thật)
│   └── registry.py             (P7: cấp client theo model id router chọn)
├── config/graph_settings.py    (cờ + ngưỡng mọi phase)
└── api/runtime.py              (wiring: intent gate, budget, memory; giữ SSE/HTTP contract)

scripts/eval_golden.py          ← MỚI P8
tests/                          ← test mỗi phase + test_e2e_agentic_flow.py
tests/fake_llm.py               (mở rộng: schema giả cho mọi subagent mới)
```

---

## 2. Cờ cấu hình mới (`app/config/graph_settings.py`)

Tất cả mặc định OFF/an toàn (Strangler). Thêm:

```python
# P0
agentic_async_enabled: bool = Field(default=False)
harness_token_budget: int = Field(default=0)          # 0 = tắt; >0 bật
harness_cost_budget_usd: float = Field(default=0.05)  # D9
harness_wallclock_timeout_s: float = Field(default=30.0)  # D9
# P1
agentic_intent_object_enabled: bool = Field(default=False)
intent_confidence_run: float = Field(default=0.9)     # D1
intent_confidence_hitl: float = Field(default=0.75)   # D1
entity_score_hitl: float = Field(default=0.6)         # D2
# P2
agentic_plan_dag_enabled: bool = Field(default=False)
plan_replan_max: int = Field(default=2)
# P3
sql_regen_max: int = Field(default=3)                 # D11
sql_empty_retry_max: int = Field(default=2)           # D11
agentic_data_validator_enabled: bool = Field(default=False)
# P4
agentic_answer_composer_enabled: bool = Field(default=False)
# P5
working_memory_pairs: int = Field(default=6)          # D3
compact_context_ratio: float = Field(default=0.70)    # D4
semantic_store_mode: str = Field(default="memory")    # "memory" | "pg"; OD-9
semantic_expire_days: int = Field(default=90)         # D5
# P6
agentic_capability_guard_enabled: bool = Field(default=False)
# P7
agentic_model_routing_enabled: bool = Field(default=False)
agentic_semantic_cache_enabled: bool = Field(default=False)
opt_escalate_replan_count: int = Field(default=2)     # D10 leo Opus khi replan ≥2
# P8
agentic_trace_enabled: bool = Field(default=True)
```

---

## 3. Phase P0 — Async boundary + Budget + Token/Cost

### 3.1 Contracts

```python
# app/harness/budget.py  (MỚI)
from dataclasses import dataclass
import time

class BudgetExceeded(Exception):
    def __init__(self, kind: str):   # "step" | "token" | "cost" | "wallclock"
        self.kind = kind

@dataclass
class TurnBudget:
    max_steps: int
    token_budget: int          # 0 = unlimited
    cost_budget_usd: float
    wallclock_timeout_s: float
    _started: float = 0.0
    used_tokens: int = 0
    used_cost_usd: float = 0.0

    def start(self) -> None: self._started = time.monotonic()
    def add_usage(self, tokens: int, cost_usd: float) -> None:
        self.used_tokens += tokens; self.used_cost_usd += cost_usd
    def check(self, step: int) -> None:
        """Raise BudgetExceeded khi chạm bất kỳ trần (trừ step do loop tự quản)."""
        if self.token_budget and self.used_tokens >= self.token_budget: raise BudgetExceeded("token")
        if self.used_cost_usd >= self.cost_budget_usd: raise BudgetExceeded("cost")
        if time.monotonic() - self._started >= self.wallclock_timeout_s: raise BudgetExceeded("wallclock")
```

```python
# app/harness/runtime.py — AgentHarness thêm async + usage
async def arun_tool(self, *, tool_name, tool, context=None) -> Any:
    """Async tương đương run_tool; audit thêm latency_ms."""
# audit row mỗi tool-call thêm: "latency_ms", "tokens", "cost_usd"
```

```python
# app/llm/openai_compatible.py — InvokeUsage điền thật
@dataclass
class InvokeUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
# astructured_predict / ainvoke_text trả (result, InvokeUsage) hoặc set last_usage
```

### 3.2 Orchestrator thay đổi
- `run()` khởi tạo `TurnBudget` từ settings, `budget.start()`.
- Sau mỗi `_decide` và mỗi tool-call: `budget.add_usage(...)` từ `last_usage`; gọi `budget.check(step)`.
- Bắt `BudgetExceeded` → `self._audit_warn(f"{exc.kind}_budget_exhausted", ctx)` → `yield FinalAnswerEvent(scratchpad.observation_summary())`.
- Rebuild `_iter_harness_stream`: nếu `agentic_async_enabled` → `StreamingResponse` async generator gốc; nếu OFF → giữ event-loop bridge cũ (fallback).

### 3.3 Test
- File: `tests/test_harness_budget.py`, mở rộng `tests/test_harness_async_contracts.py`.
- Mock: `FakeLlmClient` trả `last_usage = InvokeUsage(prompt_tokens=50, completion_tokens=50, cost_usd=0.001)`.
- Case cost: `harness_cost_budget_usd=0.0025` → loop dừng ở step 3, audit có `cost_budget_exhausted`.
- Case wallclock: monkeypatch `time.monotonic` → dừng `wallclock`.
- **E2E (tạo mới)** `tests/test_e2e_agentic_flow.py`: khung dùng FakeLlmClient + stub SQL; ở P0 chỉ assert: request đơn giản → loop chạy → `final_answer` → SSE `done`, audit có `tokens/cost/latency`.
- Lệnh: `python -m pytest tests/test_harness_budget.py tests/test_harness_async_contracts.py tests/test_e2e_agentic_flow.py tests -q`

---

## 4. Phase P1 — IntentObject + Confidence + EntityResolver

### 4.1 Contracts

```python
# app/harness/intent.py  (MỚI)
from pydantic import BaseModel, Field

class ResolvedEntity(BaseModel):
    raw: str
    matched: str = ""
    score: float = 0.0

class Ambiguity(BaseModel):
    field: str
    options: list[str] = Field(default_factory=list)
    reason: str = ""

class IntentObject(BaseModel):
    goal: str
    intent_type: str   # data_query|chart_report|catalog_draft|inventory_draft|chat|out_of_scope
    required_data: list[str] = Field(default_factory=list)
    resolved_entities: list[ResolvedEntity] = Field(default_factory=list)
    confidence: float = 0.0
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)

# LLM output schema (cho astructured_predict + FakeLlmClient)
class IntentObjectOutput(IntentObject): ...

class IntentDecision(BaseModel):
    mode: str          # "run" | "auto_assume" | "clarify"
    clarify_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

class IntentSubagent:
    def __init__(self, *, llm_registry, entity_resolver, settings): ...
    async def analyze(self, question: str, memory_text: str, dictionary_text: str) -> IntentObject: ...
    def decide(self, intent: IntentObject) -> IntentDecision:
        """Áp ngưỡng D1/D2 → mode."""
        if intent.missing_required: return IntentDecision(mode="clarify", clarify_questions=_q(intent))
        min_entity = min([e.score for e in intent.resolved_entities], default=1.0)
        if intent.confidence < settings.intent_confidence_hitl or min_entity < settings.entity_score_hitl:
            return IntentDecision(mode="clarify", clarify_questions=_q(intent))
        if intent.confidence < settings.intent_confidence_run:
            return IntentDecision(mode="auto_assume", assumptions=_assume(intent))
        return IntentDecision(mode="run")
```

```python
# EntityResolver — fuzzy + embedding (fallback fuzzy-only)
class EntityResolver:
    def __init__(self, *, semantic_store, synonym_map): ...   # synonym_map từ K2
    async def score(self, raw: str, entity_type: str) -> ResolvedEntity:
        """embedding similarity (semantic_store) kết hợp rapidfuzz; lấy max."""
```

### 4.2 Orchestrator gate
- Trước loop, nếu `agentic_intent_object_enabled`: gọi `IntentSubagent.analyze` + `decide`.
  - `mode="clarify"` → `yield ClarifyEvent(questions, ...)` rồi return (tận dụng SSE `clarify` đã có).
  - `mode="auto_assume"` → đính kèm assumptions vào scratchpad (answer_composer P4 sẽ nêu).
  - `mode="run"` → vào loop; gắn IntentObject vào `ctx.intent_object` (thêm field optional).
- `TurnContext` thêm: `intent_object: IntentObject | None = None`.

### 4.3 Test
- File: `tests/test_intent_object.py`, `tests/test_intent_confidence_thresholds.py`.
- `fake_llm.py` thêm nhánh `IntentObjectOutput` (tham số hoá: `intent_confidence`, `intent_missing`, `intent_entity_score`).
- 3 case: confidence 0.95 → run; missing time period → clarify; entity score 0.5 → clarify với options.
- EntityResolver test với `InMemorySemanticStore` (3 SKU giả) + synonym map nhỏ.
- **E2E mở rộng**: thêm assert intent gate (clarify branch phát đúng SSE `clarify`).
- Lệnh: `python -m pytest tests/test_intent_object.py tests/test_intent_confidence_thresholds.py tests/test_e2e_agentic_flow.py tests -q`

---

## 5. Phase P2 — PlanGraph + Fan-out + Replan

### 5.1 Contracts

```python
# app/harness/plan_graph.py  (MỚI)
class PlanNode(BaseModel):
    id: str
    tool: str
    needs: list[str] = Field(default_factory=list)
    input_spec: dict = Field(default_factory=dict)
    output_expect: str = ""

class PlanGraph(BaseModel):
    nodes: list[PlanNode]

class PlanGraphOutput(PlanGraph): ...   # LLM schema

class PlannerSubagent:
    async def plan(self, intent: IntentObject, dictionary_text: str) -> PlanGraph: ...

class NodeResult(BaseModel):
    node_id: str
    ok: bool
    output_meets_expect: bool
    tool_result: dict          # ToolResult.output rút gọn

class PlanExecutor:
    def __init__(self, *, tool_registry, policy, harness, validator): ...
    async def execute(self, plan: PlanGraph, ctx: TurnContext) -> list[NodeResult]:
        """
        Topo-sort theo needs. Các node cùng tầng (needs đã xong) chạy ĐỒNG THỜI
        bằng asyncio.gather. Mỗi node: policy.check → arun_tool → validate output_expect.
        Trả NodeResult[]. Node fail/không-meets-expect → đánh dấu để replan.
        """
    def needs_replan(self, results: list[NodeResult]) -> bool: ...
```

### 5.2 Orchestrator plan mode
- Nếu `agentic_plan_dag_enabled` và `intent.intent_type in {data_query, chart_report}`:
  - `plan = await planner.plan(intent, dict)`; `results = await executor.execute(plan, ctx)`.
  - `needs_replan` và `replan_count < plan_replan_max` → planner sửa node lỗi/thêm clarify → execute lại.
  - Vượt `plan_replan_max` → degrade (best-effort answer từ NodeResult đã có).
- Cờ OFF → dùng loop reactive (002), không đổi.

### 5.3 Test
- File: `tests/test_plan_graph.py`, `tests/test_plan_parallel.py`.
- Song song: hai node SQL độc lập; dùng `asyncio.Event`/đếm `concurrent_peak` trong fake tool để chứng minh chạy đồng thời (peak ≥ 2).
- Replan: validator fail node n1 → planner trả plan v2 → executor pass.
- `fake_llm.py` thêm `PlanGraphOutput`.
- **E2E mở rộng**: bật `agentic_plan_dag_enabled` cho 1 case chart_report → 2 SQL song song → chart.
- Lệnh: `python -m pytest tests/test_plan_graph.py tests/test_plan_parallel.py tests/test_e2e_agentic_flow.py tests -q`

---

## 6. Phase P3 — SQL self-correct (tool hoá) + DataValidator

### 6.1 Tách `sql_pipeline.py` (giữ public API)
- Trích hàm thuần: `sql_raw(state) -> str`, `sql_review(state, sql) -> SqlReviewOutput`, `execute(state, sql) -> rows`. Giữ tên export hiện có để graph cũ không vỡ.
- `SqlQueryTool.invoke` điều phối budget:

```python
# app/graph/tools/sql_query.py (mở rộng)
async def invoke(self, args, ctx) -> ToolResult:
    seen: set[str] = set()        # fingerprint = hash(sql + reason)
    regen = 0; empty_retry = 0
    while regen <= settings.sql_regen_max:
        sql = await self._gen(args, ctx, hint=last_hint)
        review = await self._review(sql, ctx)
        fp = _fingerprint(sql, review.issues)
        if fp in seen: break          # dedup short-circuit
        seen.add(fp)
        if not review.ok:
            regen += 1; last_hint = review.retry_hint; continue
        rows = await self._execute(sql, ctx)
        if not rows and empty_retry < settings.sql_empty_retry_max:
            empty_retry += 1; continue
        return ToolResult(ok=True, output={"rows": rows, "sql": sql}, ...)
    # degrade: trả kết quả gần nhất hợp lệ + cảnh báo
    return ToolResult(ok=True, output={"rows": last_rows, "degraded": True},
                      observation_text="Không tối ưu hoàn toàn; trả kết quả gần nhất kèm cảnh báo.")
```

### 6.2 DataValidator

```python
# app/graph/tools/data_validator.py (MỚI)
class DataValidatorOutput(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)   # "negative_value", "missing_column", "time_mismatch"
    severity: str = "info"   # info|warn|fail

class DataValidatorTool:   # AsyncTool
    manifest = ToolManifest(name="data_validator",
        description="Kiểm tra tính hợp lý nghiệp vụ của rows (số âm, vượt trần, thiếu cột vs required_data, lệch thời gian).",
        args_schema='{"rows":"list","required_data":"list[str]"}')
    async def invoke(self, args, ctx) -> ToolResult:
        # rule-based (K8 công thức) + optional LLM cho ca mơ hồ
        ...  # ok=False khi severity=="fail" → trigger replan (P2) hoặc clarify
```

### 6.3 Test
- File: `tests/test_data_validator.py`, `tests/test_sql_self_correct_budget.py` (+ giữ `test_sql_query_domain.py`).
- Dùng `FakeLlmClient(sql_review_failures=2)` (có sẵn) → regen 2 rồi pass; rows âm → validator fail; dedup: review trả cùng issue 2 lần → break.
- Read-only: SQL chứa `update`/`drop` → `HarnessPolicyError` (P6 củng cố; ở P3 vẫn qua `enforce_read_only_sql`).
- **E2E mở rộng**: SQL self-correct + validator pass trong pipeline.
- Lệnh: `python -m pytest tests/test_data_validator.py tests/test_sql_self_correct_budget.py tests/test_sql_query_domain.py tests/test_e2e_agentic_flow.py tests -q`

---

## 7. Phase P4 — AnswerComposer + chart + erp_guide tools

### 7.1 Contracts

```python
# app/graph/tools/answer_composer.py (MỚI)
class AnswerComposerOutput(BaseModel):
    answer_markdown: str            # tiếng Việt, có điểm nhấn/bảng
    assumptions: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)   # 1-3 câu

class AnswerComposerTool:
    manifest = ToolManifest(name="answer_composer",
        description="Soạn câu trả lời cuối giàu thông tin từ observations + nêu giả định + 1-3 gợi ý tiếp theo.",
        args_schema='{"observations":"list","assumptions":"list[str]"}')
    async def invoke(self, args, ctx) -> ToolResult:
        out: AnswerComposerOutput = await self._compose(args, ctx)  # đọc K10 template, K14 format VND/ngày
        text = _render(out)   # gắn follow-ups + assumptions
        return ToolResult(ok=True, output=out.model_dump(), observation_text=text,
                          sse_payload={"_event":"delta_full","text":text})
```

```python
# app/graph/tools/build_chart.py (MỚI) — wrap chart subgraph hiện hữu, chọn type theo shape (K9)
# app/graph/tools/erp_guide.py   (MỚI) — wrap erp_guide node (K13)
```
- Đăng ký 3 tool vào registry. answer_composer được phép là tool "kết" mà orchestrator gọi trước final_answer (hoặc orchestrator dùng nó để sinh final text).

### 7.2 Test
- File: `tests/test_answer_composer.py` (+ giữ `test_chart_pipeline.py`).
- `fake_llm.py` thêm `AnswerComposerOutput` (answer + 2 follow_ups).
- Case rows time-series → `build_chart` chọn `line`; rows rỗng → composer trả thông điệp hướng dẫn; assert follow_ups ≥ 1 và toàn tiếng Việt.
- **E2E mở rộng**: pipeline kết bằng answer_composer → SSE `delta_full` chứa gợi ý.
- Lệnh: `python -m pytest tests/test_answer_composer.py tests/test_chart_pipeline.py tests/test_e2e_agentic_flow.py tests -q`

---

## 8. Phase P5 — Memory 3 tầng + Compact + Persistence

### 8.1 Contracts

```python
# app/harness/memory.py (MỚI)
class WorkingMemory:
    def __init__(self, pairs: int): ...   # N=6 (D3)
    def attach(self, messages: list[BaseMessage]) -> list[BaseMessage]: ...  # giữ N cặp gần nhất

class EpisodicMemory:
    summary: str   # [COMPACT] block của phiên

class SemanticRecord(BaseModel):
    user_id: str; kind: str; content: str; embedding: list[float] | None = None; created_at: float

class SemanticStore(Protocol):           # OD-9
    async def upsert(self, rec: SemanticRecord) -> None: ...
    async def recall(self, user_id: str, query: str, k: int = 5) -> list[SemanticRecord]: ...

class InMemorySemanticStore(SemanticStore):   # default test; cosine trên list
    ...
class PgVectorSemanticStore(SemanticStore):   # khi SEMANTIC_STORE_MODE=pg; expire D5
    ...
```

```python
# app/harness/compact.py (MỚI)
class CompactOutput(BaseModel):
    compact_block: str   # bắt đầu bằng "[COMPACT]"
class CompactSubagent:
    def should_compact(self, token_count: int, window: int) -> bool:
        return token_count >= window * settings.compact_context_ratio   # 0.70 (D4)
    async def compact(self, messages) -> CompactOutput: ...   # giữ mốc/ràng buộc/kết quả; không nén phần đang dở
```

### 8.2 Persistence
- `checkpointing.py`: persist `pending_hitl` record theo `thread_id` (nâng cấp `_pending_hitl` in-memory của 003). Nếu `agentic_async_enabled` → `AsyncSqliteSaver`.
- `api/runtime.py`: nạp WorkingMemory mỗi require; PII filter (D6) trước upsert semantic; thay reset thủ công bằng `fresh_turn_overlay()` (đã định ở Tech Spec 001 S-12/S-13).

### 8.3 Test
- File: `tests/test_memory_tiers.py`, `tests/test_checkpoint_persist.py` (+ giữ `test_context_compact.py`).
- WorkingMemory giữ đúng 6 cặp; compact kích hoạt khi ép `compact_context_ratio` thấp → block bắt đầu `[COMPACT]`.
- `InMemorySemanticStore` recall trả record liên quan; PII thô (số điện thoại) không được upsert.
- Persistence: restart giả lập (tạo store mới) → resume trả `HITL_EXPIRED` rõ ràng nếu in-memory; với AsyncSqliteSaver giữ được.
- Lệnh: `python -m pytest tests/test_memory_tiers.py tests/test_checkpoint_persist.py tests/test_context_compact.py tests/test_e2e_agentic_flow.py tests -q`

---

## 9. Phase P6 — Capability/RBAC + sensitive mask + anti-injection + idempotency

### 9.1 Contracts

```python
# app/harness/capability.py (MỚI) — đọc K6 RBAC matrix, K5 allowlist
SENSITIVE_COLUMNS = {   # D7
    "products.cost_price", "finance_ledger", "margin",
}
class CapabilityMatrix:
    def can(self, role: str, action: str) -> bool: ...        # owner/staff × action
    def mask_columns(self, role: str, rows: list[dict]) -> list[dict]:
        """staff: ẩn cột nhạy cảm; owner: full."""

def sanitize_user_data(text: str) -> str:
    """Bỏ qua chỉ thị nhúng trong dữ liệu (G4): tách data khỏi instruction; strip
    các pattern kiểu 'ignore previous', 'system:' trong nội dung rows trước khi đưa vào prompt."""
```

```python
# app/harness/policy.py (mở rộng HarnessPolicy.check)
def check(self, tool_name, args, *, role=None, tenant_id=None) -> None:
    # 1. capability theo role (thay _is_denied_tool substring)
    # 2. SQL read-only (giữ DENIED_SQL_KEYWORDS — defense in depth)
    # 3. tenant scope
# Mask áp ở tool output (sql_query/data_validator) qua CapabilityMatrix.mask_columns.
# Idempotency: draft tools nhận idempotency_key = hash(thread_id+payload); Spring confirm dùng key.
```
- `TurnContext` thêm: `role: str | None = None` (từ request metadata).
- Gỡ `_is_denied_tool` substring khỏi đường harness (giữ cho legacy nếu cần), thay bằng `HarnessPolicy`.

### 9.2 Test
- File: `tests/test_capability_rbac.py`, `tests/test_anti_injection.py` (+ giữ `test_harness_policy.py`).
- staff hỏi `cost_price` → bị mask/từ chối ("Bạn không có quyền..."); owner thấy đủ.
- SQL `; DROP TABLE` → `HarnessPolicyError` (100%).
- rows chứa "ignore previous instructions" → `sanitize_user_data` loại bỏ, hành vi không đổi.
- double-submit cùng idempotency_key → 1 lần confirm (mock Spring đếm call).
- Lệnh: `python -m pytest tests/test_capability_rbac.py tests/test_anti_injection.py tests/test_harness_policy.py tests/test_e2e_agentic_flow.py tests -q`

---

## 10. Phase P7 — Model routing + Semantic cache

### 10.1 Contracts

```python
# app/harness/model_router.py (MỚI) — D10
WORK_MODEL_TIER = {
    "intent": "haiku", "compact": "haiku",
    "planner": "sonnet", "sql": "sonnet", "answer_composer": "sonnet",
}
class ModelRouter:
    def pick(self, work: str, *, replan_count: int = 0) -> str:
        if replan_count >= settings.opt_escalate_replan_count: return "opus"   # leo Opus
        return WORK_MODEL_TIER.get(work, "sonnet")
# llm_registry.get(model_id) cấp client tương ứng (model id đã cấu hình sẵn trong registry)
```

```python
# app/harness/cache.py (MỚI) — N3
class SemanticCache(Protocol):
    def get(self, key: str) -> Any | None: ...
    def put(self, key: str, value: Any) -> None: ...
class InMemorySemanticCache(SemanticCache): ...   # default
# key = hash(tool_name + fingerprint(args) + tenant_id); chỉ cache kết quả tất định
# (schema_explore, sql_query theo fingerprint+tenant). Audit "cache_hit"/"cache_miss".
```

### 10.2 Test
- File: `tests/test_model_router.py`, `tests/test_semantic_cache.py`.
- router: work="intent"→haiku; replan_count=2→opus.
- cache: 2 lượt cùng (tool+args+tenant) → lượt 2 `cache_hit`, không gọi tool lại (mock đếm); tenant khác → miss.
- Lệnh: `python -m pytest tests/test_model_router.py tests/test_semantic_cache.py tests/test_e2e_agentic_flow.py tests -q`

---

## 11. Phase P8 — Observability + Eval golden

### 11.1 Contracts

```python
# app/harness/observability.py (MỚI)
@dataclass
class TurnMetrics:
    intent: str; steps: int; replans: int; hitl: bool
    tokens: int; cost_usd: float; latency_ms: float; budget_hit: str | None
class TraceRecorder:
    def record_step(self, *, step, tool, ok, tokens, cost_usd, latency_ms) -> None: ...
    def finalize(self) -> TurnMetrics: ...   # ghi audit jsonl + log
```

```python
# scripts/eval_golden.py (MỚI)
# Đọc docs/ai-python/agentic-ai-supporting-assets/013_K12_golden_eval_set.md (subset ≥10 câu)
# Chạy offline (FakeLlmClient/stub) → so intent/answer-shape kỳ vọng → in pass-rate.
# CLI: python scripts/eval_golden.py --offline [--min-pass 0.8]
```

### 11.2 Test
- File: `tests/test_observability.py`; chạy `python scripts/eval_golden.py --offline`.
- assert TurnMetrics có cost/latency/retry; audit ghi `*_budget_exhausted` khi chạm trần.
- Lệnh: `python -m pytest tests/test_observability.py tests/test_e2e_agentic_flow.py tests -q && python scripts/eval_golden.py --offline`

---

## 12. E2E flow cuối (`tests/test_e2e_agentic_flow.py` đầy đủ sau P8)

Một test tích hợp offline (FakeLlmClient + `SQL_EXECUTOR_MODE=stub` + `InMemorySemanticStore` + `InMemorySemanticCache`):

```
request "Doanh thu và tồn kho tháng này, vẽ biểu đồ" (role=owner)
 → intent gate: confidence 0.95 → run; intent_type=chart_report; required_data=[revenue,inventory]
 → plan_dag enabled: PlanGraph 2 SQL node (song song) → data_validator → build_chart → answer_composer
 → policy.check mỗi node (read-only + role owner)
 → SSE thứ tự: progress* → chart → delta_full(+follow_ups) → done
 → TraceRecorder.finalize có tokens/cost/latency
HITL e2e: "tạo sản phẩm Áo thun" → catalog_draft pending_hitl → SSE draft (không done)
 → resume (clarification) → confirm path (stub nếu OQ-10) → final_answer → done
Regression e2e: tắt mọi cờ agentic → đi loop 002 → kết quả như cũ
```
- Lệnh tổng: `cd ai_python && python -m pytest tests -q` (toàn bộ phải xanh). Tùy chọn FE khói: `cd frontend/mini-erp && npm run test:e2e`.

---

## 13. fake_llm.py — schema cần thêm (tổng hợp)

`tests/fake_llm.py::FakeLlmClient.structured_predict` (và bản async `astructured_predict`) thêm nhánh trả tất định cho:
`IntentObjectOutput`, `IntentDecision`(nếu LLM-driven), `PlanGraphOutput`, `DataValidatorOutput`, `AnswerComposerOutput`, `CompactOutput`. Tham số hoá qua `__init__` (vd `intent_confidence`, `intent_missing`, `plan_nodes`, `validator_fail`, `compose_followups`). Thêm `last_usage: InvokeUsage` mặc định để P0 đo cost.

---

## 14. Files KHÔNG sửa logic (giữ tương thích)
- `app/graph/main_graph.py` + toàn bộ `app/graph/nodes/*` (trừ tách thuần `sql_pipeline.py` giữ public API) — fallback Strangler.
- `app/api/routes.py` — SSE/HTTP contract + harness chunk nesting (double-nest key `harness`).
- Test graph tuyến tính hiện có — chỉ thêm, không xóa.

---

## 15. Horizontal analysis — rủi ro coding
1. **Double-emit SSE**: tool adapter (build_chart/answer_composer) forward `sse_payload` — tránh subgraph progress double-emit (giống lưu ý Tech Spec 001 §12.1).
2. **Async lan tỏa**: P0 async đụng `openai_compatible.py`, `sql_executor.py`, `checkpointing.py`; giữ sync fallback (đừng xóa method sync).
3. **Tách `sql_pipeline.py` (1297 dòng)**: chỉ trích hàm, giữ tên export; chạy `test_sql_*` regression sau mỗi bước tách.
4. **Mask cột nhạy cảm** phải áp ở **output tool** (sau khi có rows), không chỉ ở SQL gen — đề phòng `SELECT *`.
5. **Cache key tenant-scoped**: tuyệt đối không chia sẻ cache giữa tenant (rò dữ liệu).
6. **IntentObject vào prompt** làm tăng token → đo ở P0 trước khi bật rộng.

---

## 16. Test strategy tổng & cách chạy (cho CODING_AGENT / codex)
- Mỗi phase: **unit của phase + E2E (`test_e2e_agentic_flow.py`) + regression toàn bộ `tests/`** — cả 3 xanh mới qua phase (khớp prompt 1-shot của Owner).
- Determinism: `conftest.py` (`SQL_EXECUTOR_MODE=stub`) + `FakeLlmClient` + `patch_pg_schema_v1` + `InMemorySemanticStore/Cache`. Không model/Spring/pgvector thật.
- Lệnh nền: `cd ai_python && python -m pytest tests -q`. FE khói (tùy chọn): `cd frontend/mini-erp && npm run test:e2e`.

---

## 17. Open Questions / GAP (truy vết)
- **OQ-1 / OQ-2** (blocker nhánh confirm thật): Spring endpoint POST confirm catalog / inventory draft? → OD-10 cho phép stub + TODO để không chặn run.
- **OQ-3**: pgvector đã bật chưa? Nếu chưa → `SEMANTIC_STORE_MODE=memory` (default), không blocker.
- **OQ-4**: K7/K8/K10 đã đủ nội dung wire chưa? Thiếu → degrade với asset tối thiểu (không blocker chạy).
- **GAP-1**: `last_usage`/cost từ FPT model có trả token thật không? Nếu provider không trả usage → P0 ước lượng bằng tokenizer cục bộ (ghi TODO).

---

> **Readiness**: **READY_WITH_RISKS** — 9 phase có contract cụ thể, file/slice/test rõ, mock determinism đầy đủ. Rủi ro được track: OQ-1/OQ-2 (confirm endpoint, stub), GAP-1 (usage từ provider). CODING_AGENT bắt đầu P0; thứ tự ưu tiên P0→P1→P3→P2→P4→P6→P5→P7→P8 (theo SRS-004 §13).
> **Next stage**: `QA_SPEC_WRITER` — viết test-case failing trước cho từng phase (TDD) dựa trên §3–§12.
