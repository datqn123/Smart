# QA Spec 002 (upgrade/ai-python): Hoàn thiện Agentic AI theo Target Design

- **SRS ref**: `docs/upgrade/ai-python/srs/004_agentic-ai-target-completion.md`
- **Tech Spec ref**: `docs/upgrade/ai-python/tech_lead/002_agentic-ai-target-completion.md`
- **Stage**: QA_SPEC_WRITER (test-driven-development)
- **Date**: 2026-06-07
- **Readiness**: **QA_READY_WITH_RISKS** (nhánh confirm draft thật phụ thuộc OQ-1/OQ-2 → test bằng stub; mọi phase khác QA_READY_FOR_CODING)

---

## 1. Nguyên tắc QA cho SRS-004

- **TDD**: với mỗi phase, viết test FAIL trước, code đến khi xanh.
- **3 lớp test mỗi phase** (gate qua phase): `unit phase` + `E2E (tests/test_e2e_agentic_flow.py)` + `regression toàn bộ tests/` (cờ agentic OFF).
- **Determinism tuyệt đối**: `conftest.py` (`SQL_EXECUTOR_MODE=stub`) + `FakeLlmClient` + `patch_pg_schema_v1` + `InMemorySemanticStore` + `InMemorySemanticCache`. KHÔNG model/Spring/pgvector thật.
- **Phân loại lỗi AI** (mọi test AI gắn nhãn): `logic-flow` | `guardrail` | `tool-integration` | `contract-drift`.

| Layer | Phạm vi |
| :-- | :-- |
| Unit | budget, intent, plan_graph, sql self-correct, data_validator, answer_composer, memory, compact, capability, model_router, cache, observability |
| Integration | orchestrator (intent gate + plan mode + budget) với stub tools |
| E2E | `test_e2e_agentic_flow.py` — full pipeline + HITL + regression-off |
| Regression | cờ `agentic_*_enabled=False` → hành vi loop 002/003 không đổi; SSE/HTTP contract |
| Ngoài phạm vi | Spring thật, FPT model thật, pgvector thật |

---

## 2. Fixtures & mock chung (bổ sung `tests/conftest.py` + `tests/fake_llm.py`)

```python
# tests/conftest.py — thêm
@pytest.fixture
def ctx_owner():
    from app.harness.tool_registry import TurnContext
    return TurnContext(tenant_id="t1", user_id="u1", thread_id="th1",
        correlation_id="c1", bearer_token=None, schema_version=None, role="owner")

@pytest.fixture
def ctx_staff(ctx_owner):
    from dataclasses import replace
    return replace(ctx_owner, role="staff")

@pytest.fixture
def mem_store():
    from app.harness.memory import InMemorySemanticStore
    return InMemorySemanticStore()

@pytest.fixture
def sem_cache():
    from app.harness.cache import InMemorySemanticCache
    return InMemorySemanticCache()
```

```python
# tests/fake_llm.py — thêm nhánh schema (tham số hoá qua __init__):
#   intent_confidence, intent_missing(list), intent_entity_score,
#   plan_nodes(list[dict]), validator_severity, compose_followups(int), compact_text
# và last_usage = InvokeUsage(prompt_tokens=50, completion_tokens=50, cost_usd=0.001)
# + async astructured_predict mirror structured_predict
def structured_predict(self, messages, schema, **kw):
    name = schema.__name__
    if name == "IntentObjectOutput":
        return schema.model_validate({
            "goal":"g","intent_type":self._intent or "data_query",
            "required_data":["revenue"], "confidence":self._intent_confidence,
            "resolved_entities":[{"raw":"x","matched":"y","score":self._intent_entity_score}],
            "missing_required": self._intent_missing or [], "ambiguities":[]})
    if name == "PlanGraphOutput":
        return schema.model_validate({"nodes": self._plan_nodes or [
            {"id":"n1","tool":"sql_query","needs":[],"input_spec":{},"output_expect":"rows"},
            {"id":"n2","tool":"sql_query","needs":[],"input_spec":{},"output_expect":"rows"},
            {"id":"n3","tool":"answer_composer","needs":["n1","n2"],"input_spec":{},"output_expect":"answer"}]})
    if name == "DataValidatorOutput":
        sev = self._validator_severity or "info"
        return schema.model_validate({"ok": sev!="fail","issues":[],"severity":sev})
    if name == "AnswerComposerOutput":
        return schema.model_validate({"answer_markdown":"Doanh thu: 100đ",
            "assumptions":[], "follow_ups":["Xem theo tuần?","So với tháng trước?"][:self._compose_followups or 2]})
    if name == "CompactOutput":
        return schema.model_validate({"compact_block": self._compact_text or "[COMPACT] tóm tắt phiên"})
    # ... giữ các nhánh cũ
```

