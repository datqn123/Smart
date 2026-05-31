# BRIDGE — Task026 — `POST /api/v1/inventory/audit-sessions/{id}/complete`

> **Task:** Task026 | **Path:** `POST /api/v1/inventory/audit-sessions/{id}/complete` | **Mode:** wire-fe | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (mục) | Backend | Frontend (api + UI) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body `requireAllCounted` | `API_Task026_inventory_audit_sessions_complete.md` §5 | `AuditSessionCompleteRequest` — mặc định true | `postAuditSessionComplete` + `AuditSessionCompleteBody`; checkbox trong dialog | Y | Gửi JSON `{ requireAllCounted }`; mặc định `true` nếu omit. |
| Trạng thái sau 200 | §6 (`Completed`) | `complete` → `submitForOwnerApproval` → **`Pending Owner Approval`** | Toast theo `data.status` sau map (ưu tiên “chờ Owner”) | **N** | Doc Task026 §6 vs `AuditSessionService.complete` + `submitForOwnerApproval` — FE theo BE. |
| Điều kiện gọi | §1 / §7 | Chỉ **`In Progress`**; `requireAllCounted` và còn dòng chưa đếm → **409** | Block UI chỉ khi **In Progress**; lỗi 409 → toast | Y | Không gọi khi Pending / Re-check / … |
| Phản hồi 200 | §6 | `AuditSessionDetailData` (như Task023) | Invalidate `list` + `detail` | Y | — |
| UI | UC6 hoàn tất | — | `AuditSessionDetailDialog` — khối “Gửi chờ Owner duyệt” + `AuditPage` `completeMutation` | Y | Ghi số từng dòng vẫn là Task025 (`PATCH …/lines`). |

**Kết luận:** FE gọi đúng path/method/body; toast và kỳ vọng trạng thái căn theo BE (**Pending Owner Approval** sau complete). Cập nhật doc Task026 §6 khi muốn khớp implementation.
