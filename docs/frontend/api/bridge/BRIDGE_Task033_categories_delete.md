# BRIDGE — Task033 — `DELETE /api/v1/categories/{id}`

> **Task:** Task033 | **Path:** `DELETE /api/v1/categories/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

**Index UI:** [`frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../mini-erp/src/features/FEATURES_UI_INDEX.md) — `/products/categories` → `CategoriesPage` + `CategoryTable` + `CategoryToolbar` + `CategoryDetailDialog` + `ConfirmDialog`.

| Hạng mục | API doc (`API_Task033_categories_delete.md`) | Backend | Frontend (`frontend/mini-erp/src`) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `DELETE` path + body rỗng | §2 | `CategoriesController` | [`deleteCategory`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) = [`deleteCategorySoft`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) (cùng impl) | Y | — |
| 200 + `data` + toast | §5 | — | `useMutation` `deleteMutation` (`mutationFn` → `deleteCategory`); `onSuccess` → `invalidateQueries` prefix `["product-management","categories"]` | Y | Một bản: **TanStack Query** thay gọi trần. |
| Owner-only vs Staff | §6, §7 **403** | `assertOwnerOnly` (JWT `role` = Owner) | `useAuthStore` → `isOwner`; Ẩn xóa hàng / hàng loạt / **Xóa mềm** trong `CategoryDetailDialog` khi không Owner | Y | Staff không thấy CTA; nếu gọi lệnh vẫn 403 + [`toastCategoryMutationEnvelope`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx). |
| `ConfirmDialog` + xóa nhiều (lần lượt) | §8 | — | Một bản: `mutateAsync`; hàng loạt: lặp `deleteCategory` + `invalidate` cuối | Y | Như spec (chưa bulk API). |
| Đóng panel chi tiết khi mục bị xóa | — | — | `onSuccess` / bulk: `setViewingCategory` khi `id` trùng | Y | Từ chi tiết: **Xóa mềm** → `setDeleteTarget` + đóng dialog trước khi confirm. |
| 409 / 404 / 403 / envelope | §7 | — | `onError: toastCategoryMutationEnvelope` | Y | — |

**Kết luận:** Task033 **đã nối dây** theo hợp đồng: API layer (`deleteCategory` / `deleteCategorySoft` → `apiJson` Bearer), nghiệp vụ **chỉ Owner** phản ánh ở UI cùng policy BE, xác nhận trước khi gọi, `invalidate` sau khi thành công.