---

## 3. Phase QP0 — Async + Budget + Token/Cost  (`tests/test_harness_budget.py`, `test_harness_async_contracts.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP0-01 | `test_budget_cost_stops_loop` | `cost_budget_usd=0.0025`, usage 0.001/step → loop dừng ≤ step 3; audit có `cost_budget_exhausted`; đúng 1 `FinalAnswerEvent` | guardrail |
| QP0-02 | `test_budget_token_stops_loop` | `harness_token_budget=120` → dừng khi `used_tokens>=120` | guardrail |
| QP0-03 | `test_budget_wallclock_stops_loop` | monkeypatch `time.monotonic` vượt `wallclock_timeout_s` → `wallclock_budget_exhausted` | guardrail |
| QP0-04 | `test_audit_records_tokens_cost_latency` | mỗi tool-call audit row có `tokens`,`cost_usd`,`latency_ms` | tool-integration |
| QP0-05 | `test_async_no_blocking_call` | `arun_tool` await được; loop chạy trong `asyncio.run` không deadlock | contract-drift |
| QP0-06 | `test_async_flag_off_keeps_legacy_bridge` | `agentic_async_enabled=False` → `test_harness_orchestrator.py` regression pass | regression |

```python
@pytest.mark.asyncio
async def test_budget_cost_stops_loop(ctx_owner):
    # LLM stub luôn call_tool; usage 0.001/step; budget 0.0025
    events = [e async for e in orchestrator.run(scratchpad, ctx_owner)]
    assert sum(isinstance(e, FinalAnswerEvent) for e in events) == 1
    assert orchestrator._last_budget_hit == "cost"
```

**E2E (tạo mới `tests/test_e2e_agentic_flow.py`)** — QP0-E2E: request đơn giản → loop → `final_answer` → SSE `done`; audit có tokens/cost/latency.

Lệnh: `python -m pytest tests/test_harness_budget.py tests/test_harness_async_contracts.py tests/test_e2e_agentic_flow.py tests -q`

---

## 4. Phase QP1 — IntentObject + Confidence + EntityResolver  (`tests/test_intent_object.py`, `test_intent_confidence_thresholds.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP1-01 | `test_intent_high_confidence_runs` | `intent_confidence=0.95` → `decide.mode=="run"` | logic-flow |
| QP1-02 | `test_intent_missing_required_clarifies` | `intent_missing=["time_period"]` → `mode=="clarify"`, questions≥1 | logic-flow |
| QP1-03 | `test_intent_low_entity_score_clarifies` | entity score 0.5 (< 0.6) → `mode=="clarify"` kèm options | logic-flow |
| QP1-04 | `test_intent_mid_confidence_auto_assume` | confidence 0.8 → `mode=="auto_assume"`, assumptions≥1 | logic-flow |
| QP1-05 | `test_clarify_questions_vietnamese` | mọi clarify question là tiếng Việt, kèm lý do | contract-drift |
| QP1-06 | `test_entity_resolver_fuzzy_fallback` | semantic_store rỗng → vẫn chấm điểm bằng fuzzy, không crash | tool-integration |
| QP1-07 | `test_intent_llm_error_fallback_heuristic` | `astructured_predict` raise → fallback `_quick_classify`, không vỡ turn | guardrail |
| QP1-08 | `test_intent_gate_clarify_emits_sse_clarify` | orchestrator gate `mode=clarify` → `ClarifyEvent` → SSE `clarify`, không vào loop | logic-flow |

**E2E**: QP1-E2E nhánh clarify (thiếu thời gian) phát `clarify` đúng.

Lệnh: `python -m pytest tests/test_intent_object.py tests/test_intent_confidence_thresholds.py tests/test_e2e_agentic_flow.py tests -q`

---

## 5. Phase QP2 — PlanGraph + Fan-out + Replan  (`tests/test_plan_graph.py`, `test_plan_parallel.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP2-01 | `test_plan_topo_order_respects_needs` | node có `needs` chạy sau dependency | logic-flow |
| QP2-02 | `test_independent_nodes_run_concurrently` | 2 node không needs → `concurrent_peak >= 2` (đếm trong fake tool dùng `asyncio.Event`) | logic-flow |
| QP2-03 | `test_output_expect_fail_marks_node` | tool trả không khớp output_expect → `NodeResult.output_meets_expect=False` | tool-integration |
| QP2-04 | `test_replan_on_validator_fail` | validator fail n1 → planner trả plan v2 → execute pass; `replan_count==1` | logic-flow |
| QP2-05 | `test_replan_cap_degrades` | replan vượt `plan_replan_max` → best-effort answer, không loop vô hạn | guardrail |
| QP2-06 | `test_plan_dag_flag_off_uses_reactive_loop` | `agentic_plan_dag_enabled=False` → loop 002 reactive, regression pass | regression |

