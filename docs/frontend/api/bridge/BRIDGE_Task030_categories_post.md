# BRIDGE — Task030 — `POST /api/v1/categories`

> **Task:** Task030 | **Path:** `POST /api/v1/categories` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

**Index UI:** [`frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../mini-erp/src/features/FEATURES_UI_INDEX.md) — route `/products/categories` → `product-management/pages/CategoriesPage.tsx`; form `CategoryForm.tsx`.

| Hạng mục | API doc (`API_Task030_categories_post.md`) | Backend | Frontend (`frontend/mini-erp/src`) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path / method / 201 | §4–§6 | [`CategoriesController`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/CategoriesController.java) `@PostMapping` | [`postCategory`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) = [`createCategory`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) (alias) | Y | `apiJson` + `201` |
| Body camelCase | §5 | `CategoryCreateRequest` | `CategoryCreateBody` + trim, `parentId` null nếu không chọn cây (≤0) | Y | — |
| `useMutation` + invalidate | Guide §5 | — | `createMutation` `mutationFn: postCategory` → `invalidateQueries({ queryKey: ["product-management", "categories"] })` (list + detail chung prefix) | Y | [`CategoriesPage.tsx`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx) |
| Submit form | UC8 | — | `CategoryForm` `onSubmit` → `handleFormSubmit` gọi `createMutation.mutateAsync` khi không `editingCategory.id` | Y | — |
| 400 + `details` | Guide §3 | `BusinessException` / validation | `CategoryForm`: `setError` theo key; hiển thị `formState.errors`; `errToastUnlessFieldDetails` tránh trùng toast với lỗi từng trường | Y | wire-fe (27/04/2026) |
| 409 / lỗi khác | §7 | Trùng mã | `errToast` toàn câu từ `ApiRequestError` | Y | — |
| SystemLogs | §7 bước 5 (tuỳ chọn) | Chưa thấy | — | **Partial** | Doc gợi ý. |

**Kết luận:** POST Task030 **đã nối dây** theo `FE_API_CONNECTION_GUIDE` (`apiJson` → `categoriesApi` → `CategoriesPage` + `CategoryForm`), invalidate cây `["product-management","categories"]`, xử lý 400 theo từng trường. **Ghi nhận lệch nhỏ:** SystemLogs trong spec bước 5 chưa phản ánh ở BE khi tạo.
