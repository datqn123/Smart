# BRIDGE — Task007 — `PATCH /api/v1/inventory/{id}`

**Task:** Task007 · **Path:** `/api/v1/inventory/{id}` · **Mode:** wire-fe · **Date:** 26/04/2026  
**Đã đọc `FE_API_CONNECTION_GUIDE.md`:** Y

| Hạng mục | API doc | Backend | Frontend | Khớp | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Method + path + JSON partial | `API_Task007_inventory_patch.md` §4–§5 | `InventoryController#patchInventory` | `inventoryApi.patchInventory` | Y | — |
| Body `locationId`, `minQuantity`, `batchNumber`, `expiryDate`, `unitId` | §5.4 | Parser + service | `InventoryPatchBody`, `buildInventoryPatchBody` | Y | — |
| Response `data` = phần tử list Task005 | §6 | `InventoryListItemData` | `InventoryListItemResponse` | Y | — |
| Lỗi 400 `details` | §8 | `BusinessException` | `ApiRequestError` → toast | Y | — |
| UI sửa một dòng | UC6 | — | `StockEditDialog` + `StockPage.handleEditConfirm` (1 dòng); nhiều dòng → toast Task008 | Y | — |

**Kết luận:** FE gọi `patchInventory(id, body)` sau khi user Lưu trong **Sửa thông tin tồn kho** khi chỉ chọn **một** dòng; `buildInventoryPatchBody` chỉ gửi field đổi; sau thành công `invalidateQueries` `inventory/v1/list` và `detail`. Chạy `npm run build` trong `frontend/mini-erp` trước merge.
