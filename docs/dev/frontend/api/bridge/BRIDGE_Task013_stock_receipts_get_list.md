# BRIDGE — Task013 — `GET /api/v1/stock-receipts`

> **Task:** Task013 | **Path:** `GET /api/v1/stock-receipts` | **Mode:** wire-fe | **Date:** 25/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Query / envelope | `API_Task013_stock_receipts_get_list.md` §5–7 | `StockReceiptsController` — `GET /api/v1/stock-receipts`, `can_manage_inventory`, `requireJwt` | `stockReceiptsApi.ts` — `getStockReceiptList` (`apiJson`, `auth: true`) | Y | `search`, `status`, `dateFrom`, `dateTo`, `supplierId`, `page`, `limit`, `sort` (`id:desc` mặc định FE). |
| `data.items` | §7 camelCase | JDBC + DTO list | `mapStockReceiptListItemToUi` → `StockReceipt` (`lineCount`, `details: []` list) | Y | Chi tiết dòng Task015; dialog list hiển thị placeholder. |
| Lỗi 400 `dateRange` | SRS / PO OQ-4 | `StockReceiptListQuery` → `details.dateRange` | Toast `details.dateRange` khi 400 | Y | — |
| RBAC 401/403 | §9 | Giống inventory | Toast message từ envelope | Y | — |
| Tìm kiếm ô chính | §5.2 `search` | Chỉ `receipt_code` / `invoice_number` ILIKE | Placeholder UI ghi rõ không gồm tên NCC | Partial | Lọc tên NCC: nhập **số ID** gửi `supplierId`; hoặc lọc tên trên **dữ liệu đã tải** (chữ). |

**Kết luận:** `InboundPage` (`/inventory/inbound`) dùng `useInfiniteQuery` + sentinel cuộn, gom trang qua `getStockReceiptList`. `ReceiptTable` / dialog dùng `lineCount` khi không có `details`. Form tạo/sửa/xóa vẫn mock/local — ngoài scope Task013.
