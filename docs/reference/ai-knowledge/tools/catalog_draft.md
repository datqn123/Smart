# CatalogDraftTool

> Source: `ai_python/app/graph/tools/catalog_draft.py`
> Prompts: catalog_draft.md, catalog_draft_product.md, catalog_draft_category.md, catalog_draft_supplier.md, catalog_draft_customer.md, catalog_draft_slots.md, catalog_entity_pick.md

## Tổng quan
Tạo bản nháp dữ liệu danh mục (sản phẩm, danh mục, nhà cung cấp, khách hàng) với cơ chế xác nhận human-in-the-loop. Quy trình hai pha: tạo bản nháp → người dùng xem xét → commit.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `catalog_draft` |
| capability | `draft_create` |
| side_effect_class | `non_idempotent_write` |
| has_hitl | `true` |
| risk_level | `high` |
| produces | `("input_table_draft",)` |
| consumes | — |
| result_ref_policy | — |
| output_artifact_types | `("input_table_draft",)` |
| rbac_required | `("draft_create",)` |
| examples | — |

## Schema đầu vào
```json
{
  "request": "string"
}
```

## Đầu ra / Quan sát
**Pha tạo bản nháp:**
```json
{
  "catalog_draft_sse": {
    "draft_id": "abc123",
    "entity_type": "product",
    "data": {...}
  }
}
```
Quan sát: `"Catalog draft ready; awaiting user confirmation."`

**Pha commit (sau khi HITL xác nhận):**
```json
{
  "draft_id": "abc123",
  "commit_result": {
    "ok": true,
    "entity_id": "PROD-001"
  }
}
```

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Hai pha HITL: tạo bản nháp → người dùng xác nhận
- HitlSpec: `event_name="draft"`
- Resume qua `_confirm()` với `commit_catalog_draft`

### LangGraph (Legacy)
- Subgraph: `catalog_draft_subgraph`
- Nodes: `classify_catalog_entity`, `resolve_catalog_draft`, `generate_catalog_draft`, `persist_catalog_draft`

## Xử lý lỗi
- **HITL_DRAFT_MISSING**: Báo lỗi nếu không tìm thấy bản nháp khi cố gắng commit
- **Commit thất bại**: Bắt lỗi và báo cáo trong `commit_result`
- **failedCount**: Quyết định trạng thái ok trong luồng HITL

## Ví dụ
**Đầu vào:**
```json
{
  "request": "Create a new product 'Laptop Pro 15' with price 25000000 VND"
}
```
**Đầu ra (pha bản nháp):**
```json
{
  "catalog_draft_sse": {
    "draft_id": "draft_abc123",
    "entity_type": "product",
    "data": {
      "product_name": "Laptop Pro 15",
      "price": 25000000,
      "currency": "VND"
    }
  }
}
```
Quan sát: `"Catalog draft ready; awaiting user confirmation."`
