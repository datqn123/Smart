# BRIDGE — Task036 — `GET /api/v1/products/{id}`

> **Task:** Task036 | **Path:** `GET /api/v1/products/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (`API_Task036_products_get_by_id.md`) + SRS **§2 C4**, **§8.4** | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `GET` + shape | Header + `units[]` + `images[]` | [`ProductsController.getById`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/ProductsController.java) → `ProductDetailData` | [`getProductById`](../../../mini-erp/src/features/product-management/api/productsApi.ts) | Y | Đã có từ trước; không đổi contract. |
| **Dialog chi tiết** | Hiển thị units, gallery, giá | — | [`ProductDetailDialog`](../../../mini-erp/src/features/product-management/components/ProductDetailDialog.tsx): `useQuery` key `["product-management","products","detail","dialog", id]` khi `isOpen`; bảng đơn vị + giá vốn/bán (null → `—`); lưới `images` sort `sortOrder`; merge header từ **detail** fallback **list** `Product` | Y | **Tồn kho** header: vẫn từ **list** (Task034) vì `ProductDetailDto` không có `currentStock`. |
| Invalidate sau ảnh | Gallery / detail đồng bộ | — | [`ProductsPage.handleProductImageAdded`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) thêm `invalidateQueries` prefix `["product-management","products","detail"]` | Y | Gồm dialog + form sửa. |
| Sửa từ dialog | UC8 | — | `onRequestEdit` → đóng dialog + `handleEdit` | Y | — |
| Form sửa (Task037) | GET detail | — | `ProductsPage` `useQuery` `detail` (không có segment `dialog`) | Y | Hai query key tách dialog vs form — tránh cache chồng. |

**Kết luận:** Đã **`wire-fe`** Task036 trên **ProductDetailDialog**: tải chi tiết khi mở, hiển thị **units** + **images** + giá ĐV cơ sở; ảnh Task039 làm mới **detail** + list; nút chỉnh sửa mở form PATCH.