```python
@pytest.mark.asyncio
async def test_independent_nodes_run_concurrently():
    peak = {"v":0,"cur":0}
    # fake tool: cur+=1, peak=max; await asyncio.sleep(0); cur-=1
    results = await executor.execute(plan_2_independent_sql, ctx)
    assert peak["v"] >= 2
```

**E2E**: QP2-E2E bật plan_dag cho chart_report → 2 SQL song song → chart.

Lệnh: `python -m pytest tests/test_plan_graph.py tests/test_plan_parallel.py tests/test_e2e_agentic_flow.py tests -q`

---

## 6. Phase QP3 — SQL self-correct + DataValidator  (`tests/test_sql_self_correct_budget.py`, `test_data_validator.py`, giữ `test_sql_query_domain.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP3-01 | `test_sql_regen_within_budget` | `FakeLlmClient(sql_review_failures=2)` → regen 2 lần rồi pass; regen ≤ `sql_regen_max=3` | logic-flow |
| QP3-02 | `test_sql_empty_result_retry` | execute rỗng → retry ≤ `sql_empty_retry_max=2` rồi review lại | logic-flow |
| QP3-03 | `test_sql_dedup_short_circuits` | review trả cùng issue 2 lần (fingerprint trùng) → break, không lặp | guardrail |
| QP3-04 | `test_sql_degrade_returns_partial` | hết budget → `output.degraded=True`, observation có cảnh báo tiếng Việt, không raise | guardrail |
| QP3-05 | `test_sql_write_blocked_by_readonly` | SQL `UPDATE/DELETE/DROP` → bị chặn (policy + `enforce_read_only_sql`) | guardrail |
| QP3-06 | `test_validator_negative_value_fails` | rows có giá trị âm → `severity=="fail"`, `ok=False` | logic-flow |
| QP3-07 | `test_validator_missing_column_fails` | thiếu cột vs `required_data` → issues chứa `missing_column` | contract-drift |
| QP3-08 | `test_validator_pass_routes_to_composer` | rows hợp lệ → `ok=True` → pipeline tới answer_composer | logic-flow |

**E2E**: QP3-E2E SQL self-correct + validator pass trong pipeline.

Lệnh: `python -m pytest tests/test_sql_self_correct_budget.py tests/test_data_validator.py tests/test_sql_query_domain.py tests/test_e2e_agentic_flow.py tests -q`

---

## 7. Phase QP4 — AnswerComposer + chart + erp_guide  (`tests/test_answer_composer.py`, giữ `test_chart_pipeline.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP4-01 | `test_composer_has_followups` | output có 1–3 `follow_ups`, toàn tiếng Việt | contract-drift |
| QP4-02 | `test_composer_states_assumptions` | có assumptions từ intent auto_assume → render vào answer | logic-flow |
| QP4-03 | `test_composer_empty_rows_guidance` | rows rỗng → thông điệp hướng dẫn nhập chi tiết, không trả lời cụt | logic-flow |
| QP4-04 | `test_composer_emits_delta_full_sse` | `sse_payload._event=="delta_full"` | contract-drift |
| QP4-05 | `test_chart_type_by_shape` | time-series → `line`; phân bổ → `bar/pie` (K9) | tool-integration |
| QP4-06 | `test_erp_guide_tool_returns_observation` | erp_guide trả observation_text không rỗng | tool-integration |

**E2E**: QP4-E2E pipeline kết bằng answer_composer → `delta_full` chứa gợi ý + chart.

Lệnh: `python -m pytest tests/test_answer_composer.py tests/test_chart_pipeline.py tests/test_e2e_agentic_flow.py tests -q`

---

## 8. Phase QP5 — Memory 3 tầng + Compact + Persistence  (`tests/test_memory_tiers.py`, `test_checkpoint_persist.py`, giữ `test_context_compact.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP5-01 | `test_working_memory_keeps_n_pairs` | `working_memory_pairs=6` → giữ đúng 6 cặp gần nhất | logic-flow |
| QP5-02 | `test_compact_triggers_at_ratio` | ép ratio thấp → compact chạy, block bắt đầu `[COMPACT]` | logic-flow |
| QP5-03 | `test_compact_preserves_constraints` | compact giữ mốc thời gian/ràng buộc/kết quả quan trọng | contract-drift |
| QP5-04 | `test_semantic_store_recall_relevant` | `InMemorySemanticStore.recall` trả record liên quan top-k | tool-integration |
| QP5-05 | `test_semantic_store_no_raw_pii` | số điện thoại/email không được `upsert` (D6) | guardrail |
| QP5-06 | `test_hitl_resume_expired_returns_clear_error` | restart giả lập (store mới) → resume trả `HITL_EXPIRED`, không crash | guardrail |
| QP5-07 | `test_semantic_store_mode_memory_default` | `semantic_store_mode="memory"` → không kết nối pgvector | contract-drift |

