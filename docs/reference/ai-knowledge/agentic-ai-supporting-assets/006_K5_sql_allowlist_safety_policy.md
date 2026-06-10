# K5 - SQL Allowlist And Safety Policy

```yaml
asset_id: K5
version: "2026.06.07"
source_of_truth: hybrid
refresh_policy: on_rbac_change
consumers: [guardrail, sql_subagent, sql_review, harness_policy]
must_log_version_in_trace: true
```

## Purpose

Định nghĩa chính xác SQL nào được phép sinh và thực thi trong luồng data_query/chart_report.

---

## Global Defaults

```yaml
defaults:
  sql_mode: read_only
  max_rows_returned: 500
  default_limit: 100
  inject_limit_if_missing: true
  max_runtime_ms: 8000
  deny_multi_statement: true          # Chặn nhiều câu SQL ngăn cách bởi ;
  require_tenant_scope: true          # Backend RLS enforce, Harness kiểm tra thêm
  allow_cte: true                     # WITH ... AS (...) SELECT được phép
  deny_nested_dml_in_cte: true        # WITH ... INSERT/UPDATE/DELETE bị chặn
  deny_system_tables: true            # pg_catalog, information_schema bị chặn
```

## Denied SQL Keywords (regex word-boundary)

```yaml
denied_keywords:
  - insert
  - update
  - delete
  - drop
  - truncate
  - alter
  - create
  - grant
  - revoke
  - execute
  - call
  - copy
  - vacuum
  - analyze        # chặn để tránh nhầm ANALYZE TABLE
```

## Denied Patterns

```yaml
denied_patterns:
  - pattern: "--.*?(ignore|disregard|forget|override).*?instruction"
    reason: "Prompt injection attempt via SQL comment"
  - pattern: "\/\*.*?(ignore|system|override).*?\*\/"
    reason: "Prompt injection via block comment"
  - pattern: "pg_sleep|pg_read_file|lo_read|dblink"
    reason: "Side-channel / file read functions"
  - pattern: "information_schema|pg_catalog|pg_tables|pg_class"
    reason: "System schema access via SQL"
  - pattern: "\\\\;"
    reason: "Multi-statement escape"
```

## Table & Column Permissions by Role

### owner — có thể đọc tất cả trừ system tables

```yaml
owner:
  allowed_tables: "*"                 # Tất cả bảng trong K1
  denied_tables:
    - systemlogs                      # Chỉ Admin xem
    - refresh_tokens
    - staffpasswordresetrequests
  column_overrides: {}                # Không có cột bị chặn thêm
```

### staff — đọc hạn chế, không đọc tài chính nhạy cảm

```yaml
staff:
  allowed_tables:
    - products
    - categories
    - productunits
    - productimages
    - inventory
    - warehouselocations
    - inventorylogs
    - stockreceipts
    - stockreceiptdetails
    - stockdispatches
    - salesorders
    - orderdetails
    - customers
    - suppliers
    - notifications
    - inventoryauditsessions
    - inventoryauditlines
    - ai_catalog_draft        # Chỉ xem nháp của chính mình (RLS ở Backend)
    - ai_inventory_draft      # Chỉ xem nháp của chính mình

  denied_tables:
    - financeledger           # Toàn bộ sổ cái tài chính
    - cashtransactions        # Thu chi
    - partnerdebts            # Công nợ
    - productpricehistory     # Giá vốn
    - storeprofiles           # Hồ sơ cửa hàng
    - aiinsights              # Dashboard AI
    - systemlogs
    - refresh_tokens
    - staffpasswordresetrequests

  denied_columns:
    products: []                      # Không có cột nhạy cảm trong products cho staff
    stockreceiptdetails:
      - cost_price
      - line_total
    salesorders:
      - discount_amount               # Staff không xem chiết khấu
```

## Enforcement Order

```
1. Harness Policy (pre-check): chặn keyword write trước khi gửi đến DB
2. SQL Guardrail (regex): kiểm tra denied_keywords + denied_patterns
3. Table/Column check: validate bảng/cột trong query khớp role
4. LIMIT injection: nếu không có LIMIT → inject LIMIT 100
5. Backend RLS: enforce tenant_id filter ở DB layer (last line of defense)
```

## Error Responses

```yaml
policy_block_user_message: >
  Trợ lý AI không thể thực hiện truy vấn này vì vượt quá phạm vi dữ liệu được phép.
  Vui lòng hỏi trong phạm vi báo cáo được hỗ trợ.

denied_table_user_message: >
  Bạn không có quyền xem thông tin này. Vui lòng liên hệ Owner để được hỗ trợ.

internal_trace: "Phải log rule_id và tool_name vào trace, KHÔNG expose ra user."
```

## Acceptance Checklist

- [ ] staff không thể query financeledger, partnerdebts, cashtransactions
- [ ] staff không thể đọc cost_price trong stockreceiptdetails
- [ ] Keyword write bị chặn bởi regex trước khi đến DB
- [ ] CTE SELECT được phép nhưng DML trong CTE bị chặn
- [ ] Tất cả SQL examples trong K7 pass policy này
- [ ] K6 RBAC matrix đồng nhất với allowed_tables ở đây
