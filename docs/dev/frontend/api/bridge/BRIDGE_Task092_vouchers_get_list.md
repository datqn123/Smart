# BRIDGE — Task092 — `GET /api/v1/vouchers`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task092 |
| **Path** | `GET /api/v1/vouchers` |
| **Mode** | wire-fe |
| **Date** | 30/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + query `page`, `limit` | `API_Task092_vouchers_and_retail_preview.md` §1 | `VouchersController.java` `@GetMapping` — `page` default `1`, `limit` nullable → `VoucherService.listRetailApplicable` (default **5**, max **50**) | `vouchersApi.ts` — `getVouchersList`; `POSCartPanel.tsx` — `useInfiniteQuery` (`limit=5`, nút **Xem thêm** → `page++`) | **Y** | — |
| Lọc + sort | §1 (active, hạn, còn lượt; `created_at DESC`) | `VoucherJdbcRepository.countRetailApplicable` + `findRetailApplicablePage` | — | **Y** (BE) | — |
| Response `data` `{ items, page, limit, total }` + item fields | §1 | `VoucherListPageData`, `VoucherListItemData` (camelCase record) | `VoucherListPageDto` / `VoucherListItemDto` trong `vouchersApi.ts` | **Y** | — |
| RBAC | §1 + envelope | `@PreAuthorize("hasAuthority('can_manage_orders')")` + JWT trong controller | `apiJson(..., { auth: true })` | **Y** | — |
| Message 200 | ví dụ SRS §8 | `ApiSuccessResponse.of(data, "Thao tác thành công")` | — | **Y** | — |

## Kết luận (≤5 dòng)

1. **BE** khớp contract §1 (`VouchersController` → `VoucherService` → `VoucherJdbcRepository`).  
2. **FE** đã nối: `getVouchersList` + `POSCartPanel` (phân trang “Xem thêm”, `limit=5`).  
3. Query `limit` bỏ trống trên BE vẫn mặc định **5** (OQ-2 SRS); UI gửi rõ `limit=5`.  
4. Sau checkout thành công, `invalidateQueries` trên `VOUCHERS_LIST_QUERY_KEY` để cập nhật `usedCount` nếu cần.
