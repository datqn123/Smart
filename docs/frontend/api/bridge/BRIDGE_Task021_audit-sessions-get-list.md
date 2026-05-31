# BRIDGE — Task021 — `GET /api/v1/inventory/audit-sessions`

> **Task:** Task021 | **Path:** `GET /api/v1/inventory/audit-sessions` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Query / envelope | `API_Task021_inventory_audit_sessions_get_list.md` §5–6 | `AuditSessionsController` `list`, `can_manage_inventory`, JWT | `auditSessionsApi.ts` — `getAuditSessionList` (`apiJson`, `auth: true`) | Y | `search`, `status` (bỏ khi `all`), `dateFrom`, `dateTo`, `page`, `limit`. |
| `data.items` aggregate | §6 camelCase | `AuditSessionListItemData` / JDBC list | `mapAuditSessionListItemToUi` → `AuditSession` (`items: []`, `totalLines`, `countedLines`, `varianceLines`) | Y | Bảng + panel mở rộng dùng aggregate; dòng chi tiết chờ Task023. |
| Lỗi 400 `dateRange` | §8 / BE `AuditSessionListQuery` | `details.dateRange` | Toast `dateRange` khi 400 | Y | Giống Task013. |
| RBAC 401/403 | §4 | `requireJwt` + `@PreAuthorize` | Toast từ envelope | Y | — |
| Trạng thái BE | SRS v2 | `Pending Owner Approval`, `Re-check` | `AuditStatus` + `StatusBadge` + select lọc | Y | Doc Task021 §5.2 chỉ liệt kê 5 giá trị; BE mở rộng — FE đã thêm option + badge. |

**Kết luận:** `AuditPage` (`/inventory/audit`) dùng `useInfiniteQuery` + sentinel cuộn, gọi `getAuditSessionList`. `AuditSessionsTable` hiển thị tiến độ / lệch từ aggregate API; panel mở rộng không có `items` từ list — ghi chú Task023. Tạo đợt / chi tiết / xóa vẫn toast placeholder — ngoài scope Task021.
