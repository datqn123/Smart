# IntentSubagent LLM Judge Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thay thế cây quyết định cứng trong `IntentSubagent` bằng một LLM call duy nhất trả về intent + mode + clarify_questions với full context (schema + query history + conversation).

**Architecture:** Single LLM Judge — LLM nhận toàn bộ context (ERP schema, query history gần nhất, conversation) và trả về `IntentAnalysisResult` chứa cả intent classification lẫn mode decision và contextual clarify questions. `decide()` method bị xóa; orchestrator đọc `intent.mode` trực tiếp. Heuristic fallback vẫn được giữ cho trường hợp LLM lỗi.

**Tech Stack:** Python 3.11+, Pydantic v2, existing `LlmClient.astructured_predict()`, pytest-asyncio

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `ai_python/app/harness/intent.py` | Modify | New schemas, `IntentContextBuilder`, updated `IntentSubagent` |
| `ai_python/app/harness/orchestrator.py` | Modify | Remove `decide()` call, use `intent.mode` trực tiếp |
| `ai_python/tests/fake_llm.py` | Modify | Handle `IntentAnalysisResult` schema name |
| `ai_python/tests/test_intent_object.py` | Modify | Update để dùng `IntentAnalysisResult` |
| `ai_python/tests/test_intent_confidence_thresholds.py` | Modify | Update schema references |

---

## Task 1: New Schemas trong `intent.py`

**Files:**
- Modify: `ai_python/app/harness/intent.py`

- [ ] **Step 1: Viết failing test cho `RequiredDataItem`**

```python
# ai_python/tests/test_intent_object.py — thêm vào đầu file test
def test_required_data_item_schema() -> None:
    from app.harness.intent import RequiredDataItem

    item = RequiredDataItem(field="revenue", source="orders", required=True, resolved=False)

    assert item.field == "revenue"
    assert item.source == "orders"
    assert item.required is True
    assert item.resolved is False
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```
cd ai_python && pytest tests/test_intent_object.py::test_required_data_item_schema -v
```
Expected: `ImportError: cannot import name 'RequiredDataItem'`

- [ ] **Step 3: Thêm `RequiredDataItem` và `IntentAnalysisResult` vào `intent.py`**

Thay thế `IntentObject`, `IntentObjectOutput`, và `IntentDecision` bằng:

```python
from typing import Literal

class RequiredDataItem(BaseModel):
    field: str
    source: str = ""        # bảng/entity cung cấp data này
    required: bool = True
    resolved: bool = False  # đã có trong context chưa


class IntentAnalysisResult(BaseModel):
    goal: str
    intent_type: str        # data_query | catalog_draft | inventory_draft | chart_report | chat
    required_data: list[RequiredDataItem] = Field(default_factory=list)
    resolved_entities: list[ResolvedEntity] = Field(default_factory=list)
    confidence: float = 0.0
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    # --- LLM judge fields ---
    mode: Literal["run", "clarify", "auto_assume"] = "run"
    clarify_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    reasoning: str = ""     # LLM tự lý giải quyết định (lightweight CoT)
    schema_refs: list[str] = Field(default_factory=list)  # bảng LLM đã tham chiếu


