# BRIDGE — Task009 — `GET /api/v1/inventory/summary`

**Task:** Task009 · **Path:** `/api/v1/inventory/summary` · **Mode:** wire-fe · **Date:** 26/04/2026  
**Đã đọc `FE_API_CONNECTION_GUIDE.md`:** Y

| Hạng mục | API doc | Backend | Frontend | Khớp | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Method + path + Bearer | `API_Task009_inventory_get_summary.md` §4–§5 | `InventoryController#inventorySummary` | `inventoryApi.getInventorySummary` | Y | — |
| Query `search`, `stockLevel`, `locationId`, `categoryId` (đồng Task005) | §5.2 | `InventoryListQuery.forSummaryFilters` → `loadSummary` | `GetInventorySummaryParams` + gọi từ `StockPage` cùng `debouncedSearch` / `filters.status` | Y | — |
| Response `data` = bốn KPI (camelCase) | §6 | `InventorySummaryData` | `InventoryListSummary` + `mapSummaryToKpis` | Y | — |
| RBAC `can_manage_inventory` | §4 / SRS OQ-3 | `@PreAuthorize` | `jwt` + authority trong test | Y | — |
| UI thẻ KPI | UC6 | — | `StockPage`: `useQuery` key `inventory/v1/summary` + ưu tiên dữ liệu Task009, fallback `data.summary` trang 1; `invalidateQueries` + `Tải lại` refetch summary | Y | — |

**Kết luận:** KPI màn Tồn kho lấy từ Task009 khi API trả về; đồng bộ filter với bảng; sau PATCH 007/008 invalidate cả `list` và `summary`. Chạy `npm run build` trong `frontend/mini-erp` trước merge.
