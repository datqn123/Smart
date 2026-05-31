# BRIDGE — Task092 — `POST /api/v1/sales-orders/retail/voucher-preview`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task092 |
| **Path** | `POST /api/v1/sales-orders/retail/voucher-preview` |
| **Mode** | wire-fe |
| **Date** | 30/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path (namespace retail **OQ-9A**) | `API_Task092_vouchers_and_retail_preview.md` §3 | `SalesOrdersController` `@RequestMapping("/api/v1/sales-orders")` + `@PostMapping("/retail/voucher-preview")` | `salesOrdersApi.ts` — `postRetailVoucherPreview`; `POSCartPanel.tsx` — `useQuery` khi có `voucherCode` + giỏ không rỗng | **Y** | — |
| Body `voucherId` / `voucherCode` (ít nhất một) | §3 | `RetailVoucherPreviewRequest` + `retailVoucherPreview`: thiếu cả hai → **400**; cả hai → kiểm tra khớp `code` | Chọn từ list: gửi cả `voucherId` + `voucherCode`; nhập tay: chỉ `voucherCode` | **Y** | — |
| Body `lines`, `discountAmount` | §3 | `validateLines` + `computeSubtotal` giống checkout; `discountAmount` optional | `lines` + `discountAmount` từ `useOrderStore` | **Y** | — |
| **200** + shape `RetailVoucherPreviewData` | §3 | `applicable: true`, `message: null`, đủ các field số tiền | Map `applicable`, `payableAmount`, `voucherDiscountAmount`, `message`; tổng hiển thị ưu tiên `payableAmount` khi `applicable` | **Y** (BE) | Trên **200**, BE hiện **luôn** `applicable = true` khi tính được. |
| **OQ-11** (200 + `applicable: false` + `message`) | §4.2 SRS | Chưa có nhánh “voucher hợp lệ nhưng không áp dụng giỏ” — mọi lỗi nghiệp vụ preview đang **400** | UI có nhánh hiển thị `!applicable` + `message` (sẵn sàng khi BE bật) | **Partial** (BE) | DOC_SYNC / BE sau |
| **OQ-12** / **400** (không tìm thấy, hết hạn, hết lượt, lines sai, mismatch) | §3 | `BAD_REQUEST` với message tiếng Việt tương ứng | Hiển thị `message` từ envelope dưới badge voucher | **Y** | — |
| Checkout **409** (hết lượt voucher) | Task092 §4 + SRS | `retailCheckout` khóa voucher → **409** khi hết lượt | `checkoutErrorToast` — nhánh **409** + toast mô tả (Task060 checkout không đổi path) | **Y** | — |
| RBAC | §1 Task092 | `@PreAuthorize("hasAuthority('can_manage_orders')")` + JWT | `apiJson(..., { auth: true })` | **Y** | — |
| Message 200 | §8 ví dụ | `ApiSuccessResponse.of(..., "Thao tác thành công")` | — | **Y** | — |

## Kết luận (≤5 dòng)

1. **BE** giữ nguyên path **`POST /api/v1/sales-orders/retail/voucher-preview`** và payload/response §3.  
2. **FE** đã nối preview + hiển thị lỗi **400** + tổng tiền ước tính; checkout **409** (voucher hết lượt) qua `checkoutErrorToast`.  
3. **OQ-11** (`applicable: false` trên 200): **BE** vẫn chưa có — UI đã chừa nhánh `message` khi `!applicable`.  
4. Lỗi validation **`@Valid`** có thể khác `BusinessException`; hiện dùng `ApiRequestError` / `body.message` chung.
