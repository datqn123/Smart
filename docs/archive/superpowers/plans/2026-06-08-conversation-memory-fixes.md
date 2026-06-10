# Conversation Memory Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two issues in the conversation memory store: empty `ai_answer` when saving turns, and intent judge not leveraging cross-turn memory context for confidence decisions.

**Architecture:** Two independent fixes. (1) Save the LLM's final answer text into scratchpad before yielding `FinalAnswerEvent` so `_save_turn_to_memory` captures a non-empty `ai_answer`. Fall back to `observation_summary()` for edge cases. (2) Update the `IntentSubagent` system prompt to instruct the LLM to treat `[CONVERSATION]` context as known information when deciding intent mode.

**Tech Stack:** Python 3.12, Pydantic v2, LangChain messages, existing HarnessOrchestrator, existing IntentSubagent

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `ai_python/app/harness/orchestrator.py` | Modify | Add AI answer capture before final answer yields; update `_save_turn_to_memory` fallback |
| `ai_python/app/harness/intent.py` | Modify | Update intent subagent system prompt to leverage `[CONVERSATION]` |
| `ai_python/tests/test_conversation_memory_store.py` | Modify | Add/update test for non-empty `ai_answer` |
| `ai_python/tests/test_agentic_integration.py` | Modify | Add test verifying intent judge memory usage |

---

### Task 1: Fix ai_answer empty — capture final answer text

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py`

**Root cause:** The reactive loop and plan mode yield `FinalAnswerEvent` without adding an `AIMessage` to `scratchpad.messages`. `_save_turn_to_memory` iterates messages looking for an `AIMessage` and finds none → `ai_answer = ""`.

- [ ] **Step 1: Add `_ai_answer` fallback field to `__init__`**

Add after `self._turn_intent_key = ""` (line 140):

```python
        # Cached final answer for conversation memory ai_answer capture.
        self._ai_answer: str = ""
```

- [ ] **Step 2: Set `_ai_answer` before every `yield FinalAnswerEvent`**

There are 7 yield sites in `_dispatch` and `_run_plan_mode`. For each, set `self._ai_answer = text` right before `yield FinalAnswerEvent(text)`.

**Site 1 — line 281 (budget exhausted before step loop):**
```python
                    self._audit_warn(f"{exc.kind}_budget_exhausted", ctx)
                    self._ai_answer = scratchpad.observation_summary()
                    yield FinalAnswerEvent(scratchpad.observation_summary())
```

**Site 2 — line 290 (normal final_answer from planner decision):**
```python
                if decision.action == "final_answer":
                    self._ai_answer = decision.final_answer or ""
                    yield FinalAnswerEvent(decision.final_answer or "")
```

**Site 3 — lines 296-299 (clarify with no questions → answer directly):**
```python
                    if not questions:
                        self._ai_answer = decision.final_answer or ""
                        yield FinalAnswerEvent(decision.final_answer or "")
```

**Site 4 — line 322 (duplicate tool call short-circuit):**
```python
                    self._turn_degraded_reason = "duplicate"
                    self._ai_answer = scratchpad.observation_summary()
                    yield FinalAnswerEvent(scratchpad.observation_summary())
```

**Site 5 — line 338 (budget exhausted during tool call):**
```python
                    self._audit_warn(f"{exc.kind}_budget_exhausted", ctx)
                    self._ai_answer = scratchpad.observation_summary()
                    yield FinalAnswerEvent(scratchpad.observation_summary())
```

**Site 6 — line 370 (step budget exhausted):**
```python
            self._turn_degraded_reason = self._turn_degraded_reason or "step_budget"
            self._ai_answer = scratchpad.observation_summary()
            yield FinalAnswerEvent(scratchpad.observation_summary())
```

**For `_run_plan_mode` — line 557 (plan error):**
```python
                logger.warning("planner failed; falling back to reactive summary", exc_info=True)
                self._ai_answer = self._plan_error_answer(scratchpad)
                yield FinalAnswerEvent(self._plan_error_answer(scratchpad))
