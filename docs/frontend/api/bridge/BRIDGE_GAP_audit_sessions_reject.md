# BRIDGE — GAP SRS Task031 — `POST /api/v1/inventory/audit-sessions/{id}/reject`

> **Task:** SRS-Task021-028-GAP-reject | **Path:** `POST /api/v1/inventory/audit-sessions/{id}/reject` | **Mode:** wire-fe | **Date:** 26/04/2026

**Nguồn sự thật:** [`backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md`](../../../../backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md) §8.1 dòng 293 (Task031 GAP), OQ-19 (`Pending Owner Approval` → `In Progress`); BE `AuditSessionsController.reject` → `AuditSessionService.reject`.

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y (`apiJson`, Bearer, `features/inventory/api`).

| Hạng mục | SRS / hợp đồng | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path / method | §8.1 Task031 | `@PostMapping("/{id}/reject")` + `requireJwt` + `@PreAuthorize("hasAuthority('can_manage_inventory')")` | `postAuditSessionReject` → `POST …/${sessionId}/reject` | Y | — |
| Request body | Ghi chú Owner tuỳ chọn (event OQ-13) | `AuditSessionRejectRequest`: `@JsonProperty("notes")` `@Size(max=500)`; body optional → `new AuditSessionRejectRequest(null)` | Cùng type `AuditSessionOwnerNotesBody` với approve; `{}` hoặc `{ notes }` | Y | BE field là `notes`, không phải `reason` (khác stock-receipts reject). |
| RBAC thực thi | OQ-16 Owner-only | `assertOwnerOnly` trong `reject` | Block Owner + nút chỉ khi `user.role === "Owner"` | Y | Staff 403 nếu gọi trực tiếp. |
| Điều kiện trạng thái | OQ-19 | Chỉ **`Pending Owner Approval`** — else **409** «Chỉ từ chối khi đợt đang chờ Owner…» | Nút **Từ chối** cùng điều kiện status với Duyệt trong `AuditSessionOwnerActionsBlock` | Y | `rejectOwnerMutation.onError` → toast message BE. |
| Response 200 `data` | Chi tiết đợt sau từ chối | `AuditSessionDetailData` | `apiJson<AuditSessionDetailData>` | Y | Invalidate list + detail (cùng query key với approve). |
| Message HTTP | — | «Owner đã từ chối — trả về In Progress» | Toast FE: «Owner đã từ chối — đợt trở lại Đang kiểm» | Partial | Literal có thể thống nhất với BE nếu cần. |
| Vị trí UI | [`FEATURES_UI_INDEX.md`](../../../mini-erp/src/features/FEATURES_UI_INDEX.md) — Kiểm kê | — | `/inventory/audit` → `AuditPage.tsx` (`rejectOwnerMutation`, `handleOwnerReject`) → `AuditSessionDetailDialog.tsx` (nút **Từ chối — trả lại đang kiểm**) | Y | Chung ô ghi chú Owner với Duyệt (cùng `ownerNotes` state). |
| API markdown riêng | Chưa có file `API_Task031_audit_sessions_reject.md` (trùng số categories Task031) | — | — | — | Contract: SRS §8.1 + BE; `fix-doc` khi Owner yêu cầu. |

**Grep** `audit-sessions` + `reject` trong `frontend/mini-erp/src/features/inventory`: `auditSessionsApi.ts` (`postAuditSessionReject`), `AuditPage.tsx`, `AuditSessionDetailDialog.tsx`.

**Kết luận:** Wire-fe đã khớp BE cho **Owner từ chối** đợt **chờ Owner** → **In Progress**. Duyệt / xóa mềm: `BRIDGE_GAP_audit_sessions_approve.md`, `BRIDGE_GAP_audit_sessions_delete.md`.
