# BRIDGE — Task034 — `GET /api/v1/products`

> **Task:** Task034 | **Path:** `GET /api/v1/products` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (`API_Task034_products_get_list.md`) + SRS §8.2 | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Query `search` / `categoryId` / `status` / `page` / `limit` / `sort` | §5–6 + whitelist sort | [`ProductsController.list`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/ProductsController.java) | [`getProductList`](../../../mini-erp/src/features/product-management/api/productsApi.ts) — `PRODUCT_LIST_SORT_WHITELIST`; debounce 400 ms + reset trang khi đổi lọc ([`ProductsPage`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx)) | Y | `categoryId` chỉ gửi khi `> 0`. |
| Dropdown danh mục | §10 gợi ý `categoryId` + flat/tree | — | `getCategoryList({ format: "tree", status: "Active" })` + `flattenCategories` → `ProductToolbar` `categoryOptions` | Y | Fallback form: `mockCategories` nếu API rỗng. |
| Response → bảng | `items` + pagination | `ProductListPageData` | `mapProductListItemDtoToProduct` → [`ProductTable`](../../../mini-erp/src/features/product-management/components/ProductTable.tsx) | Y | — |
| RBAC | Bearer + quyền đọc | `can_manage_products` | `apiJson` `auth: true` | Y | — |
| Xóa / tạo / sửa từ UI | — | Task035/037/038/041 | Toast hướng dẫn nối API; chưa gọi BE | N (chờ task) | Giữ scope Task034 = **list**. |

**Kết luận:** Đã nối **GET list** vào `/products/list`: `productsApi.getProductList` + `useQuery` + phân trang + sort whitelist + lọc server. Toolbar đổi lọc danh mục theo **`categoryId`**. CRUD/delete bulk: thông báo task sau, không giả lập cập nhật danh sách.
