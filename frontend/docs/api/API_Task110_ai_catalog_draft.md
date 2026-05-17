# API — Task110 AI catalog draft (HITL)

**Base:** `/api/v1/ai/catalog-drafts`  
**Auth:** Bearer JWT — `can_use_ai` + quyền entity (`can_manage_products` hoặc `can_manage_customers`).

## POST `/api/v1/ai/catalog-drafts`

Tạo nháp (AI hoặc FE).

**Body (JSON):**

```json
{
  "entityType": "product",
  "columns": [{ "key": "skuCode", "label": "Mã SKU", "type": "string", "required": true }],
  "rows": [{ "rowId": "r1", "values": { "skuCode": "A-01", "name": "SP 1", "baseUnitName": "Cái", "costPrice": 10000, "salePrice": 15000 } }],
  "conversationId": "optional-thread-uuid",
  "meta": { "sourcePrompt": "..." }
}
```

**201:** envelope `data` = `CatalogDraftResponse` (`id`, `entityType`, `status`, `columns`, `rows`, `expiresAt`, …).

## GET `/api/v1/ai/catalog-drafts/{id}`

Đọc nháp của user hiện tại.

## PATCH `/api/v1/ai/catalog-drafts/{id}`

Cập nhật `rows` (và tuỳ chọn `columns`) sau khi user sửa trên UI.

## POST `/api/v1/ai/catalog-drafts/{id}/commit`

Ghi từng dòng chưa commit qua service catalog (`ProductService.create`, …). Trả `committedCount`, `failedCount`, `outcomes[]`, `draft` cập nhật.

## DELETE `/api/v1/ai/catalog-drafts/{id}`

Đánh dấu nháp `expired`.

## SSE chat

FastAPI stream thêm event `draft` (JSON: `draftId`, `entityType`, `columns`, `rows`, `previewMessage`). Spring relay forward nguyên event name.
