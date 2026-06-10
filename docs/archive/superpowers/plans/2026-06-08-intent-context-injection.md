# Intent Context Injection — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inject tool manifest (schema) và observations (query history) vào `IntentContext` trước khi gọi `IntentSubagent.analyze()` trong orchestrator, để LLM judge có đủ context quyết định `mode=run` thay vì clarify sai.

**Architecture:** Trong `orchestrator._dispatch()`, build `IntentContext` từ `self._tool_registry.tools_manifest_text()` (schema) + `scratchpad.observations` (query history) + `_memory_text()` (conversation), truyền vào `intent_agent.analyze(intent_context=ctx)`. Đồng thời fix `hitl` metric — set `True` khi ClarifyEvent phát sinh từ intent judge.

**Tech Stack:** Python 3.11+, Pydantic v2, existing `IntentContextBuilder`, existing `tools_manifest_text()`, existing `scratchpad.observations`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `ai_python/app/harness/orchestrator.py` | Modify | Build IntentContext, pass to analyze(), fix hitl metric |
| `ai_python/tests/test_intent_confidence_thresholds.py` | Modify | Add regression test for context injection |

---

## Task 1: Build IntentContext và inject vào analyze()

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py` (lines ~218–224)

- [ ] **Step 1: Viết failing test**

```python
# ai_python/tests/test_intent_confidence_thresholds.py — thêm
@pytest.mark.asyncio
async def test_intent_analyze_receives_tool_manifest_context() -> None:
    """Verify orchestrator injects tools_manifest_text as schema_text into analyze()."""
    from app.harness.intent import IntentAnalysisResult
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolManifest, ToolRegistry
    from langchain_core.messages import HumanMessage

    captured: list[dict] = []

    class CapturingClient:
        last_usage = None

        async def astructured_predict(self, messages, schema, **kwargs):
            # Capture the system message content
            for m in messages:
                if isinstance(m, dict) and m.get("role") == "system":
                    captured.append({"system": m["content"]})
                elif hasattr(m, "type") and m.type == "system":
                    captured.append({"system": m.content})
            return schema.model_validate({
                "goal": "test",
                "intent_type": "data_query",
                "required_data": [],
                "confidence": 0.95,
                "mode": "run",
                "clarify_questions": [],
                "assumptions": [],
                "reasoning": "test",
                "schema_refs": [],
            })

        def invoke_text(self, *a, **kw): return "ok"
        def stream_text(self, *a, **kw): return iter(["ok"])
        def structured_predict(self, messages, schema, **kwargs):
            import asyncio
            return asyncio.get_event_loop().run_until_complete(
                self.astructured_predict(messages, schema, **kwargs)
            )

    class Registry:
        def get(self, role): return CapturingClient()

    registry = ToolRegistry()
    registry.register(
        ToolManifest(name="sql_query", description="Run SQL queries", args_schema={}),
        impl=None,  # type: ignore[arg-type]
    )

    orchestrator = HarnessOrchestrator(
        llm_registry=Registry(),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )

    events = [
        event
        async for event in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="tồn kho sản phẩm A")]),
            _ctx(),
        )
    ]

    # The intent LLM call should have received a system message containing tool manifest
    assert captured, "No system message captured — intent_context not injected"
    assert any("sql_query" in c["system"] for c in captured), (
        "Tool manifest not found in system prompt — schema_text not injected"
    )
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_intent_analyze_receives_tool_manifest_context -v
```
Expected: FAIL — `AssertionError: Tool manifest not found in system prompt`

- [ ] **Step 3: Update orchestrator để build IntentContext**

Trong `orchestrator.py`, tìm đoạn (khoảng line 218–224):

```python
if bool(getattr(self._settings, "agentic_intent_object_enabled", False)):
    intent_agent = IntentSubagent(llm_registry=self._llm_registry, settings=self._settings)
    intent = await intent_agent.analyze(
        self._effective_question(scratchpad),
        memory_text=self._memory_text(scratchpad),
        dictionary_text="",
    )
```

Thay bằng:

```python
if bool(getattr(self._settings, "agentic_intent_object_enabled", False)):
    from app.harness.intent import IntentContextBuilder
    intent_agent = IntentSubagent(llm_registry=self._llm_registry, settings=self._settings)
    intent_ctx = IntentContextBuilder().build(
        schema_text=self._tool_registry.tools_manifest_text(),
        history_text=self._observations_text(scratchpad),
        memory_text=self._memory_text(scratchpad),
    )
    intent = await intent_agent.analyze(
        self._effective_question(scratchpad),
        intent_context=intent_ctx,
    )