# Backward-compat aliases — orchestrator và tests cũ dùng tên cũ
IntentObject = IntentAnalysisResult
IntentObjectOutput = IntentAnalysisResult
IntentDecision = IntentAnalysisResult
```

> **Note:** Alias `IntentDecision = IntentAnalysisResult` cho phép orchestrator hiện tại (`intent_decision.mode`, `intent_decision.clarify_questions`) không cần thay đổi trong task này.

- [ ] **Step 4: Chạy test**

```
cd ai_python && pytest tests/test_intent_object.py::test_required_data_item_schema -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/intent.py ai_python/tests/test_intent_object.py
git commit -m "feat(intent): add RequiredDataItem and IntentAnalysisResult unified schema"
```

---

## Task 2: `IntentContextBuilder` và `IntentContext`

**Files:**
- Modify: `ai_python/app/harness/intent.py`

- [ ] **Step 1: Viết failing test**

```python
# ai_python/tests/test_intent_object.py — thêm
def test_intent_context_builder_assembles_blocks() -> None:
    from app.harness.intent import IntentContextBuilder

    builder = IntentContextBuilder()
    ctx = builder.build(
        schema_text="Table: orders(id, total, created_at)",
        history_text="Q: doanh thu tháng 3 → SELECT SUM(total) FROM orders WHERE month=3",
        memory_text="User asked about revenue",
    )

    assert "orders" in ctx.schema_text
    assert "SELECT" in ctx.history_text
    assert "revenue" in ctx.memory_text
    assert ctx.to_prompt_blocks()  # returns non-empty string
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```
cd ai_python && pytest tests/test_intent_object.py::test_intent_context_builder_assembles_blocks -v
```
Expected: `ImportError: cannot import name 'IntentContextBuilder'`

- [ ] **Step 3: Thêm `IntentContext` và `IntentContextBuilder` vào `intent.py`**

Thêm sau phần `IntentAnalysisResult`:

```python
class IntentContext(BaseModel):
    schema_text: str = ""
    history_text: str = ""
    memory_text: str = ""

    def to_prompt_blocks(self) -> str:
        parts: list[str] = []
        if self.schema_text:
            parts.append(f"[SCHEMA]\n{self.schema_text}")
        if self.history_text:
            parts.append(f"[QUERY HISTORY]\n{self.history_text}")
        if self.memory_text:
            parts.append(f"[CONVERSATION]\n{self.memory_text}")
        return "\n\n".join(parts)


class IntentContextBuilder:
    def build(
        self,
        *,
        schema_text: str = "",
        history_text: str = "",
        memory_text: str = "",
    ) -> IntentContext:
        return IntentContext(
            schema_text=schema_text,
            history_text=history_text,
            memory_text=memory_text,
        )
```

- [ ] **Step 4: Chạy test**

```
cd ai_python && pytest tests/test_intent_object.py::test_intent_context_builder_assembles_blocks -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/intent.py ai_python/tests/test_intent_object.py
git commit -m "feat(intent): add IntentContext and IntentContextBuilder"
```

---

## Task 3: Update `IntentSubagent.analyze()` — LLM nhận full context

**Files:**
- Modify: `ai_python/app/harness/intent.py`

- [ ] **Step 1: Viết failing test**

```python
# ai_python/tests/test_intent_object.py — thêm
@pytest.mark.asyncio
async def test_intent_subagent_uses_full_context() -> None:
    from app.harness.intent import IntentAnalysisResult, IntentContextBuilder, IntentSubagent

    captured_messages: list = []

    class CapturingClient:
        last_usage = None

        async def astructured_predict(self, messages, schema, **kwargs):
            captured_messages.extend(messages)
            return schema.model_validate({
                "goal": "Xem doanh thu",
                "intent_type": "data_query",
                "required_data": [{"field": "revenue", "source": "orders", "required": True, "resolved": False}],
                "confidence": 0.95,
                "mode": "run",
                "clarify_questions": [],
                "assumptions": [],
                "reasoning": "User asked about revenue clearly",
                "schema_refs": ["orders"],
            })

    class Registry:
        def get(self, role):
            return CapturingClient()

    ctx = IntentContextBuilder().build(
        schema_text="Table: orders(id, total)",
        history_text="Q: doanh thu → SELECT SUM(total) FROM orders",
        memory_text="prev: hỏi về doanh thu",
    )

    agent = IntentSubagent(llm_registry=Registry(), settings=_settings())
    result = await agent.analyze("doanh thu tháng này", intent_context=ctx)

    assert isinstance(result, IntentAnalysisResult)
    assert result.mode == "run"
    assert result.reasoning
    # Verify context was injected into prompt
    prompt_text = " ".join(str(m) for m in captured_messages)
    assert "orders" in prompt_text
    assert "SELECT" in prompt_text
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```
cd ai_python && pytest tests/test_intent_object.py::test_intent_subagent_uses_full_context -v
```
Expected: FAIL — `analyze()` chưa nhận `intent_context` param

- [ ] **Step 3: Update `IntentSubagent.analyze()` trong `intent.py`**

Thay thế method `analyze()` hiện tại:

```python
async def analyze(
    self,
    question: str,
    memory_text: str = "",
    dictionary_text: str = "",  # kept for backward compat — ignored
    intent_context: "IntentContext | None" = None,
) -> IntentAnalysisResult:
    ctx = intent_context or IntentContext(memory_text=memory_text)
    prompt_blocks = ctx.to_prompt_blocks()

    if self._llm_registry is None:
        return self._heuristic(question)
    client = self._llm_registry.get("intent")
    try:
        return await client.astructured_predict(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an intent analysis expert for a Vietnamese ERP system. "
                        "Analyze the user's request using the context below and return a structured result. "
                        "Decide the mode: 'run' if you have enough info, 'clarify' if critical info is missing, "
                        "'auto_assume' if you can make safe assumptions. "
                        "Write contextual clarify_questions in Vietnamese if mode='clarify'. "
                        "Write a 1-2 sentence reasoning explaining your decision.\n\n"
                        f"{prompt_blocks}"
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            IntentAnalysisResult,
        )
    except Exception:
        return self._heuristic(question)
