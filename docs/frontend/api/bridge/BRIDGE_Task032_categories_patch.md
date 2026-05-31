# BRIDGE — Task032 — `PATCH /api/v1/categories/{id}`

> **Task:** Task032 | **Path:** `PATCH /api/v1/categories/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y  
**Đã đọc** [`frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../mini-erp/src/features/FEATURES_UI_INDEX.md): Y (route `/products/categories` → `CategoriesPage` + `CategoryForm`)

**Grep** `Path` `/api/v1/categories` trong `frontend/mini-erp/src` — chỉ [`categoriesApi.ts`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) (không `Glob` cả `features/`).

| Hạng mục | API doc (`API_Task032_categories_patch.md`) | Backend | Frontend (`frontend/mini-erp/src`) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path / method / 200 | §2, §6 | [`CategoriesController`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/CategoriesController.java) `@PatchMapping` | [`patchCategory`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) | Y | **wire-fe:** type `CategoryPatchBody` + JSDoc §5 (partial, `description: ""` xóa mô tả, không `parentId: null` kéo gốc v1). |
| Body partial | §5 | `CategoryService.patch` | [`buildPatchBody`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx) → `CategoryPatchBody` | Y | — |
| Invalidate list + detail | — | — | `invalidateQueries({ queryKey: ["product-management", "categories"] })` — prefix gồm `list` và `detail` | Y | **wire-fe** sau PATCH success. |
| Toast **400** / **409** envelope | §8 | `BusinessException` + `ApiErrorResponse` | [`toastCategoryMutationEnvelope`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx): **400** + `details` → im lặng (form `setError` trong [`CategoryForm`](../../../mini-erp/src/features/product-management/components/CategoryForm.tsx)); **409** → `toast.error` message (+ `details` nếu có); **400** không `details` → `toast.error` message | Y | Cùng handler cho `createMutation` + `patchMutation`. |
| SystemLogs | §7 tuỳ chọn | Không thấy | — | **Partial** | — |

**Kết luận:** **wire-fe** hoàn tất: `patchCategory` + `CategoryPatchBody`, `patchMutation` + invalidate prefix, toast envelope 400/409 tách với map field form. Doc §9 Zod tách — logic PATCH vẫn khớp `buildPatchBody`.
