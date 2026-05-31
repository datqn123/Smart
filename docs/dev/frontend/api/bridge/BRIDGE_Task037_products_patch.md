# BRIDGE — Task037 — `PATCH /api/v1/products/{id}`

> **Task:** Task037 | **Path:** `PATCH /api/v1/products/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026 *(cập nhật SRS §14.1 / BR-8 / BR-10 / OQ-8)*

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (`API_Task037_products_patch.md`) + SRS §8.5, §14.1, **BR-3–BR-4**, **BR-8**, **BR-10**, **OQ-8** | Backend | Frontend | Khớp | Ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `PATCH` + Bearer | §2–3 | [`ProductsController.patch`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/ProductsController.java) | [`patchProduct`](../../../mini-erp/src/features/product-management/api/productsApi.ts) + [`ProductsPage`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) `patchMutation` | **Y** | `apiJson`, `auth: true`. |
| Partial body | Chỉ field đổi | `JsonNode` | [`buildProductPatchBody`](../../../mini-erp/src/features/product-management/api/productsApi.ts) so với [`productDetailToEditSnapshot`](../../../mini-erp/src/features/product-management/api/productsApi.ts) | **Y** | Không gửi key nếu giá trị trùng snapshot. |
| **`hasImageChange` (khái niệm)** | SRS §14.5 OQ-8(3): chỉ cần một thành phần (meta / giá / ảnh) đổi | BE có thể so DB khi mở rộng PATCH gallery | FE: `hasFieldPatch \|\| hasStaged` trong `onSubmit` sửa; chỉ ảnh → không bắt buộc PATCH | **Y (FE)** | Chỉ ảnh: bỏ qua `patchMutation`, chỉ chạy vòng Task039 sau Lưu. |
| **`BR-10` — ảnh form sửa** | Không POST ảnh khi đang soạn; chỉ khi **Lưu** | — | [`ProductImagePanel`](../../../mini-erp/src/features/product-management/components/ProductImagePanel.tsx) với `staged` + `onStagedChange`; [`ProductsPage`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) submit: (1) `patchMutation` nếu `Object.keys(body).length > 0`; (2) `postProductImageMultipart` / `postProductImageJson` theo `stagedImages` | **Y** | Thứ tự align OQ-8(2) v1: PATCH trước, rồi Task039. |
| `categoryId: null` | Bỏ phân loại | `ProductService.patch` | Select **Không phân loại** (`0`) → body `categoryId: null` khi khác snapshot | **Y** | |
| Cặp giá | Đủ `salePrice` + `costPrice` khi đổi giá | BE validate cặp | Form luôn có 2 field; `buildProductPatchBody` gửi cả hai nếu một trong hai đổi | **Y** | |
| `priceEffectiveDate` | Tuỳ chọn | BE parse | Input `type="date"` (chỉ edit), chỉ gửi khi có chuỗi và đã đổi giá | **Y** | |
| Invalidate | List + detail | — | `invalidateQueries` list + detail sau PATCH; sau block ảnh staged thêm invalidate nếu `hasStaged` | **Y** | Kèm `getProductById` (Task036) khi mở form sửa. |
| 409 / 400 `details` | Task032-style | — | [`toastProductMutationEnvelope`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx); [`ProductForm`](../../../mini-erp/src/features/product-management/components/ProductForm.tsx) `setError` khi **400** + `details` | **Y** | Giống pattern CategoriesPage. |
| UI | `ProductForm` / `ProductsPage` | — | [`ProductForm`](../../../mini-erp/src/features/product-management/components/ProductForm.tsx) + [`ProductsPage`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) | **Y** | `onImageAdded` vẫn truyền cho tương thích; panel sửa/tạo ưu tiên staged. |

**Kết luận:**

- Đã **`wire-fe`**: `getProductById`, `patchProduct`, snapshot + `buildProductPatchBody`, `useMutation` + invalidate list/detail, xử lý lỗi 409 / 400 `details` như Task032/Task035.
- Snapshot cập nhật khi `GET` chi tiết thành công; không có thay đổi field và không có staged ảnh → toast + `ProductFormSubmitAborted`.
- Luồng **chỉ đổi ảnh** (BR-8): không PATCH rỗng; gọi Task039 sau Lưu — khớp SRS §11 / §14.5.
- Tùy chọn sau: một `PATCH` gộp gallery (ADR SRS §14.2) — doc `fix-doc` Task037 khi BE có contract.
