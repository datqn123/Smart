# BRIDGE — Task028 — `POST /api/v1/inventory/audit-sessions/{id}/apply-variance`

> **Task:** Task028 | **Path:** `POST /api/v1/inventory/audit-sessions/{id}/apply-variance` | **Mode:** verify | **Date:** 26/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y (envelope `apiJson`, Bearer, `features/*/api`).

| Hạng mục | API doc (`API_Task028_inventory_audit_sessions_apply_variance.md`) | Backend | Frontend (`frontend/mini-erp/src`) | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Path / method / Bearer | §3 | `AuditSessionsController` `@PostMapping("/{id}/apply-variance")` + `requireJwt`, `@PreAuthorize("hasAuthority('can_manage_inventory')")` | **Không** có `Grep` hit `apply-variance` / `applyVariance` | **N** | `Mode=wire-fe`: thêm hàm trong `features/inventory/api/auditSessionsApi.ts` + UI (vd. `AuditPage` / `AuditSessionDetailDialog`). |
| Body `reason` | §4 bắt buộc, audit | `AuditApplyVarianceRequest`: `@JsonProperty("reason")` `@NotBlank` `@Size(max=500)` | — | Y | — |
| Body `mode` | §4 `delta` \| `set_actual` | `mode` optional; `@Pattern(^(delta\|set_actual)$)`; `modeOrDefault()` → `"delta"` | — | Y | Gửi thiếu `mode` → BE coi như `delta`. |
| Unknown JSON fields | — | `@JsonIgnoreProperties(ignoreUnknown = false)` trên record request | — | — | FE chỉ gửi `reason` + `mode` (tránh 400 deserialize). |
| Điều kiện session | §6.1: `Completed` | `applyVariance`: `!ST_COMPLETED` → **409** «Chỉ áp chênh lệch khi đợt đã Completed» | — | Y | Khớp SRS C8 / OQ-15. |
| Chọn dòng áp | §6.1 bước 3 | `loadLinesToApply`: `is_counted = TRUE`, `actual_quantity IS NOT NULL`; service lọc `(actual - system) ≠ 0` | — | Y | — |
| Idempotency (BR-6) | §6.1 bước 9 — 409 «Đã áp chênh lệch» | Các dòng còn lệch nhưng `variance_applied_at` đã set hết → **409** «Đã áp chênh lệch cho đợt này»; cột `variance_applied_at` + `setVarianceAppliedAt` | — | Y | Không double-apply toàn đợt khi còn snapshot lệch đã mark. |
| Không còn dòng lệch | — (không nêu rõ 200 rỗng) | `withVar.isEmpty()` → **200** `appliedLines: []` | — | **Partial** | Hợp lệ: đợt Completed nhưng không có dòng `(actual−system)≠0` → không lỗi, không đổi tồn. |
| `quantity >= 0` (BR-7) | §6.1 | `newQty < 0` → **409** «Số lượng tồn sau điều chỉnh không được âm» | — | Y | — |
| Lock / race (SRS §C8) | §6.1 FOR UPDATE session + inventory | `lockSession` SQL `… FOR UPDATE`; `lockInventoryQuantity` `SELECT quantity … FOR UPDATE` | — | Y | — |
| OQ-5 làm tròn | Mục tiêu §1 (DECIMAL vs INT) | `computeNewQuantity`: `HALF_UP` int cho `delta` và `roundedActual` (`set_actual`) | — | Y | BE chốt hướng A (int sau làm tròn). |
| `InventoryLogs` | §1 khuyến nghị `ADJUSTMENT` | `insertInventoryLog` → `action_type = 'ADJUSTMENT'` | — | Y | Khớp SRS G7 tinh thần. |
| `reference_note` | §6 / SRS G7 ≤255 | `buildApplyReferenceNote` + `REF_NOTE_MAX = 255` truncate | — | Y | Prefix `auditSession=…;line=…;` + `reason`. |
| `SystemLogs` / Task012 | §2, §6.1 bước 7 | Trong `applyVariance` **không** gọi `insertEvent` / SystemLogs (chỉ inventory + line flag + log tồn) | — | **N** | Doc mô tả rộng hơn BE hiện tại; cập nhật `API_Task028` §6 hoặc bổ sung BE nếu cần audit trail đồng bộ Task022–027. |
| RBAC Owner-only | — (doc §3 Owner/Staff) | Chỉ `can_manage_inventory`, **không** `assertOwnerOnly` | — | Y | Khớp SRS OQ-16 cho `apply-variance`. |
| Response 200 `data` | §5 | `AuditApplyVarianceData` (`sessionId`, `appliedLines[]`); `AuditApplyVarianceLineResult` (`lineId`, `inventoryId`, `deltaQty`, `quantityAfter`) | — | Y | Type TS wire-fe nên bám record này. |
| Message 200 | §5 ví dụ | Controller: `ApiSuccessResponse.of(data, "Đã áp chênh lệch kiểm kê lên tồn kho")` | — | Y | — |
| Zod §8 | `reason` max 500, `mode` enum default `delta` | Khớp validation chính | — | Y | — |

**Kết luận (verify):** Hợp đồng HTTP request/response và luồng nghiệp vụ chính (Completed, lock, mode, làm tròn, ADJUSTMENT, idempotent 409) **khớp** giữa `API_Task028` và BE. **Chưa** có code FE gọi endpoint. **Lệch:** BE không ghi `SystemLogs` trong `applyVariance` như mục §6 doc; trường hợp **200 với `appliedLines: []`** khi không có dòng lệch — doc nên làm rõ. Bước tiếp: `Mode=wire-fe` theo `API_BRIDGE_AGENT_INSTRUCTIONS.md` (api + dialog + `BRIDGE` cột FE).