```

- [ ] **Step 4: Thêm `_observations_text()` static method vào `HarnessOrchestrator`**

Thêm ngay sau `_memory_text()` (khoảng line 820):

```python
@staticmethod
def _observations_text(scratchpad: TurnScratchpad) -> str:
    if not scratchpad.observations:
        return ""
    parts = [
        f"- {obs.tool_name}: {obs.observation_text}"
        for obs in scratchpad.observations[-5:]
        if obs.ok and obs.observation_text
    ]
    return "\n".join(parts)
```

- [ ] **Step 5: Chạy test**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_intent_analyze_receives_tool_manifest_context -v
```
Expected: PASS

- [ ] **Step 6: Chạy full intent tests**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py tests/test_intent_object.py tests/test_agentic_integration.py -v 2>&1 | tail -20
```
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_intent_confidence_thresholds.py
git commit -m "feat(orchestrator): inject tool manifest and observations into IntentContext for LLM judge"
```

---

## Task 2: Fix `hitl` metric khi ClarifyEvent phát sinh từ intent judge

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py` (lines ~231–237)

- [ ] **Step 1: Viết failing test**

```python
# ai_python/tests/test_intent_confidence_thresholds.py — thêm
@pytest.mark.asyncio
async def test_intent_clarify_sets_hitl_true_in_metrics() -> None:
    """When intent judge returns mode=clarify, turn metrics must record hitl=True."""
    from app.harness.observability import TraceRecorder
    from app.harness.orchestrator import ClarifyEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry
    from langchain_core.messages import HumanMessage
    from tests.fake_llm import FakeLlmClient

    recorder = TraceRecorder()
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(FakeLlmClient(intent="data_query", intent_missing=["time_period"])),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
    )

    events = [
        event
        async for event in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="báo cáo bán hàng")]),
            _ctx(),
            recorder=recorder,
        )
    ]

    clarify_events = [e for e in events if isinstance(e, ClarifyEvent)]
    assert clarify_events, "Expected ClarifyEvent"
    assert recorder._hitl > 0, f"Expected hitl > 0, got {recorder._hitl}"
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_intent_clarify_sets_hitl_true_in_metrics -v
```
Expected: FAIL — `AssertionError: Expected hitl > 0, got 0`

- [ ] **Step 3: Kiểm tra `TraceRecorder` API**

```
cd ai_python && grep -n "hitl\|_hitl\|record_hitl" app/harness/observability.py | head -20
```

Note the method name for recording HITL. It's likely `record_hitl()` or incrementing `_hitl` directly.

- [ ] **Step 4: Thêm recorder.record_hitl() khi ClarifyEvent từ intent judge**

Trong `orchestrator.py`, tìm đoạn:

```python
if intent.mode == "clarify":
    yield ClarifyEvent(
        questions=intent.clarify_questions,
        suggested_rewrite="",
        original_question=self._original_question(scratchpad),
    )
    return
```

Thay bằng:

```python
if intent.mode == "clarify":
    if recorder is not None:
        recorder.record_hitl()
    yield ClarifyEvent(
        questions=intent.clarify_questions,
        suggested_rewrite="",
        original_question=self._original_question(scratchpad),
    )
    return
```

- [ ] **Step 5: Chạy test**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_intent_clarify_sets_hitl_true_in_metrics -v
```
Expected: PASS

- [ ] **Step 6: Chạy full test suite**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py tests/test_intent_object.py tests/test_agentic_integration.py -v 2>&1 | tail -20
```
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_intent_confidence_thresholds.py
git commit -m "fix(orchestrator): record hitl=True in metrics when intent judge emits ClarifyEvent"
```

---

## Self-Review

**Spec coverage:**
- [x] Build IntentContext với schema_text từ tools_manifest_text() — Task 1
- [x] Build IntentContext với history_text từ scratchpad.observations — Task 1
- [x] Truyền intent_context vào analyze() — Task 1
- [x] _observations_text() helper lấy 5 observations ok gần nhất — Task 1
- [x] Fix hitl metric khi ClarifyEvent từ intent judge — Task 2

**Placeholder scan:** Không có TBD/TODO.

**Type consistency:**
- `IntentContextBuilder().build(schema_text=..., history_text=..., memory_text=...)` — consistent với signature đã implement
- `_observations_text(scratchpad: TurnScratchpad) -> str` — consistent với `_memory_text(scratchpad)` pattern
- `recorder.record_hitl()` — cần verify tên method trong Task 2 Step 3 trước khi dùng

**Scope:** Minimal — chỉ 2 files, 2 tasks.