**E2E**: QP5-E2E lượt 2 dùng working memory; HITL resume vẫn chạy.

Lệnh: `python -m pytest tests/test_memory_tiers.py tests/test_checkpoint_persist.py tests/test_context_compact.py tests/test_e2e_agentic_flow.py tests -q`

---

## 9. Phase QP6 — Capability/RBAC + mask + anti-injection + idempotency  (`tests/test_capability_rbac.py`, `test_anti_injection.py`, giữ `test_harness_policy.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP6-01 | `test_staff_cannot_see_cost_price` | role=staff + rows có `cost_price` → bị mask/từ chối, thông điệp "Bạn không có quyền..." | guardrail |
| QP6-02 | `test_owner_sees_sensitive_columns` | role=owner → thấy đủ cột nhạy cảm | guardrail |
| QP6-03 | `test_capability_blocks_write_sql_100pct` | mọi SQL ghi bị `HarnessPolicyError` qua capability guard (không chỉ substring) | guardrail |
| QP6-04 | `test_anti_injection_strips_embedded_instructions` | rows chứa "ignore previous instructions" → `sanitize_user_data` loại bỏ, hành vi không đổi | guardrail |
| QP6-05 | `test_tenant_scope_enforced` | tenant khác → policy chặn truy cập chéo | guardrail |
| QP6-06 | `test_idempotency_prevents_double_confirm` | double-submit cùng idempotency_key → mock Spring confirm chỉ gọi 1 lần | tool-integration |
| QP6-07 | `test_select_star_masks_sensitive_at_output` | `SELECT *` trả cột nhạy cảm → mask áp ở output (không chỉ ở SQL gen) | guardrail |

**E2E**: QP6-E2E owner full vs staff masked trên cùng câu hỏi.

Lệnh: `python -m pytest tests/test_capability_rbac.py tests/test_anti_injection.py tests/test_harness_policy.py tests/test_e2e_agentic_flow.py tests -q`

---

## 10. Phase QP7 — Model routing + Semantic cache  (`tests/test_model_router.py`, `test_semantic_cache.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP7-01 | `test_router_intent_uses_haiku` | `pick("intent")=="haiku"` | logic-flow |
| QP7-02 | `test_router_planner_uses_sonnet` | `pick("planner")=="sonnet"` | logic-flow |
| QP7-03 | `test_router_escalates_to_opus_on_replan` | `pick("sql", replan_count=2)=="opus"` | logic-flow |
| QP7-04 | `test_cache_hit_skips_tool` | 2 lượt cùng (tool+args+tenant) → lượt 2 `cache_hit`, tool gọi 1 lần | logic-flow |
| QP7-05 | `test_cache_tenant_isolation` | tenant khác cùng args → `cache_miss` (không rò dữ liệu) | guardrail |
| QP7-06 | `test_cache_only_deterministic_tools` | tool có side-effect/HITL không được cache | contract-drift |

Lệnh: `python -m pytest tests/test_model_router.py tests/test_semantic_cache.py tests/test_e2e_agentic_flow.py tests -q`

---

## 11. Phase QP8 — Observability + Eval golden  (`tests/test_observability.py` + `scripts/eval_golden.py`)

| ID | Test | Assert | Nhãn |
| :-- | :-- | :-- | :-- |
| QP8-01 | `test_turn_metrics_has_cost_latency_retry` | `TurnMetrics` có `tokens/cost_usd/latency_ms/replans` | contract-drift |
| QP8-02 | `test_audit_warns_on_budget_hit` | chạm trần → audit ghi `*_budget_exhausted` | guardrail |
| QP8-03 | `test_metrics_grouped_by_intent` | metrics tính được p50/p95 theo intent (mock nhiều turn) | logic-flow |
| QP8-04 | `test_eval_golden_offline_passes_subset` | `python scripts/eval_golden.py --offline` pass-rate ≥ `--min-pass` trên subset ≥10 câu | tool-integration |
| QP8-05 | `test_eval_detects_regression` | đổi prompt mock gây sai → eval báo fail | contract-drift |

