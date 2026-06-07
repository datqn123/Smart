# K15 - Intent To Tool Success History

```yaml
asset_id: K15
version: "2026.06.07"
source_of_truth: generated_append_only
refresh_policy: append_after_every_turn
consumers: [planner, observability, eval_harness]
must_log_version_in_trace: true
```

## Purpose

Ghi lại kết quả mỗi turn để planner học theo plan đã hiệu quả và tránh lặp plan đã thất bại.

---

## Event Contract

```json
{
  "event_id": "uuid-v4",
  "created_at": "2026-06-07T10:30:00+07:00",
  "schema_version": "1.0",

  "context": {
    "tenant_hash": "sha256_of_tenant_id",
    "role": "owner",
    "correlation_id": "corr-abc123",
    "thread_id": "thread-xyz789"
  },

  "intent": {
    "intent_type": "data_query",
    "normalized_intent_key": "revenue_by_period",
    "confidence": 0.92,
    "hitl_triggered_for_intent": false
  },

  "plan": {
    "plan_graph_hash": "sha256_of_plan_dag",
    "tools_executed": ["sql_subagent", "data_validator", "answer_composer"],
    "parallel_branches": 0,
    "replan_count": 0,
    "hitl_count": 0
  },

  "sql": {
    "attempt_count": 1,
    "final_sql_fingerprint": "sha256_of_normalized_sql",
    "policy_blocks": 0,
    "review_failures": 0,
    "empty_result_retries": 0
  },

  "outcome": {
    "status": "success",
    "answer_template_used": "T1",
    "user_feedback": "accepted",
    "latency_ms": 4200,
    "cost_usd": 0.018,
    "token_count": 1850,
    "step_budget_used": 3,
    "budget_exhausted": false
  },

  "asset_versions": {
    "K1": "2026.06.07",
    "K2": "2026.06.07",
    "K3": "2026.06.07",
    "K5": "2026.06.07",
    "K7": "2026.06.07"
  },

  "failure_detail": null
}
```

---

## Failure Detail Schema (khi outcome.status != success)

```json
{
  "failure_detail": {
    "failure_stage": "sql_subagent",
    "failure_kind": "policy_block",
    "error_code": "HARNESS_POLICY_BLOCK",
    "sql_keyword_blocked": "DELETE",
    "replan_triggered": false,
    "fallback_used": "observation_summary",
    "degraded": false
  }
}
```

---

## Normalized Intent Key Catalog

Planner dùng key này để tra aggregate history. Key phải khớp với danh sách trong K8.

```yaml
valid_intent_keys:
  - revenue_by_period
  - revenue_by_channel
  - expense_by_period
  - gross_profit_by_period
  - net_cashflow_by_period
  - inventory_on_hand_all
  - inventory_on_hand_by_product
  - inventory_on_hand_by_category
  - low_stock_list
  - expiry_soon_list
  - top_products_by_quantity
  - top_products_by_revenue
  - customer_debt_balance
  - supplier_debt_balance
  - overdue_debt_list
  - order_count_by_status
  - order_count_by_channel
  - receipt_pending_list
  - stock_movement_by_product
  - catalog_draft_create
  - inventory_draft_create
  - schema_explore
  - chat_greeting
  - out_of_scope
  - permission_denied
```

---

## Planner Query Interface

Planner truy vấn aggregate history trước khi chọn plan:

```sql
-- Ví dụ: tìm plan route thành công nhất cho intent
SELECT
  plan_graph_hash,
  COUNT(*) FILTER (WHERE outcome_status = 'success') AS success_count,
  COUNT(*) AS total_count,
  AVG(latency_ms) AS avg_latency,
  AVG(cost_usd) AS avg_cost,
  AVG(replan_count) AS avg_replan
FROM k15_intent_history
WHERE normalized_intent_key = :intent_key
  AND role = :role
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY plan_graph_hash
ORDER BY success_count DESC, avg_latency ASC
LIMIT 3;
```

```sql
-- Kiểm tra plan hay bị policy block
SELECT plan_graph_hash, COUNT(*) AS block_count
FROM k15_intent_history
WHERE failure_kind = 'policy_block'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY plan_graph_hash
ORDER BY block_count DESC;
```

---

## Privacy Rules

```yaml
privacy:
  tenant_id: "Hash SHA-256 trước khi lưu — không lưu raw tenant_id"
  user_id: "Không lưu user_id — chỉ lưu role (owner/staff)"
  raw_question: "Không lưu câu hỏi gốc — chỉ lưu normalized_intent_key"
  raw_sql: "Không lưu SQL gốc — chỉ lưu fingerprint (hash) của SQL"
  pii: "Không lưu tên/phone/email trong bất kỳ field nào"
  raw_trace: "Lưu riêng trong observability store với retention policy ngắn hơn"
```

---

## Metrics Dashboard

| Metric | Cách tính | Alert khi |
|---|---|---|
| Success rate per intent | success_count / total | < 80% trong 24h |
| Avg latency p95 | percentile(latency_ms, 0.95) | > SLO theo K15.D8 |
| Avg cost per turn | AVG(cost_usd) | > $0.05 |
| HITL rate | hitl_count > 0 / total | > 30% (quá nhiều làm phiền user) |
| Replan rate | replan_count > 0 / total | > 20% (plan chất lượng thấp) |
| Policy block rate | failure_kind=policy_block / total | > 5% (prompt injection?) |
| Empty result rate | empty_result_retries > 0 / total | > 15% (K1/K7 cần cập nhật) |
| Budget exhausted rate | budget_exhausted=true / total | > 10% |

---

## Acceptance Checklist

- [ ] Event append sau mỗi turn hoàn tất (kể cả failed/degraded)
- [ ] PII không có trong bất kỳ field nào
- [ ] normalized_intent_key là key hợp lệ trong danh sách trên
- [ ] Planner có thể query aggregate mà không đọc raw trace
- [ ] asset_versions log đúng version K1-K7 đã dùng trong turn đó
- [ ] schema_version được tăng khi thêm field mới