```

**For `_run_plan_mode` — line 627 (plan complete):**
```python
        self._turn_plan = plan
        if degraded_reason:
            self._turn_degraded_reason = degraded_reason
        self._ai_answer = final_text
        yield FinalAnswerEvent(final_text)
```

**For `_resume_hitl` — line 420 (HITL resume):**
```python
        scratchpad.add_observation(result, tool_name)
        self._ai_answer = result.observation_text
        yield FinalAnswerEvent(result.observation_text)
```

- [ ] **Step 3: Update `_save_turn_to_memory` to use `self._ai_answer`**

Replace the loop that searches for `AIMessage`:

Old code (lines 474-488):
```python
        # Extract user question and AI answer from scratchpad
        user_msg = ""
        ai_answer = ""
        for m in reversed(scratchpad.messages):
            content = str(getattr(m, "content", "") or "")
            from langchain_core.messages import HumanMessage, AIMessage
            if not ai_answer and isinstance(m, AIMessage) and content:
                ai_answer = content
            if not user_msg and isinstance(m, HumanMessage) and content:
                user_msg = content
                if ai_answer:
                    break

        if not user_msg:
            return
```

New code:
```python
        # Extract user question from scratchpad
        user_msg = ""
        for m in reversed(scratchpad.messages):
            content = str(getattr(m, "content", "") or "")
            from langchain_core.messages import HumanMessage
            if not user_msg and isinstance(m, HumanMessage) and content:
                user_msg = content
                break

        if not user_msg:
            return

        # Use cached final answer (set before each yield FinalAnswerEvent).
        ai_answer = self._ai_answer
```

- [ ] **Step 4: Run existing tests to verify nothing broken**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py tests/test_agentic_integration.py -v`
Expected: All pass (8 + 10 = 18 tests)

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/harness/orchestrator.py
git commit -m "fix(memory_store): capture final answer text before yielding FinalAnswerEvent"
```

---

### Task 2: Update test to verify ai_answer is non-empty

**Files:**
- Modify: `ai_python/tests/test_conversation_memory_store.py`

- [ ] **Step 1: Update `test_memory_saves_turn_after_dispatch`**

Add ai_answer assertion after the existing assertions:

```python
    assert ctx2.recent_turns[-1].ai_answer != "", (
        "ai_answer should not be empty after a completed turn"
    )
```

- [ ] **Step 2: Run test**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py::test_memory_saves_turn_after_dispatch -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add ai_python/tests/test_conversation_memory_store.py
git commit -m "test: verify ai_answer is non-empty after turn completion"
```

---

### Task 3: Fix intent judge prompt to leverage conversation memory

**Files:**
- Modify: `ai_python/app/harness/intent.py`

**Root cause:** The `[CONVERSATION]` block is rendered into the system prompt, but the prompt instructions don't explicitly tell the LLM to treat prior conversation context as known information for mode decisions. The LLM sees prior context but doesn't use it to increase confidence.

- [ ] **Step 1: Update the system prompt in `IntentSubagent.analyze()`**

In `ai_python/app/harness/intent.py`, line 152-159, update the system prompt to add instruction about using `[CONVERSATION]`:

Old:
```python
                        "content": (
                            "You are an intent analysis expert for a Vietnamese ERP system. "
                            "Analyze the user's request using the context below and return a structured result. "
                            "Decide the mode: 'run' if you have enough info, 'clarify' if critical info is missing, "
                            "'auto_assume' if you can make safe assumptions. "
                            "Write contextual clarify_questions in Vietnamese if mode='clarify'. "
                            "Write a 1-2 sentence reasoning explaining your decision.\n\n"
                            f"{prompt_blocks}"
                        ),
```

