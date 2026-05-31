# BRIDGE — Task023 — `GET /api/v1/inventory/audit-sessions/{id}`

> **Task:** Task023 | **Path:** `GET /api/v1/inventory/audit-sessions/{id}` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path + envelope | `API_Task023_inventory_audit_sessions_get_by_id.md` §5–6 | `AuditSessionsController.getById`, `AuditSessionDetailData` + lines | `getAuditSessionById` (`apiJson`, `auth: true`) | Y | — |
| `items[]` → `AuditItem` | §6 camelCase | `AuditSessionLineItemData` (BigDecimal → JSON number/string) | `mapAuditSessionLineToAuditItem` + `mapAuditSessionDetailToUi` | Y | `actualQuantity` null → optional; `variance` / `variancePercent` số. |
| Phụ trợ header | — | `events`, `ownerNotes`, `cancelReason` | Type `AuditSessionDetailData` (optional); dialog chưa render `events` | Partial | Có thể bổ sung timeline sau (SRS OQ-13). |
| UI | UC6 xem dòng | — | `AuditSessionDetailDialog` + `AuditPage` (`useQuery`, `onView` từ `AuditSessionsTable`) | Y | `listHint` giữ mã/tên khi đang fetch. |
| Lỗi 404/401/403 | §8 | Resource server + RBAC | `isError` + message trong dialog | Y | — |

**Kết luận:** Nút mắt / `onView` mở dialog, tải chi tiết theo `id`, bảng read-only các dòng kiểm. Sửa đợt / patch dòng — ngoài scope Task023.
