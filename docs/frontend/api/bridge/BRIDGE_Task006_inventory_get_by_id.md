# BRIDGE — Task006 — `GET /api/v1/inventory/{id}`

**Task:** Task006 · **Path:** `/api/v1/inventory/{id}` · **Mode:** wire-fe · **Date:** 26/04/2026  
**Đã đọc `FE_API_CONNECTION_GUIDE.md`:** Y

| Hạng mục | API doc | Backend | Frontend | Khớp | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Method + path + query `include=relatedLines` | `API_Task006_inventory_get_by_id.md` §4–§5 | `InventoryController#getById` | `inventoryApi.getInventoryById` | Y | — |
| Response `data` + `relatedLines` (lô `quantity>0`) | §6 | `InventoryByIdData` | `InventoryDetailResponse` | Y | — |
| Lỗi 400/401/403/404 | §8 | `BusinessException` / security | `apiJson` → `ApiRequestError` | Y | — |
| UI chi tiết lô | §5.5 | — | `StockBatchDetailsDialog` + `StockPage` (`useQuery`) | Y | — |

**Kết luận:** FE gọi `getInventoryById(id, { includeRelatedLines: true })` khi mở dialog; bảng lô = dòng chính + `relatedLines` từ BE; khi lỗi API vẫn hiển thị banner + dữ liệu list. Chạy `npm run build` trong `frontend/mini-erp` trước merge.
