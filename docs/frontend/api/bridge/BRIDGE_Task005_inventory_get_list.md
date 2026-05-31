# BRIDGE — Task005 — `GET /api/v1/inventory` (list + summary)

> **Task:** Task005 | **Path:** `/api/v1/inventory` | **Mode:** wire-fe | **Date:** 25/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp (Y) | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Hợp đồng mở/đóng, query | `API_Task005_inventory_get_list.md` §4–7 | `InventoryController.java` — `GET /api/v1/inventory` | `inventoryApi.ts` → `getInventoryList` | Y | Tham số: `search`, `stockLevel`, `page`, `limit`, `sort` |
| Phản hồi `data` | Mục §7 mẫu 200 | `InventoryListPageData` + DTO tương ứng | Type `InventoryListData` + map → `InventoryItem` | Y | `summary` + `items` + `page`/`limit`/`total` |
| Phân trang / tải thêm màn tồn | §5.2 | BE offset theo `page`/`limit` (20) | `StockPage.tsx` — `useInfiniteQuery` + nối `items`, tải trang kế khi **cuộn tới gần cuối** vùng bảng | Y | Cùng contract API; KPI lấy từ trang 1. |
| Toolbar / bảng | §6 ánh xạ | — | `StockPage` dùng `StockToolbar` / `StockTable` từ server | Y | Nhập/xuất/sửa hàng loạt: dialog + toast, chưa nối API ghi (Task007+). |

**Kết luận:** Màn `StockPage` (`/inventory/stock`) gọi `apiJson` qua `getInventoryList` (Bearer, `VITE_API_BASE_URL`). Một lỗi 401/403 hiển thị toast. BRIDGE tối thiểu — có thỏa Doc Sync bổ sung `samples` sau.
