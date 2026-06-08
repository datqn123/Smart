# Code Review Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 confirmed bugs from code review: (1) list-valued JWT role claim silently drops implied capabilities, (2) ok=True/output_meets_expect=False incorrectly cascades to block all downstream nodes, (3) failed tool observations excluded from intent LLM context.

**Architecture:** Three independent single-file fixes. No shared state. Can be implemented in any order, but Task 1 (security) takes priority.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest-asyncio

---

## File Map

| File | Task | Change |
|------|------|--------|
| `ai_python/app/api/auth.py` | Task 1 | Fix `derive_role_permissions` to handle list-valued role claims |
| `ai_python/app/harness/plan_graph.py` | Task 2 | Separate `hard_failed` from `validation_failed` in PlanExecutor |
| `ai_python/app/harness/orchestrator.py` | Task 3 | Include failed observations in `_observations_text` |

---

## Task 1: Fix list-valued role claim in `derive_role_permissions`

**Files:**
- Modify: `ai_python/app/api/auth.py`
- Test: `ai_python/tests/test_v3_rbac_plumbing.py`

**Root cause:** `_read_claim(claims, ROLE_CLAIM_KEYS)` hits the `elif value is not None` branch for a list value and does `str(["admin"])` → `"['admin']"`. The `_ROLE_IMPLIED_CAPABILITIES` lookup for `"['admin']"` returns nothing.

**Fix:** Extract role separately using `_coerce_permission_flags`-style logic: if the role claim value is a list, take the first non-empty string element.

- [ ] **Step 1: Write the failing test**

```python
# ai_python/tests/test_v3_rbac_plumbing.py — thêm
def test_derive_role_permissions_list_valued_role_claim() -> None:
    """JWT roles=['admin'] (list) must grant the same implied caps as role='admin' (str)."""
    from app.api.auth import derive_role_permissions

    role, perms = derive_role_permissions({"roles": ["admin"]})

    assert role == "admin", f"Expected 'admin', got {role!r}"
    assert "draft_create" in perms, "Implied capability draft_create missing for list-valued admin role"
    assert "data_read" in perms, "Implied capability data_read missing for list-valued admin role"


def test_derive_role_permissions_list_valued_owner_claim() -> None:
    from app.api.auth import derive_role_permissions

    role, perms = derive_role_permissions({"roles": ["owner", "staff"]})

    # First element wins; owner implies same caps as admin
    assert role == "owner"
    assert "draft_create" in perms
    assert "data_read" in perms


def test_derive_role_permissions_string_role_unchanged() -> None:
    from app.api.auth import derive_role_permissions

    role, perms = derive_role_permissions({"role": "admin"})

    assert role == "admin"
    assert "draft_create" in perms
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd ai_python && pytest tests/test_v3_rbac_plumbing.py::test_derive_role_permissions_list_valued_role_claim tests/test_v3_rbac_plumbing.py::test_derive_role_permissions_list_valued_owner_claim -v
```
Expected: FAIL — `assert role == "admin"` fails because role is `"['admin']"`

- [ ] **Step 3: Fix `_read_claim` to handle list-valued claims**

In `ai_python/app/api/auth.py`, replace the `_read_claim` function (lines 120–131):

```python
def _read_claim(claims: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = claims.get(key)
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        elif isinstance(value, (list, tuple)):
            # Take the first non-empty string element (e.g. roles=["admin","staff"])
            for item in value:
                normalized = str(item).strip()
                if normalized:
                    return normalized
        elif value is not None:
            normalized = str(value).strip()
            if normalized:
                return normalized
    return None
```

- [ ] **Step 4: Run tests**

```
cd ai_python && pytest tests/test_v3_rbac_plumbing.py -v 2>&1 | tail -15
```
Expected: All PASS

- [ ] **Step 5: Run broader auth tests**

