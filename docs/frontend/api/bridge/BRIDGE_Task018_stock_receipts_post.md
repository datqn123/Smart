Task=Task018 (ticket) | Path=`POST /api/v1/stock-receipts/{id}/approve` | Mode=wire-fe | Date=2026-04-26

> **Lưu ý đánh số:** Controller BE ghi **Task019** cho endpoint approve; tài liệu hợp đồng: [`API_Task019_stock_receipts_approve.md`](../API_Task019_stock_receipts_approve.md). Trong repo, **Task018** trước đó đã gán cho `POST …/submit` ([`API_Task018_stock_receipts_submit.md`](../API_Task018_stock_receipts_submit.md)). File bridge này theo **prompt** (Task018 + tên file `…_post`).

Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y).

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + POST + Bearer | Task019 §3–4 | `StockReceiptsController` `@PostMapping("/stock-receipts/{id}/approve")` + `PreAuthorize` `can_approve` | `approveStockReceipt(id, { inboundLocationId })` trong `stockReceiptsApi.ts` | Y | — |
| Body | Task019 §4 — `inboundLocationId` | `StockReceiptApproveRequest` | JSON camelCase | Y | — |
| Response 200 | Task019 §5 — `StockReceiptViewData` | `StockReceiptViewData` | `apiJson<StockReceiptViewResponse>` | Y | — |
| UI | UC4/UC7 — dialog phiếu Pending | — | `ReceiptDetailDialog`: chọn vị trí (`STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS` seed V1 id 1..5), nút Duyệt → API; `onAfterApprove` → `InboundPage` invalidate list + detail | Y | RBAC: user không có `can_approve` → 403 toast |
| Từ chối | Task020 | — | `rejectStockReceipt` + overlay lý do trong `ReceiptDetailDialog` | Y | Xem `BRIDGE_Task020_stock_receipts_post.md` |

**Kết luận:** Đã nối approve; vị trí nhập là dropdown tĩnh khớp seed `WarehouseLocations` — môi trường khác id cần chỉnh `STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS` hoặc API danh sách vị trí sau này.
