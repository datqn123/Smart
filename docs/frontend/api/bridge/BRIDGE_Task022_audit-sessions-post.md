# BRIDGE — Task022 — `POST /api/v1/inventory/audit-sessions`

> **Task:** Task022 | **Path:** `POST /api/v1/inventory/audit-sessions` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body JSON | `API_Task022_inventory_audit_sessions_post.md` §5, §9 Zod | `AuditSessionCreateRequest` + `AuditScopeBody` (`mode`, `locationIds` / `categoryId` / `inventoryIds`) | `auditSessionsApi.ts` — `postAuditSession`, types `AuditSessionCreateBody` | Y | `notes` gửi `null` khi trống; camelCase khớp BE. |
| Phản hồi | §6 `201` + envelope | `AuditSessionsController.create` → `AuditSessionDetailData` | `apiJson` → `AuditSessionDetailResponse` (tối thiểu `auditCode`, `id`, `items`) | Y | Toast + invalidate list Task021. |
| Auth / RBAC | §4 | `Bearer` + `can_manage_inventory` | `auth: true` | Y | — |
| Form UI | §5 ví dụ | — | `AuditSessionCreateForm.tsx` + `AuditPage` (`useMutation`, mở dialog) | Y | Chọn `scope.mode` + nhập ID (CSV/ xuống dòng); validate client Zod. |
| Lỗi 400 | §8 | `BusinessException` + `details` | `onError` toast + `description` từ `details` | Y | — |

**Kết luận:** Nút **Tạo đợt kiểm kê** trên `AuditPage` mở dialog form, gọi `postAuditSession`, thành công thì làm mới infinite list. Xem/sửa/xóa dòng kiểm trên bảng vẫn placeholder (Task023+).
