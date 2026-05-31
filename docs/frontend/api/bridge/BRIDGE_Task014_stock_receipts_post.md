Task=Task014 | Path=POST /api/v1/stock-receipts | Mode=wire-fe | Date=2026-04-26

Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y).

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + method + Bearer | §4 Overview — `POST` `/api/v1/stock-receipts`, Bearer | `StockReceiptsController.java` `@PostMapping("/stock-receipts")` + `PreAuthorize` `can_manage_inventory` | `stockReceiptsApi.ts` → `postStockReceipt` (`auth: true`); gọi từ `InboundPage.tsx` | Y | — |
| Request body (camelCase) | §5.3 — `supplierId`, `receiptDate`, `invoiceNumber?`, `notes?`, `saveMode` `draft\|pending`, `details[]` với `unitId` | `StockReceiptCreateRequest.java`, `StockReceiptDetailRequest.java` (cùng field + `unitId`) | Body build trong `handleFormSubmit` (create); `saveMode` từ hai nút form | Y | — |
| `saveMode` → status | §5.3, §7 | `StockReceiptLifecycleService.create` → `mapSaveMode` | `ReceiptForm.tsx`: "Lưu bản nháp" → `draft`, "Gửi yêu cầu duyệt" → `pending` | Y | — |
| Response 201 + envelope | §6 — `StockReceiptViewData` + message | `ApiSuccessResponse.of(..., "Đã tạo phiếu nhập kho")` + `CREATED` | `apiJson` unwrap `data`; UI không map response, chỉ `invalidateQueries` list | Y | — |
| Lỗi 400 `details` | §8 | `BusinessException` + `details` map | `toast.error` + `description` từ `details` | Y (tối thiểu) | Có thể bổ sung `setError` theo key nếu cần UX form |
| Catalog SP/NCC | §5 (FK thật) | Seed V6/V10 vs UI | `receiptFormCatalog.ts` (productId/unitId giả định 1..8 khớp V6 khi DB sạch); NCC vẫn mock 1..5 — cần `supplierId` tồn tại trên DB | Partial | BRIDGE: dev chọn NCC/SP có trong DB hoặc chỉnh catalog |

**Kết luận:** Đã nối Task014 qua `postStockReceipt` + form nhập (`ReceiptForm` / `InboundPage` tạo mới). Sửa phiếu Draft → Task016 `patchStockReceipt` (xem `BRIDGE_Task016_stock_receipts_post.md`). Rủi ro: mock nhà cung cấp có thể không khớp `suppliers` trên môi trường — khi đó BE trả 400 và toast hiển thị `details`.

---

## Bổ sung — Task015 | Path=`GET /api/v1/stock-receipts/{id}` | Mode=wire-fe | Date=2026-04-26

*Hợp đồng đọc thực tế: `frontend/docs/api/API_Task015_stock_receipts_get_by_id.md` (prompt SRS gốc trích nhầm Task014 POST).*

Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y).

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Path + Bearer | §4 — `GET` `/api/v1/stock-receipts/{id}` | `StockReceiptsController` `@GetMapping("/stock-receipts/{id}")` | `getStockReceiptById(id)` trong `stockReceiptsApi.ts` | Y | — |
| Response 200 + `details` | §6 — `StockReceiptViewData` | `StockReceiptViewData` / `StockReceiptLineViewData` | `mapStockReceiptViewToUi` → `StockReceipt` | Y | — |
| Chi tiết dialog | UC7 — `ReceiptDetailDialog` | — | `InboundPage`: `useQuery` khi mở panel; hiển thị `receiptDetail ?? selectedReceipt`; `ReceiptDetailDialog` nhận `isLoadingDetail` | Y | — |
| Hydrate form sửa | UC7 hydrate | — | `handleEditReceipt` → `getStockReceiptById` + `mapStockReceiptViewToUi` trước khi mở `ReceiptForm` | Y | Lưu form Draft → `patchStockReceipt` (Task016) |

**Kết luận Task015:** Đã nối GET theo id; danh sách Task013 vẫn chỉ tóm tắt, dialog/form sửa lấy đủ dòng qua BE. Duyệt/từ chối trên dialog vẫn mock (Task019/020).