```
cd ai_python && pytest -k "auth or rbac or permission" -v 2>&1 | tail -20
```
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add ai_python/app/api/auth.py ai_python/tests/test_v3_rbac_plumbing.py
git commit -m "fix(auth): handle list-valued JWT role claims in _read_claim"
```

---

## Task 2: Separate hard_failed from validation_failed in PlanExecutor

**Files:**
- Modify: `ai_python/app/harness/plan_graph.py`
- Test: `ai_python/tests/test_v3_executor_guardrails.py`

**Root cause:** When a node has `ok=True` but `output_meets_expect=False`, it is added to `failed`. The FR-6 blocked-guard then cascades to skip all downstream dependents. A shape mismatch (unexpected output) should not block a write/draft tool the same way a hard tool failure does — it should trigger a replan but let the planner decide.

**Fix:** Introduce `hard_failed` set (ok=False) separate from `validation_failed` (ok=True, output_meets_expect=False). The FR-6 guardrail only blocks on `hard_failed`. Both contribute to `replan_required` observations.

- [ ] **Step 1: Write the failing test**

```python
# ai_python/tests/test_v3_executor_guardrails.py — thêm
@pytest.mark.asyncio
async def test_executor_validation_failed_does_not_block_dependents() -> None:
    """A node with ok=True but output_meets_expect=False should NOT cascade-block downstream nodes."""
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.tool_registry import ToolResult, TurnContext

    ctx = TurnContext(
        tenant_id="t1", user_id="u1", thread_id="th1",
        correlation_id="c1", bearer_token=None, schema_version=None,
    )

    call_log: list[str] = []

    class _Registry:
        def get_impl(self, name):
            async def _tool(args, ctx):
                call_log.append(name)
                if name == "node_a":
                    # ok=True but output doesn't match expectation (no 'rows' key)
                    return ToolResult(ok=True, output={"answer_markdown": "something"}, observation_text="ok")
                return ToolResult(ok=True, output={"rows": [{"v": 1}]}, observation_text="ok")
            return _tool

    plan = PlanGraph(nodes=[
        PlanNode(id="node_a", tool="node_a", needs=[], input_spec={}, output_expect="rows"),
        PlanNode(id="node_b", tool="node_b", needs=["node_a"], input_spec={}, output_expect="rows"),
    ])

    from app.harness.runtime import AgentHarness
    executor = PlanExecutor(
        tool_registry=_Registry(),
        harness=AgentHarness(enabled=False),
        policy=None,
    )
    results = await executor.execute(plan, ctx)

    # node_b MUST still execute even though node_a had output_meets_expect=False
    assert "node_b" in call_log, f"node_b was blocked by node_a's validation failure. call_log={call_log}"
    node_a_result = next(r for r in results if r.node_id == "node_a")
    node_b_result = next(r for r in results if r.node_id == "node_b")
    assert not node_a_result.ok or not node_a_result.output_meets_expect  # node_a had bad output
    assert node_b_result.ok  # node_b ran successfully


@pytest.mark.asyncio
async def test_executor_hard_failed_still_blocks_dependents() -> None:
    """A node with ok=False (hard failure) MUST still block all downstream dependents (FR-6)."""
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.tool_registry import ToolResult, TurnContext

    ctx = TurnContext(
        tenant_id="t1", user_id="u1", thread_id="th1",
        correlation_id="c1", bearer_token=None, schema_version=None,
    )

    call_log: list[str] = []

    class _Registry:
        def get_impl(self, name):
            async def _tool(args, ctx):
                call_log.append(name)
                if name == "node_a":
                    return ToolResult(ok=False, output={}, observation_text="hard error", error_message="hard error")
                return ToolResult(ok=True, output={"rows": []}, observation_text="ok")
            return _tool

    plan = PlanGraph(nodes=[
        PlanNode(id="node_a", tool="node_a", needs=[], input_spec={}, output_expect="rows"),
        PlanNode(id="node_b", tool="node_b", needs=["node_a"], input_spec={}, output_expect="rows"),
    ])

    from app.harness.runtime import AgentHarness
    executor = PlanExecutor(
        tool_registry=_Registry(),
        harness=AgentHarness(enabled=False),
        policy=None,
    )
    results = await executor.execute(plan, ctx)

    # node_b MUST NOT execute after node_a hard-failed
    assert "node_b" not in call_log, f"node_b ran after node_a hard-failed. call_log={call_log}"
    node_b_result = next(r for r in results if r.node_id == "node_b")
    assert not node_b_result.ok
    assert "skipped" in (node_b_result.error or "")
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd ai_python && pytest tests/test_v3_executor_guardrails.py::test_executor_validation_failed_does_not_block_dependents tests/test_v3_executor_guardrails.py::test_executor_hard_failed_still_blocks_dependents -v
```
Expected: First test FAILs (node_b blocked), second test may already PASS.

- [ ] **Step 3: Fix `execute()` in `plan_graph.py`**

In `ai_python/app/harness/plan_graph.py`, in `PlanExecutor.execute()`, replace:

```python
        succeeded: set[str] = set()
        failed: set[str] = set()
```

With:

```python
        succeeded: set[str] = set()
        hard_failed: set[str] = set()   # ok=False — blocks downstream (FR-6)
        validation_failed: set[str] = set()  # ok=True but output_meets_expect=False — triggers replan only
```

Replace the `blocked` guard (lines ~118-135):

```python
            # FR-6 / guardrail (P1-1): a node whose dependency HARD-FAILED must never run —
            # otherwise a write/draft tool could execute after a failed lookup or error.
            # Validation failures (ok=True but unexpected output shape) only trigger replan,
            # they do not cascade-block — the planner decides whether to retry or proceed.
            blocked = [
                node
                for node in plan.nodes
                if node.id in pending and any(dep in hard_failed for dep in node.needs)
            ]
            if blocked:
                for node in blocked:
                    results.append(
                        NodeResult(
                            node_id=node.id,
                            ok=False,
                            output_meets_expect=False,
                            error="skipped: dependency failed",
                        )
                    )
                    hard_failed.add(node.id)
                    pending.pop(node.id, None)
                continue
```

Replace the `ready` check:

```python
            ready = [
                node
                for node in plan.nodes
                if node.id in pending and all(dep in succeeded or dep in validation_failed for dep in node.needs)
            ]
