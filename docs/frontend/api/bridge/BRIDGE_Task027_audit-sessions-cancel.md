# BRIDGE — Task027 — `POST /api/v1/inventory/audit-sessions/{id}/cancel`

> **Task:** Task027 | **Path:** `POST /api/v1/inventory/audit-sessions/{id}/cancel` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body | §4 `{ "cancelReason": "…" }` | `AuditSessionCancelRequest` — `@JsonProperty("cancelReason")` `@NotBlank` `@Size(max=1000)` | `postAuditSessionCancel` + `AuditSessionCancelBody`; dialog nhập lý do | Y | — |
| Trạng thái cho phép | §1 Pending / In Progress / Pending Owner | Cùng bộ ba trong `AuditSessionService.cancel` | `canRequestAuditSessionCancel` + disable nút thùng rác | Y | **Re-check** không hủy bằng endpoint này (409 nếu gọi). |
| 200 response | §5 `Cancelled` | `AuditSessionDetailData` sau `getById` | Invalidate list + detail; đóng dialog | Y | — |
| Zod mẫu §8 | `reason` optional | — | FE dùng `cancelReason` theo BE/doc §4 | **N** | Mục §8 doc sai field / bắt buộc so với §4 và BE. |
| UI | UC6 hủy | — | `AuditSessionsTable` → `onRequestCancel` → `AuditPage` `cancelMutation` + `AuditSessionCancelDialog` | Y | Icon thùng rác = **hủy đợt** (không soft-delete). Ghi số dòng = Task025. |

**Kết luận:** FE gọi đúng path/method/body và đồng bộ điều kiện trạng thái với BE. Sửa `API_Task027` §8 (Zod) cho khớp `cancelReason` bắt buộc nếu muốn doc thống nhất.
