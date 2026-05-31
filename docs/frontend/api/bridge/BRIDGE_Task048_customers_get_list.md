# BRIDGE — Task048 — `GET /api/v1/customers`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task048 |
| **Path** | `GET /api/v1/customers` |
| **Mode** | wire-fe (verify cập nhật) |
| **Date** | 27/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y (theo quy trình API_BRIDGE) |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + 200 envelope | `API_Task048_customers_get_list.md` §2, §6 | `CustomersController.java` `@GetMapping` → `list()` → `ApiSuccessResponse` + `CustomerListPageData` | `frontend/mini-erp/src/features/product-management/api/customersApi.ts` — `getCustomerList`, `CUSTOMER_LIST_QUERY_KEY`, `mapCustomerListItemDtoToCustomer`, whitelist sort khớp BE. `CustomersPage.tsx` — `useQuery` + debounce tìm kiếm, phân trang, chọn `sort` từ whitelist; bảng hiển thị `loyaltyPoints`, `totalSpent`, `orderCount`. | **Y** | Xóa đơn (Task052) dùng `invalidateQueries` trên prefix list. |
| RBAC `can_manage_customers` | Task048 §4 ghi chung; **SRS** OQ-4(b) | `@PreAuthorize("hasAuthority('can_manage_customers')")` | Menu **Khách hàng** — `Sidebar.tsx` `perm: "can_manage_customers"`; JWT `mp` parse + `useAuthStore` (seed role cần bật quyền). | **Y** (FE menu + BE guard) | Route `/products/customers` chưa bọc `RequirePerm` (nếu cần hard-guard thì bổ sung). |
| Query: `search`, `status`, `page`, `limit`, `sort` | §5 | Cùng tên tham số, default `status=all`, `page=1`, `limit=20` | `getCustomerList` — gửi `search` khi khác rỗng; `status` khi ≠ `all`; `page`/`limit`/`sort` mặc định giống spec. | **Y** | — |
| Sort whitelist | §5, §7; **SRS** §8.2 | `CustomerJdbcRepository.resolveListOrderBy` — 10 giá trị; invalid → `IllegalArgumentException` → 400 (service layer) | `CUSTOMER_LIST_SORT_WHITELIST` + `<select>` trên `CustomersPage` — cùng 10 giá trị. | **Y** | — |
| `totalSpent` / `orderCount` (loại trừ `Cancelled`) | §6, §7 | `FROM_CUSTOMER_AGG` + `FILTER (WHERE status IS DISTINCT FROM 'Cancelled')` trên `salesorders` | Cột bảng + map DTO → `Customer`. | **Y** | Cập nhật **Task048 §6** dòng mơ hồ “hoặc mọi trạng thái” — **đã khớp SRS/BE** (ưu tiên sửa doc) |
| Lỗi 400/401/403 | §8 | 400 nếu `sort` lệch; 401/403 theo security / authority | `errToast` khi list lỗi; 401/403 từ `apiJson`. | **Y** | — |

## Kết luận (≤5 dòng)

1. **Backend** triển khai `GET /api/v1/customers` tại `CustomersController` + `CustomerService`/`CustomerJdbcRepository`, phù hợp aggregate và sort whitelist.  
2. **API markdown** `API_Task048_customers_get_list.md` tương đối khớp; nên rút gọn mục gây mơ hồ ở §6 (orderCount) cho đúng BE/SRS.  
3. **Frontend** đã nối **Task048**: `getCustomerList` + `CustomersPage` (phân trang, sort, tìm kiếm); `npm run build` + test `CustomersPage.test.tsx` pass.  
4. **Form tạo/sửa** (Task049/051) và **bulk delete** (Task053) vẫn cần tích hợp API tương ứng — form hiện `invalidateQueries` + toast hướng dẫn.  
5. **Output** `frontend/docs/api/bridge/BRIDGE_Task048_customers_get_list.md` cập nhật sau `wire-fe`.
