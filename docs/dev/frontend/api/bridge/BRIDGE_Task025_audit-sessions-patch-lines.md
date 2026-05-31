# BRIDGE — Task025 — `PATCH /api/v1/inventory/audit-sessions/{id}/lines`

> **Task:** Task025 | **Path:** `PATCH /api/v1/inventory/audit-sessions/{id}/lines` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body `lines[]` | `API_Task025_inventory_audit_sessions_patch_lines.md` §5 | `AuditLinesPatchRequest` / `AuditLinePatchRow` | `patchAuditSessionLines` + `AuditLinesPatchBody` | Y | `lineId`, `actualQuantity` (≥0), `notes` optional max 500 (BE `@Size`). |
| Phản hồi 200 | §6 | `AuditSessionDetailData` | Invalidate `list` + `detail` sau thành công | Y | — |
| Điều kiện ghi số | §7.1 Pending/In Progress (doc) | BE thực tế: **In Progress** hoặc **Re-check** | `canCountAuditLines` trong `AuditSessionDetailDialog` | Partial | Doc Task025 §1/7.1 vs `AuditSessionService.patchLines` — FE theo BE. |
| UI | UC6 ghi từng dòng | — | Bảng chỉnh trong **Chi tiết** (`LineCountEditorRow`: nhập thực tế + ghi chú + **Lưu** từng dòng) | Y | `AuditPage` `linesPatchMutation` + `onPatchLines`. |
| Pending | — | 409 nếu PATCH lines khi chưa In Progress | Banner hướng dẫn Task024 | Y | — |
| Lỗi 400/409 | §8 | `details` | `linesPatchMutation.onError` toast + description | Y | — |

**Kết luận:** Dialog chi tiết cho phép ghi số khi đợt **Đang kiểm** hoặc **Kiểm lại**; mỗi dòng PATCH một phần tử `lines`. Hoàn tất / áp chênh — task khác.
