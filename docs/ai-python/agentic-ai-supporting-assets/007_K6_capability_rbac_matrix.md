# K6 - Capability / RBAC Matrix

```yaml
asset_id: K6
version: "2026.06.07"
source_of_truth: backend_auth
refresh_policy: on_rbac_change
consumers: [guardrail, harness, tool_registry, frontend_ai_access]
must_log_version_in_trace: true
```

## Purpose

Định nghĩa role nào được dùng capability nào trong AI assistant. Backend là nguồn sự thật; file này phản chiếu để harness enforce ở tầng application.

---

## Capability Matrix

### owner

```yaml
owner:
  prerequisite: "can_use_ai: true trong roles.permissions"
  capabilities:
    data_query:
      allowed: true
      sensitive_finance: true        # Được đọc financeledger, partnerdebts
      sensitive_cost: true           # Được đọc cost_price, giá vốn
      allowed_tables: "*"            # Theo K5 owner allowed_tables
    schema_explore:
      allowed: true
    chart_report:
      allowed: true
      sensitive_finance: true
    catalog_draft:
      allowed: true
      requires_hitl: true            # Bắt buộc HITL trước khi commit
      entity_types: [product, category, supplier, customer]
    inventory_draft:
      allowed: true
      requires_hitl: true
      entity_types: [stock_receipt]
    chat:
      allowed: true
    memory_read:
      allowed: true
    semantic_memory_write:
      allowed: true
    eval_run:
      allowed: false                 # Chỉ admin/dev
```

### staff

```yaml
staff:
  prerequisite: "can_use_ai: true trong roles.permissions"
  capabilities:
    data_query:
      allowed: true
      sensitive_finance: false       # Không được đọc financeledger, partnerdebts
      sensitive_cost: false          # Không được đọc cost_price
      allowed_tables: "xem K5 staff.allowed_tables"
    schema_explore:
      allowed: true
      scope: "non_sensitive_tables_only"
    chart_report:
      allowed: true
      sensitive_finance: false
    catalog_draft:
      allowed: false
      reason: "Staff không được tạo/sửa catalog qua AI"
    inventory_draft:
      allowed: false
      reason: "Staff không được tạo phiếu nhập qua AI"
    chat:
      allowed: true
    memory_read:
      allowed: true
    semantic_memory_write:
      allowed: false
    eval_run:
      allowed: false
```

### admin (system role)

```yaml
admin:
  capabilities:
    data_query:     { allowed: true,  sensitive_finance: true, sensitive_cost: true }
    schema_explore: { allowed: true }
    chart_report:   { allowed: true }
    catalog_draft:  { allowed: true,  requires_hitl: true }
    inventory_draft:{ allowed: true,  requires_hitl: true }
    chat:           { allowed: true }
    memory_read:    { allowed: true }
    semantic_memory_write: { allowed: true }
    eval_run:       { allowed: true }
```

### unauthenticated / unknown role

```yaml
unauthenticated:
  capabilities: {}
  action: "reject_all — return 401/403 trước khi vào harness"
```

---

## Capability Definitions

| Capability | Mô tả |
|---|---|
| `data_query` | Truy vấn dữ liệu đọc qua sql_subagent |
| `schema_explore` | Xem cấu trúc bảng/schema (không có dữ liệu thực) |
| `chart_report` | Vẽ biểu đồ từ kết quả truy vấn |
| `catalog_draft` | Tạo nháp catalog (product/category/supplier/customer) qua HITL |
| `inventory_draft` | Tạo nháp phiếu nhập kho qua HITL |
| `chat` | Hội thoại thông thường, câu hỏi về ERP |
| `memory_read` | Đọc lịch sử hội thoại phiên hiện tại |
| `semantic_memory_write` | Ghi vào semantic long-term memory |
| `eval_run` | Chạy golden eval set (dev/admin only) |

---

## Enforcement Points

```
1. Frontend: ẩn AI route nếu can_use_ai=false
2. API Gateway / FastAPI: kiểm tra can_use_ai trước khi vào harness
3. Harness (pre-tool): kiểm tra capability trước mỗi tool call
4. Tool implementation: verify lại capability (defense-in-depth)
5. Backend Spring: RLS enforce tenant_id + role tại DB
```

## HITL-Required Capabilities

`catalog_draft` và `inventory_draft` KHÔNG ĐƯỢC commit mà không có xác nhận HITL từ user. Harness phải:
1. Tạo nháp + emit `PendingHitlEvent`
2. Dừng loop, chờ user xác nhận
3. Chỉ commit khi nhận `clarification_response` có confirm=true

## Acceptance Checklist

- [ ] Staff không thể gọi catalog_draft hoặc inventory_draft
- [ ] Staff không nhận data_query result chứa cột nhạy cảm
- [ ] `can_use_ai` là prerequisite bắt buộc cho mọi capability
- [ ] Mọi tool trong tool_registry có entry trong matrix này
- [ ] Đồng nhất với K5 allowed_tables cho từng role
- [ ] Backend permission source là nguồn sự thật; file này sync khi Backend thay đổi