```

- [ ] **Step 4: Update `_heuristic()` để trả về `IntentAnalysisResult`**

```python
@staticmethod
def _heuristic(question: str) -> IntentAnalysisResult:
    text = (question or "").lower()
    if any(token in text for token in ("tạo sản phẩm", "tạo danh mục", "catalog")):
        intent_type = "catalog_draft"
    elif any(token in text for token in ("nhập kho", "xuất kho", "tạo phiếu")):
        intent_type = "inventory_draft"
    elif any(token in text for token in ("biểu đồ", "chart", "vẽ")):
        intent_type = "chart_report"
    elif any(token in text for token in ("doanh thu", "tồn kho", "báo cáo", "công nợ")):
        intent_type = "data_query"
    else:
        intent_type = "chat"
    return IntentAnalysisResult(
        goal=question or intent_type,
        intent_type=intent_type,
        required_data=[],
        confidence=0.9,
        mode="run",
        reasoning="heuristic fallback",
    )
```

- [ ] **Step 5: Xóa `decide()` method khỏi `IntentSubagent`**

Xóa toàn bộ method `decide()` (lines 112–142 trong file gốc). LLM đã handle logic này.

- [ ] **Step 6: Xóa các helper functions không còn dùng**

Xóa `_missing_question()`, `_low_confidence_question()`, `_entity_question()`, `_float_setting()` khỏi cuối file.

- [ ] **Step 7: Chạy test**

```
cd ai_python && pytest tests/test_intent_object.py::test_intent_subagent_uses_full_context -v
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add ai_python/app/harness/intent.py
git commit -m "feat(intent): replace heuristic decide() with LLM judge in analyze()"
```

---

## Task 4: Update `fake_llm.py` để handle `IntentAnalysisResult`

**Files:**
- Modify: `ai_python/tests/fake_llm.py`

- [ ] **Step 1: Thêm `intent_mode` param và handler mới**

Trong `FakeLlmClient.__init__()`, thêm param:

```python
intent_mode: str = "run",
```

Và trong `self._...` assignments:

```python
self._intent_mode = intent_mode
```

- [ ] **Step 2: Thêm handler cho `IntentAnalysisResult` trong `structured_predict()`**

Thêm block này **trước** block `IntentObjectOutput` hiện tại:

```python
if schema.__name__ == "IntentAnalysisResult":
    intent_val = self._intent if self._intent is not None else "data_query"
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
            "mode": self._intent_mode if not self._intent_missing else "clarify",
            "clarify_questions": (
                ["Bạn muốn xem trong khoảng thời gian nào?"]
                if self._intent_missing
                else []
            ),
            "assumptions": [],
            "reasoning": "fake reasoning",
            "schema_refs": ["orders"],
        }
    )
