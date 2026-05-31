Task=Task020 | Path=`POST /api/v1/stock-receipts/{id}/reject` | Mode=verify | Date=2026-04-26

> Tên file output theo prompt (`…_post`); endpoint là **reject**, không phải tạo phiếu.

Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y). Hợp đồng: [`API_Task020_stock_receipts_reject.md`](../API_Task020_stock_receipts_reject.md) (prompt trích `API_Task014` không khớp path).

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + POST + Bearer | §3 — `POST` `/api/v1/stock-receipts/{id}/reject` | `StockReceiptsController` `@PostMapping("/stock-receipts/{id}/reject")` + `PreAuthorize` `can_approve` | `rejectStockReceipt(id, { reason })` trong `stockReceiptsApi.ts` | Y | — |
| Body | §4 — `reason` bắt buộc, max 2000 | `StockReceiptRejectRequest` | `JSON.stringify({ reason })`; FE `Textarea` `maxLength={2000}`, trim trước gửi | Y | — |
| Response 200 | §5 — `StockReceiptViewData` / status Rejected | `StockReceiptViewData` | `apiJson<StockReceiptViewResponse>` | Y | — |
| UI (chi tiết) | UC4/UC7 — phiếu `Pending` | — | `ReceiptDetailDialog.tsx`: overlay lý do → `rejectStockReceipt` → `onAfterApprove` → `InboundPage` `invalidateQueries` list + detail | Y | — |
| UI (form) | UC7 | — | `ReceiptForm.tsx`: khi `receipt.status === "Pending"` và `canApprove`, cùng overlay + `rejectStockReceipt` + `onAfterApproveOrReject` | Y | — |
| RBAC | §3 | Giống approve (`can_approve`) | `toast` trên `ApiRequestError` | Y | SRS Owner-only có thể kiểm thêm ở BE `StockReceiptAccessPolicy` — không đổi FE |

**Verify (grep):** `backend/.../StockReceiptsController.java` có `@PostMapping("/stock-receipts/{id}/reject")`; `frontend/mini-erp/src/features/inventory/api/stockReceiptsApi.ts` có `POST` tới `` `/api/v1/stock-receipts/${id}/reject` ``; không còn `alert` mock reject trên hai component trên.

**Kết luận (Mode=verify):** Doc ↔ BE ↔ FE **khớp**; reject đã móc qua `apiJson` + Bearer, hai điểm vào UI (dialog chi tiết + form phiếu Pending). Không cần sửa code trong phiên verify.
