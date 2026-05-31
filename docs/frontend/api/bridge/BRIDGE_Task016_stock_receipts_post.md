Task=Task016 | Path=PATCH /api/v1/stock-receipts/{id} | Mode=wire-fe | Date=2026-04-26

> Tên file output theo ticket (`BRIDGE_Task016_stock_receipts_post.md`); nội dung là **PATCH** (không phải POST).

Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y).

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + method + Bearer | `API_Task016_stock_receipts_patch.md` §3 — `PATCH` `/api/v1/stock-receipts/{id}` | `StockReceiptsController` `@PatchMapping("/stock-receipts/{id}")` | `patchStockReceipt(id, body)` trong `stockReceiptsApi.ts` | Y | — |
| Body partial | §4.4 — `supplierId`, `receiptDate`, `invoiceNumber`, `notes`, `details[]` (ít nhất một field) | `StockReceiptPatchRequest.java` + `StockReceiptDetailRequest` cho từng dòng | `InboundPage` nhánh `editingReceipt`: gửi đủ header + `details` (replace all) | Y | — |
| Chi tiết dòng | Giống Task014 | Cùng DTO dòng | Tái dùng type `StockReceiptCreateDetailBody` trong patch body | Y | — |
| Response 200 | §5 — shape như Task015 | `StockReceiptViewData` | `apiJson` unwrap `data` (không map lại state form sau PATCH; đóng dialog form) | Y | Có thể hydrate lại từ response nếu cần |
| Lỗi 409 Draft-only | §7 | `StockReceiptLifecycleService.patch` — không Draft → CONFLICT | `toast` qua `ApiRequestError` | Y (tối thiểu) | — |
| UI Draft | §1 UC7 | — | `ReceiptForm` chỉ cho sửa khi `receipt.status === "Draft"` (sẵn có) | Y | Hai nút Lưu/Gửi khi sửa vẫn gọi cùng PATCH (không có `saveMode` BE) |

**Ghi chú prompt:** Tài liệu tham chiếu đúng cho Path này là `frontend/docs/api/API_Task016_stock_receipts_patch.md`, không phải `API_Task014_stock_receipts_post.md`.

**Kết luận:** Đã thay `inventoryCrudLogic.updateReceipt` bằng `patchStockReceipt` + `invalidateQueries` list và detail. Xóa phiếu → Task017 `deleteStockReceipt` trên `InboundPage` (không còn `deleteReceipt` mock).
