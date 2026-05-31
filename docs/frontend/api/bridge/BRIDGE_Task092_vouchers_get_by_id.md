# BRIDGE — Task092 — `GET /api/v1/vouchers/{id}`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task092 |
| **Path** | `GET /api/v1/vouchers/{id}` |
| **Mode** | wire-fe |
| **Date** | 30/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path `GET …/vouchers/{id}` (id số dương) | `API_Task092_vouchers_and_retail_preview.md` §2 | `VouchersController.java` `@GetMapping("/{id:[0-9]+}")` → `parsePositiveIntId` → `VoucherService.getById` | `vouchersApi.ts` — `getVoucherById`; `POSCartPanel.tsx` — `handlePickVoucherFromList` (trước khi `setVoucher` / `setSelectedVoucherId`) | **Y** | — |
| 404 không tồn tại | §2 | `BusinessException(NOT_FOUND, "Không tìm thấy voucher")` khi `findVoucherById` rỗng | Toast lỗi từ envelope (`ApiRequestError`) | **Y** | — |
| Response body = một object cùng shape item list | §2 | `ApiSuccessResponse<VoucherListItemData>` — các field `id`, `code`, `name`, `discountType`, `discountValue`, `validFrom`, `validTo`, `isActive`, `usedCount`, `maxUses`, `createdAt` | Cùng `VoucherListItemDto` với list | **Y** | — |
| RBAC | §1 (cùng Task092) | `@PreAuthorize("hasAuthority('can_manage_orders')")` + JWT | `apiJson(..., { auth: true })` | **Y** | — |
| Message 200 | ví dụ SRS §8 | `ApiSuccessResponse.of(..., "Thao tác thành công")` | — | **Y** | — |

## Kết luận (≤5 dòng)

1. **BE** khớp §2: chi tiết theo `id`, **404** khi không có bản ghi (`VoucherService.getById`).  
2. **FE** gọi `getVoucherById` khi chọn một dòng trong danh sách voucher trên `POSCartPanel`.  
3. Path chỉ nhận **chữ số** (`[0-9]+`); id không hợp lệ → **400** — khác 404 “không tìm thấy voucher”.  
4. Khớp SRS luồng list → detail trước preview/checkout.
