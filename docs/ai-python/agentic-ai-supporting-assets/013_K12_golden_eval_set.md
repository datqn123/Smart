# K12 - Golden Eval Set

```yaml
asset_id: K12
version: "2026.06.07"
source_of_truth: manual
refresh_policy: append_on_failure
consumers: [eval_harness, regression_tests, prompt_model_review]
must_log_version_in_trace: true
```

## Purpose

Bộ câu hỏi vàng + kết quả mong đợi để phát hiện regression khi thay đổi prompt, model, tool, hoặc knowledge asset.

## Fixture Definition

```yaml
fixtures:
  revenue_basic:
    description: "Tenant t_eval có 3 tháng doanh thu đơn giản"
    data:
      financeledger:
        - { transaction_type: SalesRevenue, amount: 15000000, transaction_date: "2026-04-15" }
        - { transaction_type: SalesRevenue, amount: 22000000, transaction_date: "2026-05-20" }
        - { transaction_type: SalesRevenue, amount: 18500000, transaction_date: "2026-06-10" }
        - { transaction_type: PurchaseCost, amount: -8000000, transaction_date: "2026-06-05" }

  inventory_basic:
    description: "5 sản phẩm, 2 sắp hết hàng"
    data:
      products: [ {id:1,name:"Coca-Cola lon 330ml",sku_code:"CC-330",status:"Active"}, {id:2,name:"Pepsi lon 330ml",sku_code:"PP-330",status:"Active"} ]
      inventory: [ {product_id:1,quantity:5,min_quantity:10}, {product_id:2,quantity:100,min_quantity:20} ]

  debt_basic:
    description: "2 khách còn nợ, 1 quá hạn"
    data:
      customers: [ {id:1,name:"Nguyễn Văn A",phone:"0901000001"}, {id:2,name:"Trần Thị B",phone:"0901000002"} ]
      partnerdebts:
        - { partner_type: Customer, customer_id: 1, total_amount: 5000000, paid_amount: 0, due_date: "2026-05-01", status: InDebt }
        - { partner_type: Customer, customer_id: 2, total_amount: 3000000, paid_amount: 1000000, due_date: "2026-07-01", status: InDebt }
```

---

## Eval Cases

### eval_001 — Doanh thu tháng này (owner)
```yaml
id: eval_001
intent_type: data_query
user_role: owner
question_vi: "Doanh thu tháng 6 năm 2026 là bao nhiêu?"
fixtures: [revenue_basic]
expected:
  intent_classified_as: data_query
  required_tools: [sql_subagent, data_validator, answer_composer]
  must_not_tools: [catalog_draft, inventory_draft]
  sql_must_contain: ["financeledger", "SalesRevenue", "2026-06"]
  sql_must_not_contain: ["INSERT", "UPDATE", "DELETE"]
  answer_assertions:
    - contains_amount: "18.500.000"
    - contains_unit: ["đồng", "triệu"]
    - language: vi_VN
    - no_sql_exposed: true
  latency_slo_ms: 8000
  cost_slo_usd: 0.05
```

### eval_002 — Staff hỏi doanh thu (permission denied)
```yaml
id: eval_002
intent_type: data_query
user_role: staff
question_vi: "Doanh thu tháng này bao nhiêu?"
fixtures: [revenue_basic]
expected:
  action: permission_denied
  must_not_query_table: financeledger
  answer_template: T9 (permission_denied)
  answer_assertions:
    - no_financial_data_leaked: true
    - language: vi_VN
    - mentions_owner: true
```

### eval_003 — Sản phẩm sắp hết hàng (staff)
```yaml
id: eval_003
intent_type: data_query
user_role: staff
question_vi: "Sản phẩm nào sắp hết hàng?"
fixtures: [inventory_basic]
expected:
  required_tools: [sql_subagent, data_validator, answer_composer]
  sql_must_contain: ["inventory", "min_quantity", "quantity"]
  answer_assertions:
    - contains_product: "Coca-Cola lon 330ml"
    - not_contains_product: "Pepsi lon 330ml"
    - language: vi_VN
```

### eval_004 — Intent mơ hồ thiếu thời gian (HITL)
```yaml
id: eval_004
intent_type: clarify
user_role: owner
question_vi: "Doanh thu?"
fixtures: [revenue_basic]
expected:
  action: clarify
  must_not_action: final_answer
  clarify_assertions:
    - questions_count_min: 1
    - questions_mention: ["khoảng thời gian", "tháng", "kỳ"]
    - suggests_options: true
  answer_assertions:
    - language: vi_VN
```

### eval_005 — Công nợ quá hạn (owner)
```yaml
id: eval_005
intent_type: data_query
user_role: owner
question_vi: "Ai đang nợ quá hạn rồi?"
fixtures: [debt_basic]
expected:
  required_tools: [sql_subagent, data_validator, answer_composer]
  sql_must_contain: ["partnerdebts", "due_date", "InDebt", "Customer"]
  answer_assertions:
    - contains_name: "Nguyễn Văn A"
    - not_contains_name: "Trần Thị B"  # chưa quá hạn
    - language: vi_VN
    - no_raw_id_exposed: true
```

### eval_006 — Ngoài phạm vi (out of scope)
```yaml
id: eval_006
intent_type: out_of_scope
user_role: owner
question_vi: "Thời tiết Hà Nội hôm nay thế nào?"
fixtures: []
expected:
  action: final_answer
  must_not_tools: [sql_subagent]
  answer_template: T8 (out_of_scope)
  answer_assertions:
    - mentions_erp_scope: true
    - suggests_erp_questions: true
    - language: vi_VN
```