```

Replace the result processing loop:

```python
            for result in layer_results:
                pending.pop(result.node_id, None)
                outputs[result.node_id] = result.tool_result if isinstance(result.tool_result, dict) else {}
                if result.ok and result.output_meets_expect:
                    succeeded.add(result.node_id)
                elif result.ok and not result.output_meets_expect:
                    # Validation failure: replan will fire via replan_required observation,
                    # but downstream nodes may still run (they'll receive outputs via data binding).
                    validation_failed.add(result.node_id)
                else:
                    hard_failed.add(result.node_id)
```

Also fix the cycle-detection break — use `hard_failed` instead of `failed`:

```python
            if not ready:
                for node_id in list(pending):
                    results.append(
                        NodeResult(
                            node_id=node_id,
                            ok=False,
                            output_meets_expect=False,
                            error="plan dependency cycle or missing dependency",
                        )
                    )
                    hard_failed.add(node_id)
                    pending.pop(node_id, None)
                break
```

- [ ] **Step 4: Run tests**

```
cd ai_python && pytest tests/test_v3_executor_guardrails.py -v
```
Expected: Both new tests PASS

- [ ] **Step 5: Run full harness tests**

```
cd ai_python && pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: All PASS (1 pre-existing failure unrelated to this change is OK)

- [ ] **Step 6: Commit**

```bash
git add ai_python/app/harness/plan_graph.py ai_python/tests/test_v3_executor_guardrails.py
git commit -m "fix(plan_graph): separate hard_failed from validation_failed — only hard failures cascade-block downstream nodes"
```

---

## Task 3: Include failed observations in `_observations_text`

**Files:**
- Modify: `ai_python/app/harness/orchestrator.py`
- Test: `ai_python/tests/test_intent_confidence_thresholds.py`

**Root cause:** `_observations_text` filters `obs.ok and obs.observation_text`, excluding all failed observations. When the LLM judge analyzes a follow-up turn after a failed tool, it sees no history and may classify the same intent, causing the same failure to repeat.

**Fix:** Include failed observations with a short failure note (tool name + "failed"). Keep the format compact so it doesn't bloat the system prompt.

- [ ] **Step 1: Write the failing test**

```python
# ai_python/tests/test_intent_confidence_thresholds.py — thêm
def test_observations_text_includes_failed_obs() -> None:
    """Failed observations must appear in _observations_text so intent LLM sees prior failures."""
    from app.harness.orchestrator import HarnessOrchestrator
    from app.harness.scratchpad import Observation, TurnScratchpad

    scratchpad = TurnScratchpad(messages=[])
    scratchpad.observations = [
        Observation(tool_name="sql_query", observation_text="table not found", ok=False),
        Observation(tool_name="answer_composer", observation_text="ok result", ok=True),
    ]

    text = HarnessOrchestrator._observations_text(scratchpad)

    assert "sql_query" in text, "Failed observation tool name must appear in history"
    assert "answer_composer" in text, "Successful observation must still appear"
```

- [ ] **Step 2: Run test to confirm it fails**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_observations_text_includes_failed_obs -v
```
Expected: FAIL — `assert "sql_query" in text` fails (failed obs filtered out)

- [ ] **Step 3: Fix `_observations_text` in `orchestrator.py`**

Find and replace the `_observations_text` static method:

```python
    @staticmethod
    def _observations_text(scratchpad: TurnScratchpad) -> str:
        if not scratchpad.observations:
            return ""
        parts = []
        for obs in scratchpad.observations[-5:]:
            if not obs.observation_text:
                continue
            if obs.ok:
                parts.append(f"- {obs.tool_name}: {obs.observation_text}")
            else:
                # Include failed tool name so intent LLM avoids repeating the same plan
                parts.append(f"- {obs.tool_name} (failed): {obs.observation_text}")
        return "\n".join(parts)
```

- [ ] **Step 4: Run test**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py::test_observations_text_includes_failed_obs -v
```
Expected: PASS

- [ ] **Step 5: Run full intent tests**

```
cd ai_python && pytest tests/test_intent_confidence_thresholds.py tests/test_intent_object.py -v
```
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add ai_python/app/harness/orchestrator.py ai_python/tests/test_intent_confidence_thresholds.py
git commit -m "fix(orchestrator): include failed observations in intent context so LLM judge sees prior failures"
```

---

## Self-Review

**Bug coverage:**
- [x] list-valued JWT role claim — Task 1
- [x] ok=True/output_meets_expect=False cascade-blocks downstream — Task 2
- [x] failed observations excluded from intent context — Task 3

**Placeholder scan:** Không có TBD/TODO.

**Type consistency:**
- `hard_failed: set[str]` / `validation_failed: set[str]` — consistent naming across Task 2 guards and result loop
- `_observations_text` return type `str` unchanged — consistent with `_memory_text` pattern
- `_read_claim` return type `str | None` unchanged — no signature change

**Scope:** Minimal — 3 files, 3 independent tasks.
