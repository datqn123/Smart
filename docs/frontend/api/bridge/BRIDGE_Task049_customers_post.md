# BRIDGE — Task049 — `POST /api/v1/customers`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task049 |
| **Path** | `POST /api/v1/customers` |
| **Mode** | wire-fe (verify cập nhật) |
| **Date** | 27/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y (theo quy trình API_BRIDGE) |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + `201` + envelope | `API_Task049_customers_post.md` §2, §4 | `CustomersController.create` — `ResponseEntity.status(201)`, `ApiSuccessResponse.of(data, "Đã tạo khách hàng")` | `customersApi.postCustomer` → `apiJson` 201 → `CustomerDetailDto`; `createCustomerMutation` trên `CustomersPage`; `onSubmit` khi **không** sửa gọi `postCustomer(buildCustomerCreateBody(data))` | **Y** | Sửa KH dùng `PATCH` (Task051) cùng dialog — không dùng POST. |
| RBAC `can_manage_customers` | Task049 ngầm; SRS OQ-4(b) | `@PreAuthorize("hasAuthority('can_manage_customers')")` | `apiJson` + Bearer; thiếu quyền → 403 → toast từ envelope | **Y** | — |
| Body: `customerCode`, `name`, `phone` bắt buộc; `email`, `address`, `status` | §3 | `CustomerCreateRequest` — `@NotBlank` trên code/name/phone; `email`/`address` optional; `status` nullable → `normalizeCustomerStatus` | `buildCustomerCreateBody` — trim, `email` rỗng → `null`, `address` rỗng → `null`, `status` từ form; Zod trên `CustomerForm` (max 50/255/20) | **Y** | — |
| `loyalty_points` = 0 khi tạo | §1, §5 | `insertCustomer` — `VALUES (…, 0, …)` | Không gửi điểm khi tạo; form **tạo mới** không chỉnh `loyaltyPoints` (chỉ hiện khi sửa + `canEditLoyaltyPoints`). | **Y** | — |
| 409 trùng `customerCode` | §5, §6 | `existsCustomerCode` → `CONFLICT` "Mã khách hàng đã tồn tại", `details.field=customerCode` | `applyCustomerCreateApiError` — map `field` + `message` lên RHF `customerCode`; 409 khác → toast | **Y** | 409 từ `DataIntegrityViolationException` có thể thiếu `field` → toast chung. |
| 400 validation / business | §6 | `MethodArgumentNotValid` → 400, `details` theo tên field; `validateEmailFormat` | `applyCustomerCreateApiError` gán từng trường; không map được → `toast.error(message)` | **Y** | — |
| `invalidate` danh sách | — | — | `onSuccess` → `queryClient.invalidateQueries` prefix `CUSTOMER_LIST_QUERY_KEY` + `toast.success("Đã tạo khách hàng")` | **Y** | — |
| Message success | (doc không cố định chuỗi) | `"Đã tạo khách hàng"` | Chấp nhận; toast tạo ở FE. | **Y** | Tùy DOC_SYNC. |

**Ký hiệu:** **P** = partial (verify cũ) — cập nhật sau khi nối.

## Grep nhanh (theo yêu cầu, không `Glob` cả `features/`)

- `d:\do_an_tot_nghiep\project\frontend\mini-erp\src\features\product-management\api\customersApi.ts` — `postCustomer`, `buildCustomerCreateBody`, `applyCustomerCreateApiError`
- `d:\do_an_tot_nghiep\project\frontend\mini-erp\src\features\product-management\components\CustomerForm.tsx` — submit, `400`/`409` RHF
- `d:\do_an_tot_nghiep\project\frontend\mini-erp\src\features\product-management\pages\CustomersPage.tsx` — `createCustomerMutation`

## Kết luận (≤5 dòng)

1. **Backend** tạo KH đúng 201, envelope, 409 trùng mã, validation body.  
2. **FE** nối Task049: tạo mới qua `postCustomer` + `buildCustomerCreateBody`; lỗi 400/409 ánh xạ field/ toast theo `ApiErrorBody.details`.  
3. **Sửa KH** dùng `PATCH` (Task051) trong cùng `CustomerForm` — không thuộc bảng POST Task049.  
4. `npm run build` (`mini-erp`) pass sau khi gỡ trùng `useMutation` / gom `Task049` một lần trong `customersApi`.  
5. **Output** `BRIDGE_Task049_customers_post.md` cập nhật cho **Mode=wire-fe**.