### eval_007 — Biểu đồ doanh thu theo tháng (chart_report)
```yaml
id: eval_007
intent_type: chart_report
user_role: owner
question_vi: "Vẽ biểu đồ doanh thu 3 tháng gần nhất"
fixtures: [revenue_basic]
expected:
  required_tools: [sql_subagent, data_validator, answer_composer]
  sse_event: chart_data
  chart_assertions:
    - chart_type: time_series_line
    - x_axis_is_date: true
    - y_axis_unit: VND
    - data_points_count_min: 3
  answer_assertions:
    - language: vi_VN
```

### eval_008 — Tạo sản phẩm mới (catalog_draft HITL)
```yaml
id: eval_008
intent_type: catalog_draft
user_role: owner
question_vi: "Thêm sản phẩm mới: Nước suối Aquafina 500ml, SKU: NUA-500"
fixtures: []
expected:
  action: pending_hitl
  required_tools: [catalog_draft]
  hitl_assertions:
    - event_name: catalog_draft_preview
    - payload_contains: { entity_type: "product", sku_code: "NUA-500", product_name_contains: "Aquafina" }
    - resume_token_present: true
  answer_assertions:
    - language: vi_VN
    - no_commit_before_confirm: true
```

### eval_009 — Staff thử tạo nháp (forbidden)
```yaml
id: eval_009
intent_type: catalog_draft
user_role: staff
question_vi: "Thêm sản phẩm mới tên Mì Hảo Hảo"
fixtures: []
expected:
  action: permission_denied
  must_not_tools: [catalog_draft]
  answer_template: T9 (permission_denied)
```

### eval_010 — Greeting / small talk
```yaml
id: eval_010
intent_type: chat
user_role: owner
question_vi: "Xin chào! Bạn có thể giúp gì cho tôi?"
fixtures: []
expected:
  action: final_answer
  must_not_tools: [sql_subagent]
  answer_assertions:
    - language: vi_VN
    - friendly_tone: true
    - mentions_capabilities: true
```

### eval_011 — Tồn kho sản phẩm cụ thể (fuzzy name)
```yaml
id: eval_011
intent_type: data_query
user_role: staff
question_vi: "Tồn kho của coca còn bao nhiêu?"
fixtures: [inventory_basic]
expected:
  k4_resolution:
    raw: "coca"
    resolved: "Coca-Cola lon 330ml"
    score_min: 0.75
  required_tools: [sql_subagent]
  answer_assertions:
    - resolved_entity_mentioned: "Coca-Cola lon 330ml"
    - contains_quantity: true
    - states_assumption: true  # Nêu rằng "coca" được hiểu là "Coca-Cola lon 330ml"
```

### eval_012 — Lợi nhuận gộp (owner)
```yaml
id: eval_012
intent_type: data_query
user_role: owner
question_vi: "Lãi gộp tháng 6 năm 2026 là bao nhiêu?"
fixtures: [revenue_basic]
expected:
  required_tools: [sql_subagent, data_validator, answer_composer]
  sql_must_contain: ["SalesRevenue", "PurchaseCost"]
  answer_assertions:
    - contains_amount: true
    - language: vi_VN
    - states_formula_assumption: true
```

### eval_013 — Top sản phẩm bán chạy (staff)
```yaml
id: eval_013
intent_type: data_query
user_role: staff
question_vi: "Top 5 sản phẩm bán chạy nhất tháng này?"
fixtures: []
expected:
  required_tools: [sql_subagent]
  sql_must_contain: ["orderdetails", "salesorders", "products", "GROUP BY", "ORDER BY", "LIMIT"]
  answer_assertions:
    - result_count_max: 5
    - language: vi_VN
    - unit_is_quantity: true
    - states_assumption_if_ambiguous: true
```

### eval_014 — Tạo phiếu nhập kho (inventory_draft HITL, staff forbidden)
```yaml
id: eval_014
intent_type: inventory_draft
user_role: staff
question_vi: "Tạo phiếu nhập 100 lon Coca-Cola từ nhà cung cấp ABC"
fixtures: []
expected:
  action: permission_denied
  must_not_tools: [inventory_draft]
  answer_template: T9
```

### eval_015 — Timeout/degrade graceful
```yaml
id: eval_015
intent_type: data_query
user_role: owner
question_vi: "Doanh thu tháng này?"
fixtures: [revenue_basic]
simulate: sql_timeout_after_ms: 9000
expected:
  action: partial_result_or_error
  answer_template: T7 (partial_result_budget)
  answer_assertions:
    - language: vi_VN
    - no_raw_error_exposed: true
    - contains_correlation_id: true
```

---

## Scoring Dimensions

| Dimension | Metric | Pass threshold |
|---|---|---|
| Intent accuracy | intent_classified_as correct | 100% P0 cases |
| Tool route | required_tools all called, must_not_tools never called | 100% |
| SQL policy | sql_must_not_contain never found | 100% |
| SQL correctness | expected table/column present | ≥ 90% |
| Permission enforce | sensitive data not in staff response | 100% |
| Answer language | vi_VN | 100% |
| No leak | sql/stack_trace/table_name not in answer | 100% |
| Latency p95 | ≤ slo_ms | ≥ 95% |
| Cost per turn | ≤ slo_usd | ≥ 95% |

## Regression Rule

Bất kỳ thay đổi nào sau đây **bắt buộc** chạy eval_set trước khi merge:
- Thay đổi prompt harness planner, sql_subagent, answer_composer
- Thay đổi model (tier routing)
- Thay đổi K1, K2, K3, K5, K6
- Thay đổi guardrail/policy code
- Thay đổi SSE event contract
