# BRIDGE — GAP SRS Task029 (+ Task030/031) — Audit sessions Owner HTTP

> **Task:** SRS-Task021-028-GAP-delete (+ approve/reject cùng phiên wire-fe) | **Paths:** `DELETE /api/v1/inventory/audit-sessions/{id}`, `POST …/{id}/approve`, `POST …/{id}/reject` | **Mode:** wire-fe | **Date:** 26/04/2026

**Nguồn sự thật:** [`backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md`](../../../../backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md) §8.1 (dòng 291–293), §6 BR-12/BR-13, §12 GAP; BE `AuditSessionsController` + `AuditSessionService` + `StockReceiptAccessPolicy.assertOwnerOnly`.

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y.

| Hạng mục | SRS / hợp đồng | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| **DELETE** xóa mềm (GAP 029) | §8.1 Task029; BR-12 Owner + `deleted_at`; BR-13 list lọc `deleted_at IS NULL` | `@DeleteMapping("/{id}")` → `softDelete` → `assertOwnerOnly` + `softDeleteSession` | `deleteAuditSessionSoft` trong `auditSessionsApi.ts`; nút **Xóa mềm** + xác nhận trong `AuditSessionDetailDialog` | Y | 200 `data: null` — `apiJson<null>`. Sau thành công: invalidate list/detail + đóng dialog chi tiết. |
| **POST approve** (GAP 030) | §8.1 Task030; OQ-15 `Pending Owner Approval` → `Completed` | `approve` + `assertOwnerOnly`; body `AuditSessionApproveRequest` (`notes` optional max 500) | `postAuditSessionApprove`; nút **Duyệt hoàn thành** khi status chờ Owner | Y | Chỉ hiện khi `useAuthStore.user.role === "Owner"` (khớp claim JWT BE). |
| **POST reject** (GAP 031) | §8.1 Task031; OQ-19 từ chối → `In Progress` | `reject` + `assertOwnerOnly`; `AuditSessionRejectRequest` (`notes` optional) | `postAuditSessionReject`; nút **Từ chối** | Y | — |
| RBAC hiển thị | OQ-16 Owner-only cho các thao tác này | `can_manage_inventory` + `assertOwnerOnly` trong service | UI Owner block chỉ khi `role === "Owner"` | Y | Staff có `can_manage_inventory` vẫn **403** nếu gọi — không hiện block. |
| Vị trí UI | §12 GAP — màn kiểm kê | — | `/inventory/audit` → `AuditPage` → `AuditSessionDetailDialog` | Y | Cùng dialog chi tiết Task023. |
| API markdown Task029 | Chưa có file `API_Task*_delete` | — | — | — | SRS + BE là contract; tạo `API_Task029_*` chỉ khi Owner `Mode=fix-doc`. |

**Kết luận:** Đã nối ba endpoint Owner vào `auditSessionsApi.ts` và **Chi tiết đợt kiểm kê** (`AuditSessionDetailDialog` + mutations `AuditPage`). List BE đã loại `deleted_at` (BR-13) — đợt xóa mềm biến khỏi danh sách sau invalidate.