```

Giữ block `IntentObjectOutput` cũ **nguyên vẹn** (backward compat cho tests chưa migrate).

- [ ] **Step 3: Chạy existing intent tests**

```
cd ai_python && pytest tests/test_intent_object.py tests/test_intent_confidence_thresholds.py -v
```
Expected: Tất cả PASS (backward compat aliases đảm bảo điều này)

- [ ] **Step 4: Commit**

```bash
git add ai_python/tests/fake_llm.py
git commit -m "test(fake_llm): add IntentAnalysisResult handler with intent_mode param"
```

---

## Task 5: Update `orchestrator.py` — bỏ `decide()` call

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py`

- [ ] **Step 1: Viết failing test**

```python
# ai_python/tests/test_intent_confidence_thresholds.py — thêm
@pytest.mark.asyncio
async def test_intent_llm_judge_mode_run_executes() -> None:
    from app.harness.orchestrator import FinalAnswerEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from langchain_core.messages import HumanMessage
    from tests.fake_llm import FakeLlmClient

    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(FakeLlmClient(intent="data_query", intent_confidence=0.95, intent_mode="run")),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )

    events = [
        event
        async for event in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="doanh thu")]),
            _ctx(),
        )
    ]

    assert any(isinstance(e, FinalAnswerEvent) for e in events)
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_intent_llm_judge_mode_run_executes -v
```
Expected: FAIL — orchestrator vẫn gọi `decide()` không còn tồn tại

- [ ] **Step 3: Update orchestrator tại lines 219–243**

Tìm đoạn:

```python
intent_decision = intent_agent.decide(intent)
if intent_decision.mode == "clarify":
    yield ClarifyEvent(
        questions=intent_decision.clarify_questions,
        ...
    )
    return
ctx = replace(
    ctx,
    intent_object=intent.model_dump(mode="json"),
    assumptions=list(intent_decision.assumptions),
)
```

Thay bằng (bỏ `decide()`, dùng `intent` trực tiếp):

```python
if intent.mode == "clarify":
    yield ClarifyEvent(
        questions=intent.clarify_questions,
        suggested_rewrite="",
        original_question=self._original_question(scratchpad),
    )
    return
ctx = replace(
    ctx,
    intent_object=intent.model_dump(mode="json"),
    assumptions=list(intent.assumptions),
)
```

- [ ] **Step 4: Chạy tất cả intent tests**

```
cd ai_python && pytest tests/test_intent_object.py tests/test_intent_confidence_thresholds.py -v
```
Expected: Tất cả PASS

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_intent_confidence_thresholds.py
git commit -m "refactor(orchestrator): remove decide() call, read intent.mode directly from LLM result"
```

---

## Task 6: Migrate existing tests sang `IntentAnalysisResult`

**Files:**
- Modify: `ai_python/tests/test_intent_object.py`

- [ ] **Step 1: Update `test_intent_high_confidence_runs`**

```python
def test_intent_high_confidence_runs() -> None:
    from app.harness.intent import IntentAnalysisResult

    # LLM đã set mode="run", không cần decide()
    intent = IntentAnalysisResult(
        goal="Xem doanh thu",
        intent_type="data_query",
        required_data=[],
        confidence=0.95,
        mode="run",
    )

    assert intent.mode == "run"
```

- [ ] **Step 2: Update `test_intent_missing_required_clarifies`**

```python
def test_intent_missing_required_clarifies() -> None:
    from app.harness.intent import IntentAnalysisResult

    # LLM trả về mode="clarify" với contextual question
    intent = IntentAnalysisResult(
        goal="Xem báo cáo",
        intent_type="data_query",
        required_data=[],
        confidence=0.95,
        mode="clarify",
        clarify_questions=["Bạn muốn xem trong khoảng thời gian nào?"],
    )

    assert intent.mode == "clarify"
    assert intent.clarify_questions
    assert "thời gian" in intent.clarify_questions[0].lower()
