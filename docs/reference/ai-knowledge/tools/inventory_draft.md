# InventoryDraftTool

> Source: `ai_python/app/graph/tools/inventory_draft.py`
> Prompts: inventory_draft.md, inventory_draft_stock_receipt.md, inventory_draft_stock_dispatch.md, inventory_draft_slots.md, inventory_entity_pick.md

## Tổng quan
Tạo bản nháp chứng từ kho (phiếu nhập kho, phiếu xuất kho) với cơ chế xác nhận human-in-the-loop. Quy trình hai pha: tạo bản nháp → người dùng xem xét → commit.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `inventory_draft` |
| capability | `draft_create` |
| side_effect_class | `non_idempotent_write` |
| has_hitl | `true` |
| risk_level | `high` |
| produces | `("inventory_draft",)` |
| consumes | — |
| result_ref_policy | — |
| output_artifact_types | `("inventory_draft",)` |
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
  "inventory_draft_sse": {
    "draft_id": "inv_abc123",
    "doc_type": "stock_receipt",
    "data": {...}
  }
}
```
Quan sát: `"Inventory draft ready; awaiting user confirmation."`

**Pha commit (sau khi HITL xác nhận):**
```json
{
  "draft_id": "inv_abc123",
  "commit_result": {
    "ok": true,
    "doc_id": "SR-2026-001"
  }
}
```

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Hai pha HITL: tạo bản nháp → người dùng xác nhận
- HitlSpec: `event_name="inventory_draft"`
- Resume qua `_confirm()` với `commit_inventory_draft`

### LangGraph (Legacy)
- Subgraph: `inventory_draft_subgraph`
- Nodes: `classify_inventory_doc`, `resolve_inventory_draft`, `generate_inventory_draft`, `persist_inventory_draft`

## Xử lý lỗi
- **HITL_DRAFT_MISSING**: Báo lỗi nếu không tìm thấy bản nháp khi cố gắng commit
- **Commit thất bại**: Bắt lỗi; dùng `committed.get("ok", True)` để xác định trạng thái

## Ví dụ
**Đầu vào:**
```json
{
  "request": "Create stock receipt for 50 units of 'Laptop Pro 15' from supplier ABC"
}
```
**Đầu ra (pha bản nháp):**
```json
{
  "inventory_draft_sse": {
    "draft_id": "draft_inv_001",
    "doc_type": "stock_receipt",
    "data": {
      "supplier": "ABC",
      "items": [
        {"product": "Laptop Pro 15", "quantity": 50}
      ]
    }
  }
}
```
Quan sát: `"Inventory draft ready; awaiting user confirmation."`
