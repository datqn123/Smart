# SRS — Task111 AI inventory draft (HITL) — phiếu nhập kho v1

## Mục tiêu

Người dùng mô tả yêu cầu tạo **phiếu nhập kho**; AI sinh nháp (header + dòng hàng); user chỉnh sửa trên chat; xác nhận tạo phiếu **Draft** hoặc **Pending** qua API kho.

## Phạm vi v1

- Entity: `stock_receipt` only.
- Nháp lưu bảng `ai_inventory_draft` (TTL 72h).
- Commit: một phiếu → `POST /api/v1/stock-receipts` (saveMode draft|pending).
- FK resolve lúc commit: `supplierName`/`supplierCode` → `supplierId`; `skuCode` → `productId`; `unitId` = đơn vị cơ sở.

## Ngoài phạm vi v1

- Phê duyệt phiếu / `inboundLocationId` trong chat (làm trên màn Nhập kho).
- Phiếu xuất kho (`stock_dispatch`) — phase 2.
- Tạo sản phẩm/NCC mới trong cùng commit.

## Luồng

1. User chat → intent `inventory_data_entry`.
2. Python `inventory_draft_subgraph` → POST `/api/v1/ai/inventory-drafts`.
3. SSE `inventory_draft` → FE `AiChatReceiptDraftCard`.
4. PATCH nháp → POST commit → `StockReceiptLifecycleService.create`.