```

- [ ] **Step 3: Update `test_intent_mid_confidence_auto_assume`**

```python
def test_intent_mid_confidence_auto_assume() -> None:
    from app.harness.intent import IntentAnalysisResult

    intent = IntentAnalysisResult(
        goal="Xem tồn kho",
        intent_type="data_query",
        required_data=[],
        confidence=0.8,
        mode="auto_assume",
        assumptions=["Tôi sẽ xử lý theo khoảng thời gian gần nhất."],
    )

    assert intent.mode == "auto_assume"
    assert intent.assumptions
```

- [ ] **Step 4: Update `test_intent_subagent_llm_output`**

```python
@pytest.mark.asyncio
async def test_intent_subagent_llm_output() -> None:
    from app.harness.intent import IntentAnalysisResult, IntentSubagent
    from tests.fake_llm import FakeLlmClient

    class Registry:
        def get(self, role: str):
            return FakeLlmClient(intent="data_query", intent_confidence=0.95)

    out = await IntentSubagent(llm_registry=Registry(), settings=_settings()).analyze(
        "doanh thu tháng này",
        memory_text="",
    )

    assert isinstance(out, IntentAnalysisResult)
    assert out.intent_type == "data_query"
    assert out.confidence == 0.95
    assert out.mode in ("run", "clarify", "auto_assume")
```

- [ ] **Step 5: Chạy toàn bộ test suite**

```
cd ai_python && pytest tests/test_intent_object.py tests/test_intent_confidence_thresholds.py -v
```
Expected: Tất cả PASS

- [ ] **Step 6: Commit**

```bash
git add ai_python/tests/test_intent_object.py
git commit -m "test(intent): migrate tests to IntentAnalysisResult, remove decide() assertions"
```

---

## Task 7: Cleanup — xóa backward-compat aliases và unused code

**Files:**
- Modify: `ai_python/app/harness/intent.py`

- [ ] **Step 1: Chạy full test suite trước để confirm baseline**

```
cd ai_python && pytest -v --tb=short 2>&1 | tail -20
```
Expected: Tất cả PASS

- [ ] **Step 2: Xóa aliases và dead code**

Trong `intent.py`, xóa:
- `IntentObject = IntentAnalysisResult` alias
- `IntentObjectOutput = IntentAnalysisResult` alias  
- `IntentDecision = IntentAnalysisResult` alias
- `_float_setting()` function (đã xóa ở Task 3 bước 6)

- [ ] **Step 3: Update imports trong `orchestrator.py`**

Tìm import line:
```python
from app.harness.intent import IntentSubagent, _intent_key_from
```
Đảm bảo không còn import `IntentObject`, `IntentDecision`, hay `IntentObjectOutput`.

- [ ] **Step 4: Chạy full test suite**

```
cd ai_python && pytest -v --tb=short 2>&1 | tail -30
```
Expected: Tất cả PASS, không có `ImportError`

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/intent.py ai_python/app/harness/orchestrator.py
git commit -m "cleanup(intent): remove backward-compat aliases after full migration"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Schema redesign (`IntentAnalysisResult`) — Task 1
- [x] `RequiredDataItem` structured field — Task 1
- [x] Context injection (schema + history + memory) — Task 2 + 3
- [x] LLM as judge (mode/clarify/auto_assume) — Task 3
- [x] `reasoning` field — Task 1 + 3
- [x] Remove heuristic decision tree — Task 3
- [x] `schema_refs` field — Task 1
- [x] Orchestrator updated — Task 5
- [x] Tests migrated — Task 6

**Placeholder scan:** Không có TBD/TODO

**Type consistency:**
- `IntentAnalysisResult` dùng nhất quán xuyên suốt Tasks 1–7
- `intent_context: IntentContext | None` param trong `analyze()` consistent với `IntentContextBuilder.build()` return type
- `FakeLlmClient(intent_mode=...)` consistent với handler trong Task 4

**Scope:** Đúng phạm vi — chỉ touch `intent.py`, `orchestrator.py` (2 lines), `fake_llm.py`, và tests.