New:
```python
                        "content": (
                            "You are an intent analysis expert for a Vietnamese ERP system. "
                            "Analyze the user's request using the context below and return a structured result. "
                            "Decide the mode: 'run' if you have enough info, 'clarify' if critical info is missing, "
                            "'auto_assume' if you can make safe assumptions. "
                            "Write contextual clarify_questions in Vietnamese if mode='clarify'. "
                            "Write a 1-2 sentence reasoning explaining your decision.\n\n"
                            "IMPORTANT: The [CONVERSATION] section below shows prior turns. "
                            "If the current question is a follow-up referencing entities or data from "
                            "those prior turns, treat that context as already-known information — "
                            "do NOT ask for clarification about it. Use the prior context to "
                            "increase your confidence in 'run' or 'auto_assume' mode.\n\n"
                            f"{prompt_blocks}"
                        ),
```

- [ ] **Step 2: Run existing intent tests**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_intent_confidence_thresholds.py tests/test_intent_object.py -v`
Expected: All pass

- [ ] **Step 3: Run full memory + integration suite**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py tests/test_agentic_integration.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add ai_python/app/harness/intent.py
git commit -m "fix(intent): instruct intent judge to use [CONVERSATION] context for confidence"
```

---

### Task 4: Integration test — intent judge uses memory context

**Files:**
- Modify: `ai_python/tests/test_agentic_integration.py`

- [ ] **Step 1: Write integration test for intent judge leveraging memory**

Append to `ai_python/tests/test_agentic_integration.py`:

```python
@pytest.mark.asyncio
async def test_intent_judge_uses_memory_context_for_followup() -> None:
    """Verify the intent subagent uses [CONVERSATION] context to avoid clarifying
    on follow-up questions that reference prior-turn entities."""
    from app.harness.intent import IntentContextBuilder, IntentSubagent
    from tests.fake_llm import FakeLlmClient

    subagent = IntentSubagent(
        llm_registry=_Registry(FakeLlmClient(intent="data_query", intent_confidence=0.95)),
        settings=_settings(agentic_intent_object_enabled=True),
    )

    # Provide prior turn context about "tokboki"
    context = IntentContextBuilder().build(
        schema_text="",
        history_text="",
        memory_text=(
            "[Các lượt gần đây]\n"
            "Người dùng: tôi muốn xem sản phẩm tokboki\n"
            "Trợ lý: sản phẩm tokboki mã SP001, tồn 50"
        ),
    )

    result = await subagent.analyze(
        question="với tốc độ bán hiện tại thì bao lâu bán hết sản phẩm tokboki",
        intent_context=context,
    )
    # The prompt update should make the judge recognize this as a follow-up
    # and not require clarification about what "tokboki" is.
    assert result.mode != "clarify", (
        f"Intent judge should not clarify when memory context is available, "
        f"got mode={result.mode}, reasoning={result.reasoning}"
    )
```

- [ ] **Step 2: Run integration test**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_agentic_integration.py::test_intent_judge_uses_memory_context_for_followup -v`
Expected: PASS (if FakeLlmClient always returns data_query with mode=run)

- [ ] **Step 3: Run full suite**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py tests/test_agentic_integration.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add ai_python/tests/test_agentic_integration.py
git commit -m "test: verify intent judge uses conversation memory for follow-up questions"
```

---

### Task 5: Verify full test suite

- [ ] **Step 1: Run memory + integration + intent tests**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_conversation_memory_store.py tests/test_agentic_integration.py tests/test_intent_confidence_thresholds.py tests/test_intent_object.py -v`
Expected: All pass

- [ ] **Step 2: Run broader test suite (if applicable)**

Run: `cd ai_python && .venv\Scripts\python.exe -m pytest tests/test_agentic_integration.py tests/test_intent_confidence_thresholds.py tests/test_intent_object.py -v 2>&1 | Select-Object -Last 25`
Expected: All pass

---

## Self-Review

**Spec coverage:**
- Empty ai_answer (Issue 1) — Tasks 1-2 ✅
- Intent judge not leveraging memory (Issue 2) — Tasks 3-4 ✅
- Full verification — Task 5 ✅

**Placeholder scan:** No TBD/TODO patterns found.

**Type consistency:** `self._ai_answer: str` is a new instance variable; `_save_turn_to_memory` reads it after `self.last_metrics` is set in the finally block. The variable is set at every `yield FinalAnswerEvent` site and defaults to `""`.
