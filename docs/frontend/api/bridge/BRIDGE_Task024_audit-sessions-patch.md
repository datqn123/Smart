# BRIDGE — Task024 — `PATCH /api/v1/inventory/audit-sessions/{id}`

> **Task:** Task024 | **Path:** `PATCH /api/v1/inventory/audit-sessions/{id}` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body partial | `API_Task024_inventory_audit_sessions_patch.md` §5 | `AuditSessionPatchRequest` (`title`, `notes`, `ownerNotes`, `status`) | `patchAuditSession` — JSON chỉ field gửi; `AuditSessionPatchBody` | Y | BE còn `ownerNotes` + `Re-check` (Owner) — doc Task024 tối thiểu; FE khớp BE thực tế. |
| Phản hồi 200 | §6 | `AuditSessionDetailData` | `apiJson` → map lại list/detail sau invalidate | Y | — |
| Staff | §5 `status` Pending ↔ In Progress | `handleStaffStatusTransition` | `AuditSessionPatchDialog` mode `staff` — Select + meta | Y | Không gửi field không đổi; toast nếu không có diff. |
| Meta-only | — | `Pending Owner Approval`, `Re-check` | Mode `meta` — chỉ title/notes | Y | Cảnh báo không đổi status qua PATCH. |
| Owner Re-check | — | `Completed` + `status=Re-check` + `ownerNotes` | Mode `owner-recheck` khi `user.role === Owner` | Y | Non-Owner Completed → blocked. |
| Lỗi 400/409 | §8 | `BusinessException` + `details` | `patchMutation.onError` toast + description | Y | — |
| UI entry | UC6 | — | `AuditPage` `handleEdit` + `useQuery` chi tiết (chung key với Task023) | Y | Xem / Sửa độc quyền: đóng dialog kia khi mở. |

**Kết luận:** Nút sửa trên bảng mở `AuditSessionPatchDialog`, tải `GET …/{id}` (cache chung `detail` với dialog xem). `patchAuditSession` sau thành công invalidate list + mọi query `detail`. Ghi số dòng / hủy / hoàn tất — task khác (025–027).
