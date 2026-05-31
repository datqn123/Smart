# BRIDGE — Task008 — `PATCH /api/v1/inventory/bulk`

**Task:** Task008 · **Path:** `/api/v1/inventory/bulk` · **Mode:** wire-fe · **Date:** 26/04/2026  
**Đã đọc `FE_API_CONNECTION_GUIDE.md`:** Y

| Hạng mục | API doc | Backend | Frontend | Khớp | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Method + path + body `{ items: [...] }` | `API_Task008_inventory_bulk_patch.md` §5 | `InventoryController#patchInventoryBulk` | `inventoryApi.patchBulkInventory` | Y | — |
| Mỗi phần tử `id` + partial giống Task007 | §5 | `InventoryBulkPatchJsonParser` + `InventoryPatchService#patchBulkInventory` | `InventoryBulkPatchItemBody`, `buildInventoryBulkPatchItems` + `buildInventoryPatchBody` | Y | — |
| Response `data.updated` + `failed: []` | §6 | `InventoryBulkPatchData` | `InventoryBulkPatchData` (TS) | Y | — |
| Max 100 phần tử có thay đổi sau lọc | §7 / SRS | Parser `MAX_ITEMS` | `BULK_PATCH_MAX_ITEMS = 100` trước khi gọi | Y | — |
| Lỗi 400 `details` (gồm `items[i].…`) | §8 | `BusinessException` + prefix | `ApiRequestError` → toast `message` | Y | — |
| UI sửa nhiều dòng | UC6 | — | `StockEditDialog` + `StockPage.handleEditConfirm` (≥2 dòng → bulk; 1 dòng → Task007) | Y | — |

**Kết luận:** FE gửi chỉ các dòng có field meta đổi; một dòng vẫn dùng `patchInventory` để giữ hành vi Task007. Sau bulk thành công `invalidateQueries` `inventory/v1/list` và `detail`. Chạy `npm run build` trong `frontend/mini-erp` trước merge.
