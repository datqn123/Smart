# BRIDGE — Task059 — `GET /api/v1/pos/products`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task059 |
| **Path** | `GET /api/v1/pos/products` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + query `search`, `categoryId`, `locationId`, `limit` | `API_Task059_pos_products_get_search.md` §5 | `PosProductsController.java` `@GetMapping` — cùng tên query; `limit` default 40, BE clamp 1–100 (`SalesOrderService.searchPosProducts`) | `features/orders/api/posProductsApi.ts` — `searchPosProducts` | **Y** | Gắn `categoryId` / `locationId` khi có UI lọc. |
| Response `data.items[]` | §6 | `PosProductRowData` → `productId`, `productName`, `skuCode`, `barcode`, `unitId`, `unitName`, `unitPrice`, `availableQty`, `imageUrl` | DTO `PosProductRowDto` + `numUnitPrice` | **Y** | — |
| RBAC + Bearer | §4 | `@PreAuthorize("hasAuthority('can_manage_orders')")` + JWT | `apiJson(..., { auth: true })` | **Y** | — |
| UI `/orders/retail` — selector | §1, §3 | — | `POSProductSelector.tsx` — `useQuery` + debounce 400ms; lưới: ảnh / SKU badge fallback, `unitPrice`, dòng *Tồn* (`availableQty`), badge Hết/Sắp hết; click thêm giỏ | **Y** | Mock `mockInventory` đã thay bằng API. |
| Giỏ POS (`unitId` + giá server) | §9 (map `lines`) | — | `OrderItem.unitId`; `useOrderStore` gộp theo `(productId, unitId)`; `POSCartPanel` truyền `unitId` vào `removeItem` / `updateQuantity` | **Y** | Persist key `pos-cart-storage-v2` (tránh dữ liệu cũ thiếu `unitId`). |

## Kết luận (≤5 dòng)

1. **`searchPosProducts`** đã thêm tại `frontend/mini-erp/src/features/orders/api/posProductsApi.ts` và gọi qua `apiJson` + Bearer.  
2. **`POSProductSelector`** dùng TanStack Query, debounce ô tìm, hiển thị `availableQty`, `unitPrice`, `imageUrl` (fallback SKU).  
3. **Giỏ** lưu `unitId` để khớp Task060 sau này; API doc dùng query `search` (không dùng alias `q`).  
4. Lọc **danh mục / vị trí kho** chưa gắn UI (nút Filter chỉ toast hướng dẫn) — mở rộng khi có spec UI.  
5. Build `npm run build` (mini-erp) **thành công**.
