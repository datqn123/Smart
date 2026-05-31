# BRIDGE — Task029 — `GET /api/v1/categories`

> **Task:** Task029 | **Path:** `GET /api/v1/categories` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (`API_Task029_categories_get_list.md`) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Query `format` | §5.2 `tree` \| `flat`, mặc định tree | [`CategoriesController.list`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/CategoriesController.java) → `CategoryService.list` | [`getCategoryList`](../../../mini-erp/src/features/product-management/api/categoriesApi.ts) luôn set `format` (mặc định `tree`) | **Partial** | UI chỉ dùng **tree**; `format=flat` có trong API nhưng chưa có toggle flat trên màn — đủ SRS tối thiểu UC8 cây. |
| Query `search` | §5.2 ILIKE name/code; tree giữ nhánh | `applySearchFilter` trong service | `debouncedSearch` → `listParams.search` trong [`CategoriesPage`](../../../mini-erp/src/features/product-management/pages/CategoriesPage.tsx) | Y | Debounce 400 ms. |
| Query `status` | §5.2 `all` \| `Active` \| `Inactive` | `normalizeListStatus` + `loadAllActive` | `statusFilter` → chỉ gửi query khi khác `all` | Y | — |
| RBAC | §4 Bearer | `hasAuthority('can_manage_products')` | `auth: true` | Y | — |
| Response `data.items` | §7 cây + `productCount`, `children` | `CategoryListPageData` / `CategoryNodeResponse` | `CategoryListData` → `mapNodeDtoToCategory` → [`CategoryTable`](../../../mini-erp/src/features/product-management/components/CategoryTable.tsx) recursive | Y | Cột SP = `productCount` trực tiếp node. |
| UI route | §6 / SRS §1.1 | — | `/products/categories` → `CategoriesPage`; index [`FEATURES_UI_INDEX.md`](../../../mini-erp/src/features/FEATURES_UI_INDEX.md) | Y | — |
| Tên hàm API | Prompt gợi ý `getCategories` | — | Export **`getCategoryList`** (cùng chức năng) | Y | Không đổi tên để tránh refactor; BRIDGE ghi rõ. |

**Kết luận:** Task029 đã nối: `getCategoryList` + `useQuery` + toolbar tìm/lọc + bảng cây. Muốn **flat view** trong UI → mở rộng sau (query `format=flat` + bảng một cấp).