Lệnh: `python -m pytest tests/test_observability.py tests/test_e2e_agentic_flow.py tests -q && python scripts/eval_golden.py --offline`

---

## 12. E2E tổng (`tests/test_e2e_agentic_flow.py` — đầy đủ sau QP8)

| ID | Test | Assert |
| :-- | :-- | :-- |
| E2E-01 | `test_full_chart_report_flow` | request doanh thu+tồn kho (owner) → intent run → plan 2 SQL song song → validator → chart → composer; SSE thứ tự `progress* → chart → delta_full(follow_ups) → done`; TurnMetrics có cost |
| E2E-02 | `test_hitl_draft_resume_flow` | "tạo sản phẩm" → `draft` (không `done`) → resume clarification → confirm (stub nếu OQ-10) → `final_answer` → `done` |
| E2E-03 | `test_clarify_then_answer_flow` | câu thiếu thời gian → `clarify` → lượt 2 trả lời → loop hoàn tất |
| E2E-04 | `test_all_flags_off_equals_legacy` | tắt mọi `agentic_*_enabled` → đi loop 002/003, kết quả như cũ (regression chính) |
| E2E-05 | `test_staff_masked_vs_owner_full` | cùng câu hỏi: staff bị mask cột nhạy cảm, owner full |

Lệnh tổng cuối: `cd ai_python && python -m pytest tests -q`. FE khói (tùy chọn, nếu server harness chạy): `cd frontend/mini-erp && npm run test:e2e`.

---

## 13. Failure-mode matrix (tổng hợp xuyên phase)

| Failure | Expected behavior | Test |
| :-- | :-- | :-- |
| Chạm token/cost/wallclock budget | best-effort `final_answer` từ observation + audit `*_budget_exhausted` | QP0-01..03 |
| Intent confidence thấp / thiếu param | `clarify` SSE, không vào loop | QP1-02,03,08 |
| IntentSubagent LLM lỗi | fallback heuristic, không vỡ turn | QP1-07 |
| Node DAG fail output_expect | mark fail → replan; vượt cap → degrade | QP2-03,04,05 |
| SQL review fail liên tục / rỗng | regen≤3 / retry≤2 → degrade trả partial | QP3-01,02,04 |
| SQL fingerprint trùng | dedup short-circuit | QP3-03 |
| SQL ghi | chặn 100% (capability + read-only) | QP3-05, QP6-03 |
| Data vô lý nghiệp vụ | validator fail → replan/clarify | QP3-06,07 |
| rows rỗng ở composer | thông điệp hướng dẫn tiếng Việt | QP4-03 |
| Context vượt 70% | compact `[COMPACT]` | QP5-02 |
| PII thô vào semantic | bị loại | QP5-05 |
| HITL resume hết hạn | `HITL_EXPIRED` rõ ràng, không crash | QP5-06 |
| staff xem cột nhạy cảm | mask/từ chối | QP6-01,07 |
| prompt-injection trong data | sanitize, hành vi không đổi | QP6-04 |
| double confirm draft | idempotency chặn nhân đôi | QP6-06 |
| cache cross-tenant | miss (isolation) | QP7-05 |
| đổi prompt gây sai | eval golden báo fail | QP8-05 |
| cờ agentic OFF | hành vi legacy 002/003 | QP2-06, E2E-04 |

---

## 14. Test execution checklist (gate cho codex)

- [ ] Mỗi phase QP0–QP8: unit phase XANH **và** `test_e2e_agentic_flow.py` XANH **và** `python -m pytest tests -q` XANH trước khi sang phase kế.
- [ ] E2E-04 (mọi cờ OFF = legacy) luôn xanh ở MỌI phase (chống regression Strangler).
- [ ] `fake_llm.py` có nhánh tất định cho mọi schema mới + `last_usage`.
- [ ] Không gọi model/Spring/pgvector thật trong bất kỳ test nào (grep `requests`/`httpx` thật trong test = fail review).
- [ ] `python scripts/eval_golden.py --offline` đạt `--min-pass` (mặc định 0.8).
- [ ] Không blocking call trên event loop (test async không deadlock).

---

> **Readiness**: **QA_READY_WITH_RISKS** — bộ test 9 phase (≈ 50 case) + 5 E2E + failure matrix đầy đủ + mock determinism. Rủi ro track: nhánh confirm draft thật (OQ-1/OQ-2) test bằng stub; GAP-1 (usage provider) test bằng `last_usage` giả định.
> **Next stage**: `CODING_AGENT` — implement theo Tech Spec 002, mỗi phase chạy bộ test QP tương ứng (TDD: viết test fail trước).
