Task=Task017 (ticket) | Path=`POST /api/v1/stock-receipts/{id}/submit` | Mode=wire-fe | Date=2026-04-26

> **Lưu ý đánh số:** Hợp đồng API trong repo là **Task018** — [`API_Task018_stock_receipts_submit.md`](../API_Task018_stock_receipts_submit.md). **Task017** trong codebase đã gán cho `DELETE …/{id}` ([`API_Task017_stock_receipts_delete.md`](../API_Task017_stock_receipts_delete.md)). File bridge này theo **prompt ticket** (Task017 + tên file `…_post`).

Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y).

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + POST + Bearer | Task018 §3–4 | `StockReceiptsController` `@PostMapping("/stock-receipts/{id}/submit")` | `submitStockReceipt(id)` trong `stockReceiptsApi.ts` — `POST`, `body: "{}"`, `auth: true` | Y | — |
| Response 200 + `data` | Task018 §5 — shape Task015 | `StockReceiptViewData` | `apiJson<StockReceiptViewResponse>` | Y | — |
| Luồng UI | UC7 — Gửi duyệt từ phiếu **Draft** đã có | `StockReceiptLifecycleService.submit` | `InboundPage` khi `editingReceipt`: **PATCH** lưu form rồi nếu `saveMode === "pending"` gọi **submit**; `saveMode === "draft"` chỉ PATCH | Y | Tạo mới trực tiếp Pending vẫn dùng Task014 `saveMode: pending` (không qua submit) |
| Invalidate cache | — | — | `invalidateQueries` list + detail sau PATCH/submit | Y | — |

**Kết luận:** Đã nối submit qua `submitStockReceipt`; nút « Gửi yêu cầu duyệt » trên form **sửa** Draft thực hiện PATCH + POST submit tuần tự. Lỗi submit (409 không phải Draft, 400 không có dòng, …) trả qua `toast` nhánh catch hiện có.
