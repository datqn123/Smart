# BRIDGE — Task031 — `GET /api/v1/categories/{id}`

> **Task:** Task031 | **Path:** `GET /api/v1/categories/{id}` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y · [`mini-erp/src/features/FEATURES_UI_INDEX.md`](../../mini-erp/src/features/FEATURES_UI_INDEX.md) (route `/products/categories` → `CategoriesPage` + `CategoryDetailDialog`)

| Hạng mục | API doc (`API_Task031_categories_get_by_id.md`) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path / GET / 200 | §2–§5 | `GET /{id}` | [`getCategoryById`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) | Y | — |
| `data`: `parentName`, `productCount` | §5 | `CategoryDetailData` | `CategoryDetailDto` + [`mapDetailDtoToCategory`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) | Y | `productCount` hiển thị header + stat cards. |
| `breadcrumb` | §5 | trail từ gốc → node | Type [`CategoryBreadcrumbItem`](../../../mini-erp/src/features/product-management/types.ts) + map từ DTO; UI: nav dạng “A › B › C” trong [`CategoryDetailDialog`](../../../mini-erp/src/features/product-management/components/CategoryDetailDialog.tsx) | Y | Last segment bold; placeholder «Đang tải đường dẫn…» khi [`detailLoading`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx) (`detailQuery.isFetching`). |
| useQuery chi tiết | UC8 | — | [`CategoriesPage`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx) `detailQuery` khi có `viewingCategory`; `detailCategory` = map(detail) \|\| list snapshot | Y | — |
| Path grep (`/categories/`) | — | — | Chỉ [`categoriesApi.ts`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) (list/get/patch/delete) | Y | Không Glob cả `features/`. |

**Kết luận:** Wire-fe hoàn tất — GET chi tiết đồng bộ **`breadcrumb`** + **`productCount`** vào dialog; không còn lệch Partial so với verify.
