# API — Task111 AI inventory draft (phiếu nhập kho HITL)

Base: `/api/v1/ai/inventory-drafts`  
Auth: `can_use_ai` + `can_manage_inventory`

## POST `/`

Body:

```json
{
  "entityType": "stock_receipt",
  "header": {
    "supplierName": "NCC ABC",
    "receiptDate": "2026-05-17",
    "saveMode": "draft",
    "invoiceNumber": "",
    "notes": ""
  },
  "lineColumns": [{ "key": "skuCode", "label": "Mã SKU", "type": "string", "required": true }],
  "lines": [
    {
      "lineId": "l1",
      "values": { "skuCode": "PC-001", "quantity": 10, "costPrice": 8000000 }
    }
  ],
  "conversationId": "optional-uuid"
}
```

## PATCH `/{id}`

Body: `{ "header"?, "lineColumns"?, "lines": [...] }`

## POST `/{id}/commit`

Tạo phiếu nhập thật. Response:

```json
{
  "success": true,
  "message": "Đã tạo phiếu nhập PN-2026-0001",
  "createdReceiptId": 42,
  "receiptCode": "PN-2026-0001",
  "draft": { ... }
}
```

## SSE (chat)

Event: `inventory_draft` — payload khớp FE `InventoryReceiptDraftPayload`.
