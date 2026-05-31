# BRIDGE — GAP SRS Task030 — `POST /api/v1/inventory/audit-sessions/{id}/approve`

> **Task:** SRS-Task021-028-GAP-approve | **Path:** `POST /api/v1/inventory/audit-sessions/{id}/approve` | **Mode:** wire-fe | **Date:** 26/04/2026

**Nguồn sự thật:** [`backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md`](../../../../backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md) §8.1 dòng 292 (Task030 GAP), OQ-15 (`Pending Owner Approval` → `Completed`); BE `AuditSessionsController.approve` → `AuditSessionService.approve`.

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y (`apiJson`, Bearer, `features/inventory/api`).

| Hạng mục | SRS / hợp đồng | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path / method | §8.1 Task030 | `@PostMapping("/{id}/approve")` + `requireJwt` + `@PreAuthorize("hasAuthority('can_manage_inventory')")` | `postAuditSessionApprove` → `POST …/${sessionId}/approve` | Y | — |
| Request body | Ghi chú Owner tuỳ chọn (event OQ-13) | `AuditSessionApproveRequest`: `@JsonProperty("notes")` `@Size(max=500)`; `@RequestBody(required = false)` → default `new AuditSessionApproveRequest(null)` | `AuditSessionOwnerNotesBody`; gửi `{}` hoặc `{ notes }` sau trim/slice 500 | Y | Không gửi field thừa (BE record `ignoreUnknown = true`). |
| RBAC thực thi | OQ-16 Owner-only cho chuyển trạng thái tới Completed | `StockReceiptAccessPolicy.assertOwnerOnly(jwt)` trong `approve` | Nút **Duyệt hoàn thành** chỉ trong block Owner khi `useAuthStore((s) => s.user?.role === "Owner")` | Y | Staff không thấy nút; nếu gọi API vẫn **403** từ BE. |
| Điều kiện trạng thái | OQ-15 | Chỉ khi lock session có status **`Pending Owner Approval`** — else **409** «Chỉ duyệt khi đợt đang chờ Owner…» | Nút Duyệt/Từ chối chỉ render khi `session.status === "Pending Owner Approval"` | Y | Sai trạng thái → `approveOwnerMutation.onError` + toast message BE. |
| Response 200 `data` | Chi tiết đợt sau duyệt | `AuditSessionDetailData` (`getById`) | `apiJson<AuditSessionDetailData>` | Y | Invalidate `["inventory","audit-sessions","v1","list"]` + `["…","detail"]` để badge/cột list cập nhật. |
| Message HTTP | — | `ApiSuccessResponse`: «Owner đã duyệt hoàn thành» | Toast FE: «Owner đã duyệt — đợt chuyển Hoàn thành» (copy UX) | Partial | Có thể đồng bộ literal với BE nếu muốn. |
| Vị trí UI | `FEATURES_UI_INDEX` — Kiểm kê | — | `/inventory/audit` → `AuditPage.tsx` (`approveOwnerMutation`, `handleOwnerApprove`) → `AuditSessionDetailDialog.tsx` (`AuditSessionOwnerActionsBlock`, nút **Duyệt hoàn thành**) | Y | Cùng dialog chi tiết Task023; không Glob thêm `features/`. |
| API markdown riêng | Chưa có `API_Task030_audit_sessions_approve.md` (trùng số categories) | — | — | — | Contract: SRS §8.1 + BE; thêm file API khi `Mode=fix-doc` nếu Owner yêu cầu. |

**Grep** `approve` + audit path trong `frontend/mini-erp/src`: `auditSessionsApi.ts` (`postAuditSessionApprove`), `AuditPage.tsx`, `AuditSessionDetailDialog.tsx`.

**Kết luận:** Wire-fe đã khớp BE cho **Owner duyệt** đợt **chờ Owner** → **Completed**; Từ chối / Xóa mềm là endpoint khác — xem `BRIDGE_GAP_audit_sessions_delete.md`.
