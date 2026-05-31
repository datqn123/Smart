# SRS — Kiểm kê kho (đợt kiểm kê) — REST Task021–Task028

> **File (Spring / `smart-erp`):** `backend/docs/srs/SRS_Task021-028_inventory-audit-sessions.md`  
> **Người soạn:** Agent BA (+ SQL Draft)  
> **Ngày:** 26/04/2026  
> **Trạng thái:** Draft  
> **PO duyệt (khi Approved):** *chưa*

---

## 0. Đầu vào & traceability

| Nguồn | Đường dẫn / ghi chú |
| :--- | :--- |
| API Task021 | [`../../../frontend/docs/api/API_Task021_inventory_audit_sessions_get_list.md`](../../../frontend/docs/api/API_Task021_inventory_audit_sessions_get_list.md) |
| API Task022 | [`../../../frontend/docs/api/API_Task022_inventory_audit_sessions_post.md`](../../../frontend/docs/api/API_Task022_inventory_audit_sessions_post.md) |
| API Task023 | [`../../../frontend/docs/api/API_Task023_inventory_audit_sessions_get_by_id.md`](../../../frontend/docs/api/API_Task023_inventory_audit_sessions_get_by_id.md) |
| API Task024 | [`../../../frontend/docs/api/API_Task024_inventory_audit_sessions_patch.md`](../../../frontend/docs/api/API_Task024_inventory_audit_sessions_patch.md) |
| API Task025 | [`../../../frontend/docs/api/API_Task025_inventory_audit_sessions_patch_lines.md`](../../../frontend/docs/api/API_Task025_inventory_audit_sessions_patch_lines.md) |
| API Task026 | [`../../../frontend/docs/api/API_Task026_inventory_audit_sessions_complete.md`](../../../frontend/docs/api/API_Task026_inventory_audit_sessions_complete.md) |
| API Task027 | [`../../../frontend/docs/api/API_Task027_inventory_audit_sessions_cancel.md`](../../../frontend/docs/api/API_Task027_inventory_audit_sessions_cancel.md) |
| API Task028 | [`../../../frontend/docs/api/API_Task028_inventory_audit_sessions_apply_variance.md`](../../../frontend/docs/api/API_Task028_inventory_audit_sessions_apply_variance.md) |
| API design | [`../../../frontend/docs/api/API_PROJECT_DESIGN.md`](../../../frontend/docs/api/API_PROJECT_DESIGN.md) §4.15 |
| UC / tồn kho | [`../../../frontend/docs/UC/Database_Specification.md`](../../../frontend/docs/UC/Database_Specification.md) §16 `Inventory` |
| Flyway | [`../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql); migration bổ sung [`../../smart-erp/src/main/resources/db/migration/V11__inventory_audit_sessions_cancel_reason.sql`](../../smart-erp/src/main/resources/db/migration/V11__inventory_audit_sessions_cancel_reason.sql) (`cancel_reason` — OQ-4) |
| Brief PO (nghiệp vụ v2) | 26–27/04/2026 — chờ duyệt + approve; Owner Re-check / xóa mềm / assertOwnerOnly (OQ-16); events + owner_notes |

---

## 1. Tóm tắt điều hành

- **Vấn đề:** Cần một **bộ REST thống nhất** cho UC6 — danh sách đợt kiểm kê, tạo đợt + snapshot dòng từ `Inventory`, đọc chi tiết, cập nhật meta/trạng thái, ghi số thực tế từng dòng, hoàn tất, hủy, áp chênh lệch lên tồn — thay mock FE.
- **Mục tiêu:** Mô tả nghiệp vụ, máy trạng thái, transaction, toàn vẹn DB; **hợp nhất** lệch giữa các file API markdown và **schema Flyway thực tế** (tên bảng, kiểu khóa, cột idempotency).
- **Đối tượng:** Nhân viên (Staff) và Owner — **đọc** danh sách/chi tiết: mọi user được phép vào chức năng kiểm kê và xem mọi bản ghi (theo quyết định OQ-1); **ghi / xóa / chuyển trạng thái đặc biệt** tách theo vai trò (§6, §4 OQ).

---

## 1.1 Giao diện Mini-ERP

| Mục | Giá trị |
| :--- | :--- |
| Nhãn menu | Kiểm kê |
| Route | `/inventory/audit` |
| Page (export) | `AuditPage` |
| Path file page | `frontend/mini-erp/src/features/inventory/pages/AuditPage.tsx` |
| Component danh sách | `AuditSessionsTable.tsx` — `frontend/mini-erp/src/features/inventory/components/AuditSessionsTable.tsx` |

Chi tiết hợp đồng HTTP: `API_Task021`–`028` (và GAP Task029 xóa — §12). **GAP UI:** nếu sau này tách route chi tiết (`/inventory/audit/:id`) chưa có trong [`FEATURES_UI_INDEX.md`](../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md) thì cập nhật index khi Dev chốt navigation.

---

## 2. Bóc tách nghiệp vụ (capabilities)

| # | Capability | Method + path | Kết quả |
| :---: | :--- | :--- | :--- |
| C1 | Phân trang + lọc danh sách đợt; **mọi user có quyền module** xem mọi bản ghi (không giới hạn theo người tạo) | `GET /api/v1/inventory/audit-sessions` | `200` + `items[]` |
| C2 | Tạo đợt `Pending`, sinh `audit_code` (KK-YYYY-NNNN), snapshot dòng theo `scope` | `POST /api/v1/inventory/audit-sessions` | `201` + shape Task023 |
| C3 | Đọc một đợt + dòng snapshot + **`owner_notes` + `events[]`** (OQ-13). *`parent_session_id`/session con: **v2** (OQ-17 huỷ v1).* | `GET /api/v1/inventory/audit-sessions/{id}` | `200` / `404` |
| C4 | PATCH meta + trạng thái: Staff `Pending`↔`In Progress` (OQ-12); Owner **Completed→Re-check** (OQ-10, **guard** OQ-11); field ghi chú tách **OQ-13** | `PATCH /api/v1/inventory/audit-sessions/{id}` | `200` / `403` / `409` |
| C5 | Ghi `actual_quantity` / `notes` dòng; **Staff** khi `In Progress`, **`Re-check`** (OQ-11, chưa apply), không chỉnh dòng phiếu đã `Completed`+đã apply | `PATCH /api/v1/inventory/audit-sessions/{id}/lines` | `200` |
| C6 | **Staff** gửi kết quả đếm (OQ-12): `POST …/complete` chuyển tới **chờ Owner duyệt** (tên `status` = **OQ-15**), **không** set `Completed` cuối cùng cho đến khi Owner duyệt (OQ-15). *Nếu PO bác giả định BA (mâu thuẫn OQ-3), revert theo bảng PO.* | `POST /api/v1/inventory/audit-sessions/{id}/complete` | `200` |
| C7 | Hủy đợt `Cancelled` | `POST /api/v1/inventory/audit-sessions/{id}/cancel` | `200` |
| C8 | Áp chênh lệch lên `Inventory` + `InventoryLogs`, idempotent theo dòng | `POST /api/v1/inventory/audit-sessions/{id}/apply-variance` | `200` / `409` nếu đã apply |
| C9 | **Owner** soft-delete (`deleted_at`) — **`assertOwnerOnly`** (OQ-16). | **`DELETE` [GAP — §12]** `/api/v1/inventory/audit-sessions/{id}` | `204` / `404` / `409` |
| C10 | **Owner** duyệt: `Pending Owner Approval` → `Completed` — **`POST …/approve`** (OQ-15) | **`POST /api/v1/inventory/audit-sessions/{id}/approve`** [GAP Task030] | `200` / `403` / `409` |

**Máy trạng thái (SRS v4 — OQ-15 + OQ-17; literal chờ duyệt = `Pending Owner Approval`):**

```text
                              ┌── cancel (Task027) ──► Cancelled
                              │
Pending ──PATCH (Staff)──► In Progress ──POST complete (Staff, Task026)──► Pending Owner Approval
   │           │                              │
   │           └── cancel ────────────────────┘
   └── cancel ─────────────────────────────────────────────────────────┘

Pending Owner Approval ──POST approve (Owner, C10)──► Completed
      │
      └── (Owner từ chối — **OQ-19** nếu cần)

Completed ──Owner PATCH──► Re-check **chỉ khi chưa apply-variance** (OQ-11); Staff PATCH lines trên **cùng** phiếu (không session con — OQ-17)

Completed ──POST apply-variance (Task028)──► (tồn đã chỉnh; không Re-check session này — OQ-11)
```

- **`Re-check` (OQ-10):** chỉ áp dụng **trước** `apply-variance` trên session đó; sau apply → Owner chỉ **ghi chú / events** (OQ-13).
- **Đa vòng / session con (OQ-8 A):** **huỷ v1** theo **OQ-17** — không `parent_session_id` bắt buộc.
- **`Cancelled`:** chỉ **Task027**; **`Completed`:** sau Owner (C10), không hủy qua PATCH Task024 (giữ **G3**).
- **Đọc (C1/C3):** `WHERE deleted_at IS NULL` (OQ-9); không ẩn theo `created_by`.

---

## 3. Phạm vi

### 3.1 In-scope

- Tám endpoint Task021–028; envelope JSON dự án (`success`, `data`, `message`, `error`, `details`).
- **Bổ sung nghiệp vụ v2:** RBAC + **OQ-16** (assert Owner trong service); trạng thái **OQ-15** (`Pending Owner Approval`); Owner **POST approve** + **DELETE** soft; **Completed→Re-check** + lines (OQ-11); events + `owner_notes` (OQ-13); **OQ-17** không bắt buộc `parent_session_id` v1.
- **Endpoint GAP:** `API_Task029` (DELETE), `API_Task030` (`POST …/approve`) — §12.
- Validation query/body theo từng API doc; mã lỗi: 400, 401, 403, 404, 409, 500 theo từng luồng.

### 3.2 Out-of-scope

- Báo cáo kiểm kê tổng hợp đa cửa hàng; import CSV; quyền phê duyệt riêng (trừ khi OQ chốt).
- **Task012** notify Owner — chỉ ghi nhắc trong Task028 API; không bắt buộc trong SRS v1.

---

## 4. Câu hỏi làm rõ cho PO (Open Questions)

> BA không tự chốt thay PO. Các mục **Quyết định BA đã hợp nhất** (§12) không nằm ở đây.  
> **Đã có quyết định PO** cho OQ-8…18 (và OQ-3\*) tại bảng *Trả lời PO*; BA đã hợp nhất vào §2, §4.1, §6, §10. **§4.2:** chỉ còn câu hỏi gợi ý (không blocker) nếu có.

| ID | Câu hỏi | Ảnh hưởng nếu không trả lời | Blocker? |
| :--- | :--- | :--- | :---: |
| **OQ-1** | **RBAC cụ thể:** PO đã hướng “mọi user dùng chức năng kiểm kê / Permission all User” — cần map sang **JWT claim cụ thể** (xem **OQ-14**). Có endpoint nào bắt `can_approve` / `role=Owner` tách biệt không? | 403 rule không nhất quán | Đã có hướng; **chi tiết claim = OQ-14** |
| **OQ-2** | **Giới hạn song song:** Có chặn tạo đợt mới / chuyển `In Progress` khi đã tồn tại **một** đợt `In Progress` toàn hệ thống / theo `location` không? (Task022 gợi ý 409 — tùy PM.) | 409 vs luôn cho phép | Không |
| **OQ-3** | **Hoàn tất (Task026):** Chỉ cho `In Progress` → `Completed`, hay cho phép **`Pending` → `Completed`** (bỏ bước đếm trong một số quy trình)? | AC test complete từ Pending | **Có** |
| **OQ-4** | **Hủy (Task027):** PO chốt cột `cancel_reason`; migration tham chiếu **`V11__inventory_audit_sessions_cancel_reason.sql`**. Còn mở: body API có bắt buộc `cancelReason` tách khỏi `notes` không? | Hợp đồng Task027 vs UI | Không |
| **OQ-5** | **Áp chênh lệch (Task028):** `Inventory.quantity` là **INT**; `actual_quantity` / `system_quantity` là **DECIMAL(12,4)**. Khi apply: **(A)** làm tròn HALF_UP về int; **(B)** nâng cột `inventory.quantity` lên NUMERIC (migration). | Lệch số lượng so với đếm thực tế | **Có** |
| **OQ-6** | **`SystemLogs`** sau các bước ghi (Task022,024,025,026,027,028): insert **bắt buộc** trong transaction hay **best-effort** sau commit (lỗi log không fail request)? | Hành vi hiếm / vận hành | Không |
| **OQ-7** | **Snapshot dòng có `quantity = 0`:** Task022 ghi “mặc định vẫn snapshot”; có policy **loại bỏ** dòng tồn 0 khỏi đợt kiểm không? | Số dòng đợt / UX đếm | Không |
| **OQ-8** | **“Một đợt chia 2 phần kiểm kê”** lưu thế nào? (A) Nhiều bản ghi `inventoryauditsessions` cha-con `parent_session_id`; (B) Một session + bảng con **`inventory_audit_rounds`** (số vòng, note, trạng thái từng vòng); (C) Một session + **`JSONB` timeline** trên header; (D) Khác. | Shape Task023/C3, migration | **Có** |
| **OQ-9** | **Xóa session (C9):** hard `DELETE` cascade lines hay **soft-delete** (`deleted_at`)? Staff có được xóa khi `Completed` / đã `apply-variance` không? Có cần Owner đồng ý không? | Toàn vẹn tồn + audit | **Có** |
| **OQ-10** | Chuỗi **`status`** DB cho “kiểm tra lại”: thêm enum mới (vd. `Re-check`) và **sửa CHECK** `inventoryauditsessions`, hay dùng từ khóa khác đồng bộ UI? | PATCH/complete/list filter | **Có** |
| **OQ-11** | Khi Owner đã chuyển **Completed → Re-check**, Staff có được **sửa lại** `actual_quantity` / `is_counted` trên **cùng dòng** snapshot cũ, hay bắt buộc **vòng mới** (phụ thuộc OQ-8)? `apply-variance` đã chạy thì xử lý thế nào? | Task025/028, migration | **Có** |
| **OQ-12** | **“Trạng thái cơ bản”** Staff được PATCH (Task024) gồm những giá trị nào ngoài `Pending`↔`In Progress`? Có cho Staff đặt `In Progress` → `Pending` rollback không? | 409 vs cho phép | Không |
| **OQ-13** | **Ghi chú Owner** (yêu cầu kiểm tra lại, đẩy tiến độ) vs **ghi chú Staff** / ghi chú theo vòng: dùng chung cột `notes` hay tách **`owner_notes`** + bảng **`inventory_audit_session_events`** (type, user_id, body, created_at)? | GET chi tiết + SQL §10 | **Có** |
| **OQ-14** | OQ-1 “Permission all User”: hiểu là **mọi user đăng nhập** của cửa hàng, hay vẫn cần claim **`can_manage_inventory`** (nhưng ai có claim đều xem hết)? | JWT 403 | Không |

**Trả lời PO (điền khi chốt):**

| ID | Quyết định PO | Ngày |
| :--- | :--- | :--- |
| OQ-1 | Ai cũng làm được chức năng kiểm kê này, Permission all User | |
| OQ-2 | Có | |
| OQ-3 | Chỉ cho `In Progress` → `Completed` | |
| OQ-4 | **migration thêm cột** `cancel_reason` | |
| OQ-5 | **(A)** làm tròn HALF_UP về int | |
| OQ-6 | Tạm thời chưa làm SysLogs | |
| OQ-7 | Không loại bỏ | |
| OQ-8 | (A) — **v1 không triển khai** `parent_session_id` (**OQ-17**); có thể mở lại v2 | 27/04/2026 |
| OQ-9 | **soft-delete** (`deleted_at`). **Chỉ Owner** được gọi xóa (**OQ-16**); bỏ quy định cũ “Staff không xóa khi hoàn thành”. | 27/04/2026 |
| OQ-10 | Chuỗi **`status`** DB cho “kiểm tra lại”: thêm enum mới (vd. `Re-check`) và **sửa CHECK** `inventoryauditsessions` | |
| OQ-11 | **Sau OQ-17 (v1):** không dùng session con — đếm lại trên **cùng** phiếu khi Owner `Completed`→`Re-check`. **Sau `apply-variance`:** không `Re-check`/mở lại đếm; Owner chỉ ghi chú/events. **Trước khi apply:** Owner `Completed`→`Re-check` + Staff `PATCH lines` (OQ-10, OQ-13). | 27/04/2026 |
| OQ-12 | **Luồng duyệt Owner:** (1) Mới tạo → **chờ kiểm**; (2) vào kho đếm → **đang kiểm**; (3) Staff nhấn hoàn thành → **chờ duyệt** (thông báo Owner); (4) Owner xác nhận → **hoàn thành**. (*Gõ PO: stautus → status*) | 26/04/2026 |
| OQ-13 | **Tách** lưu trữ: ghi chú / timeline Owner–Staff **không** gom hết vào một `notes` — dùng **`owner_notes` (hoặc tương đương) + bảng `inventory_audit_session_events`** (OQ-13 gốc). | 26/04/2026 |
| OQ-14 | **Mọi user** vào xem và thao tác **Staff**; các chức năng **chỉ Owner** (duyệt hoàn thành, `Completed`→`Re-check` khi được phép OQ-11, v.v.) — chi tiết map JWT: **OQ-16**. | 26/04/2026 |
| OQ-15 | **Chuỗi `status` (DB, có khoảng trắng như V1):** `Pending` (chờ kiểm) → `In Progress` (đang kiểm) → **`Pending Owner Approval`** (chờ duyệt) → `Completed` (sau Owner). **Task026:** `In Progress` → `Pending Owner Approval` (không set `Completed` trực tiếp). **Owner duyệt:** endpoint mới **`POST /api/v1/inventory/audit-sessions/{id}/approve`** (Task030; có thể thêm body tùy chọn). **PATCH Task024** chỉ dùng cho meta / chuyển trạng thái Staff (`Pending`↔`In Progress`), **không** thay cho approve. | 27/04/2026 |
| OQ-16 | **Chỉ Owner (kiểm tra `Jwt` claim `role` = Owner, không phân biệt hoa thường — cùng pattern `StockReceiptAccessPolicy.assertOwnerOnly`):** (1) mọi thao tác đưa phiếu tới **`Completed`** (gọi `POST …/approve` từ `Pending Owner Approval`); (2) **soft-delete** (`DELETE` / `SET deleted_at`). **Kỹ thuật:** Giữ `@PreAuthorize("hasAuthority('can_manage_inventory')")` trên controller; trong **service** phân nhánh: nếu chuyển `status` có **target = `Completed`** hoặc soft-delete → `assertOwnerOnly(jwt)`; **`Completed`→`Re-check`** cũng `assertOwnerOnly`. Các PATCH `status` khác (Staff) không gọi `assertOwnerOnly`. **`POST apply-variance` / `cancel`:** Staff + Owner nếu cùng có `can_manage_inventory` (không bắt Owner-only theo OQ-16). | 27/04/2026 |
| OQ-17 | **Không triển khai** `parent_session_id` / session cha–con trong v1 (đơn giản hoá; ưu tiên luồng chờ Owner duyệt). Đếm lại sau **`Re-check`:** trên **cùng** phiếu + cùng `inventoryauditlines` theo guard OQ-11 (chưa apply variance). | 27/04/2026 |
| OQ-18 | Body **Task027** bắt buộc field **`cancelReason`** map vào `cancel_reason`. | 27/04/2026 |
| OQ-19 | Owner **từ chối** từ `Pending Owner Approval`: trả trạng thái **thấp hơn** = **`In Progress`** — endpoint **`POST /api/v1/inventory/audit-sessions/{id}/reject`** (Task031 GAP hoặc gộp doc Task030). | 27/04/2026 |
| OQ-20 | GET list/detail: phiếu đã soft-delete → **404** (không lộ tồn tại). | 27/04/2026 |
| OQ-3\* | *Điều chỉnh sau OQ-12/OQ-15:* “`In Progress` → `Completed`” **chỉ** xảy ra qua bước Owner **`POST …/approve`** (hoặc service tương đương), không còn là nghĩa trực tiếp của **Task026** (Task026 chỉ → `Pending Owner Approval`). | 27/04/2026 |

\* Ghi đè diễn giải OQ-3 cũ trong bảng; giữ dòng OQ-3 lịch sử phía trên hoặc coi OQ-3\* là bổ sung — Dev bám **OQ-3\*** + OQ-15.

### 4.1 Tóm tắt BA (sau khi PO điền bảng)

- **OQ-8 (A) + OQ-17:** PO chọn **không triển khai** session cha–con / `parent_session_id` trong **v1** — bỏ aggregate `childSessions` khỏi phạm vi bắt buộc; có thể mở lại v2.
- **OQ-9 + OQ-16:** `deleted_at` (soft-delete); **chỉ Owner** được gọi xóa mềm (`assertOwnerOnly` — OQ-16).
- **OQ-10:** Thêm literal `Re-check` (hoặc đúng chuỗi PO chốt) + **sửa CHECK** Flyway.
- **OQ-11 (+ OQ-17):** Tránh xung đột tồn sau apply; **không** dùng session con trong v1 — sau `Re-check`, Staff chỉnh **`PATCH lines`** trên **cùng** phiếu (snapshot cũ), trong guard “chưa apply variance”.
- **OQ-12 + OQ-15:** Trạng thái chờ duyệt = **`Pending Owner Approval`**; duyệt = **`POST …/approve`**.
- **OQ-3 vs OQ-12/OQ-15:** Đã hợp nhất bằng dòng **OQ-3\*** trong bảng PO — Task026 không đi thẳng `Completed`.

### 4.2 Đã chốt

**OQ-19** (reject → `In Progress`) và **OQ-20** (GET sau xóa → **404**) nằm trong bảng *Trả lời PO* phía trên.

---

## 5. Phân tích scope tệp & bằng chứng

### 5.1 Tài liệu đã đối chiếu

- `API_Task021` … `API_Task028` (toàn bộ).
- Flyway `V1__baseline_smart_inventory.sql` (mục Inventory audit + Inventory + InventoryLogs).

### 5.2 Mã / package dự kiến (Spring)

- Controller: thêm **`POST …/approve`**, **`DELETE …/{id}`**; giữ `can_manage_inventory` + **§6.1** `assertOwnerOnly`.
- Service + JDBC: sessions/lines/events; có thể tách **`AuditSessionAccessPolicy`** (reuse logic `StockReceiptAccessPolicy`) cho đọc JWT `role`.
- **Không** sửa `frontend/mini-erp/**` trong SRS backend (API_BRIDGE sau G-DEV).

### 5.3 Rủi ro phát hiện sớm

- **Race** khi `apply-variance` đồng thời với nhập/xuất khác trên cùng `inventory_id` — cần `SELECT … FOR UPDATE` trên `inventory` trong transaction Task028 (đã nêu trong API Task028).

---

## 6. Persona & RBAC

> **Nguồn:** Quyết định OQ-1 (mọi user dùng chức năng kiểm kê) + yêu cầu bổ sung PO 26/04/2026. Chi tiết claim JWT: **OQ-14**.

| Hành động | Staff | Owner | Điều kiện kỹ thuật | HTTP khi từ chối |
| :--- | :---: | :---: | :--- | :---: |
| JWT hợp lệ | ✓ | ✓ | Bearer | 401 |
| **GET** list + **GET** chi tiết (mọi bản ghi) | ✓ | ✓ | Theo OQ-1 / OQ-14 | 403 nếu không đủ claim đăng nhập |
| **POST** tạo đợt, **PATCH** lines, **POST** complete/cancel | ✓ | ✓ | Owner có `can_manage_inventory` thì có thể thao tác Staff (OQ-14) | 403 |
| **PATCH** session: meta / `notes` (Staff) vs **`owner_notes` + events** (Owner ưu tiên — OQ-13) | ✓ | ✓ | Field-level theo migration OQ-13 | 403 |
| **PATCH** session: **Completed → Re-check** + lý do | — | ✓ | `assertOwnerOnly` + guard OQ-11 | 403 / 409 |
| **POST …/approve** (C10) | — | ✓ | `assertOwnerOnly`; nguồn = `Pending Owner Approval` (OQ-15) | 403 / 409 |
| **DELETE** session (C9, soft) | — | ✓ | **`assertOwnerOnly`** luôn (OQ-16) | 403 / 404 / 409 |
| **POST** apply-variance | ✓ | ✓ | `can_manage_inventory`; session `Completed` (OQ-15) + Task028 | 403 / 409 |

### 6.1 OQ-16 — Triển khai Spring (đã chốt PO)

- **Controller:** `@PreAuthorize("hasAuthority('can_manage_inventory')")` trên toàn bộ endpoint audit (giữ như `AuditSessionsController` hiện tại).
- **Service:** Dùng `Jwt` + helper tương đương `com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy.assertOwnerOnly` (claim **`role`**, giá trị `Owner`, không phân biệt hoa thường) **trước** khi:
  - ghi `status = Completed` (từ `Pending Owner Approval`, qua `POST …/approve` hoặc nhánh PATCH nếu Dev gom — ưu tiên **POST approve** OQ-15);
  - thực hiện **soft-delete**;
  - thực hiện **`Completed`→`Re-check`**.
- **Không** gọi `assertOwnerOnly` cho: `Pending`↔`In Progress`, `POST complete` → `Pending Owner Approval`, `PATCH lines`, `POST cancel`, `POST apply-variance` (theo OQ-16).

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Actor

| Actor | Mô tả |
| :--- | :--- |
| User | Nhân viên / quản lý thực hiện kiểm kê |
| Client | Mini-ERP |
| API | `smart-erp` |
| DB | PostgreSQL |

### 7.2 Luồng chính (tóm tắt)

1. Staff/Owner tạo đợt cha (scope) → snapshot dòng trên **session** đó (Task022).
2. Staff `Pending` → `In Progress`, PATCH lines (đếm).
3. Staff **POST complete** → trạng thái **chờ Owner duyệt** (OQ-12, tên **OQ-15**).
4. Owner **duyệt** (C10) → `Completed`; hoặc từ chối / yêu cầu xử lý — **OQ-15** (nếu PO có nhánh này).
5. Owner có thể **Completed → Re-check** **chỉ** khi **chưa** `apply-variance` (OQ-11) + ghi chú/events (OQ-13).
6. **Apply-variance** khi `Completed` (sau approve) theo Task028.
7. **Owner** soft-delete khi cần (**OQ-16**).

### 7.3 Sơ đồ (apply variance)

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API
  participant D as DB
  C->>A: POST apply-variance (reason, mode)
  A->>D: BEGIN; lock session + lines + inventory rows
  A->>D: UPDATE inventory; INSERT inventory_logs
  A->>D: UPDATE audit lines variance_applied_at (idempotent)
  A->>D: COMMIT
  A-->>C: 200 + appliedLines
```

### 7.4 Owner — chuyển Completed → Re-check

```mermaid
sequenceDiagram
  participant O as Owner
  participant A as API
  participant D as DB
  O->>A: PATCH session (status=Re-check*, ownerNote/reason)
  A->>D: BEGIN; SELECT session FOR UPDATE
  A->>D: VALIDATE current status = Completed AND chưa apply-variance (OQ-11)
  A->>D: INSERT event / UPDATE notes (OQ-13)
  A->>D: UPDATE status
  A->>D: COMMIT
  A-->>O: 200 + detail shape Task023
```

\*Tên trạng thái lưu DB: **OQ-10**. Nếu đã apply variance → **409** (OQ-11).

---

## 8. Hợp đồng HTTP & ví dụ JSON

> Chi tiết field-level: **bám nguyên** các mục §5–§6 của từng file `API_Task021` … `API_Task028`. Dưới đây là ví dụ rút gọn + lỗi tiêu biểu; Tester lấy đủ mẫu từ API doc + [`API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md).

### 8.1 Bảng endpoint

| Task | Tên chức năng | Method | Path |
| :---: | :--- | :--- | :--- |
| 021 | Liệt kê đợt kiểm kê (lọc, phân trang) | GET | `/api/v1/inventory/audit-sessions` |
| 022 | Tạo đợt kiểm kê (snapshot theo phạm vi) | POST | `/api/v1/inventory/audit-sessions` |
| 023 | Xem chi tiết đợt (dòng, `owner_notes`, `events`) | GET | `/api/v1/inventory/audit-sessions/{id}` |
| 024 | Cập nhật phiếu: meta, trạng thái Staff (`Pending`↔`In Progress`); Owner `Completed`→`Re-check` (kèm `ownerNotes`, guard OQ-11) | PATCH | `/api/v1/inventory/audit-sessions/{id}` |
| 025 | Ghi / cập nhật số đếm từng dòng (`PATCH lines`) | PATCH | `/api/v1/inventory/audit-sessions/{id}/lines` |
| 026 | Staff gửi hoàn tất → chờ Owner duyệt (`Pending Owner Approval`) | POST | `/api/v1/inventory/audit-sessions/{id}/complete` |
| 027 | Hủy đợt (`cancelReason` bắt buộc — OQ-18) | POST | `/api/v1/inventory/audit-sessions/{id}/cancel` |
| 028 | Áp chênh lệch kiểm kê lên tồn kho (`apply-variance`) | POST | `/api/v1/inventory/audit-sessions/{id}/apply-variance` |
| **029 (GAP)** | **Xóa mềm đợt** (Owner — OQ-9, OQ-16); doc `frontend/docs/api/` | **DELETE** | `/api/v1/inventory/audit-sessions/{id}` |
| **030 (GAP)** | **Owner duyệt hoàn thành** (`Pending Owner Approval` → `Completed` — OQ-15) | **POST** | `/api/v1/inventory/audit-sessions/{id}/approve` |
| **031 (GAP)** | **Owner từ chối duyệt** (`Pending Owner Approval` → `In Progress` — OQ-19) | **POST** | `/api/v1/inventory/audit-sessions/{id}/reject` |

### 8.2 Request ví dụ — Task022 (tạo đợt)

```json
{
  "title": "Kiểm kê kho A1 - Tháng 4",
  "auditDate": "2026-04-13",
  "notes": null,
  "scope": {
    "mode": "by_location_ids",
    "locationIds": [1, 2]
  }
}
```

### 8.3 Response lỗi tiêu biểu — 409 (state / idempotency)

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể hoàn tất: còn dòng chưa đếm",
  "details": {}
}
```

---

## 9. Quy tắc nghiệp vụ (BR)

| Mã | Điều kiện | Hành động / kết quả |
| :--- | :--- | :--- |
| BR-1 | `status` ∈ tập **CHECK sau migration** (V1 + **`Pending Owner Approval`**, **`Re-check`**, OQ-10/OQ-15) | Validate mọi transition |
| BR-2 | Task021 `varianceLines` | Chỉ đếm dòng `is_counted = true` AND `actual_quantity` NOT NULL AND `(actual_quantity - system_quantity) <> 0` (theo Task021) |
| BR-3 | Task023 `variance` / `variancePercent` khi chưa đếm | `actualQuantity` null → API trả `variance = 0`, `variancePercent = 0`, `isCounted = false` (theo Task023) |
| BR-4 | Task025 | `actual_quantity >= 0`; khi ghi số: `is_counted = true` |
| BR-5 | Task026 `requireAllCounted = true` (mặc định) | Trước khi Staff POST complete: `COUNT(*) WHERE is_counted = false` > 0 → 409. **Sau OQ-12:** POST complete chỉ chuyển → **chờ duyệt** (OQ-15), không còn nghĩa “đã hoàn thành cuối cùng”. |
| BR-6 | Task028 idempotent | Nếu `variance_applied_at` IS NOT NULL trên dòng → không apply lại dòng đó; toàn request đã apply hết → 409 “Đã áp chênh lệch” |
| BR-7 | Task028 sau cập nhật | `inventory.quantity >= 0` (CHECK DB); vi phạm → rollback, 409 hoặc 400 |
| BR-8 | Đọc list/detail | Không lọc theo `created_by` trừ khi PO đổi (mâu thuẫn OQ-1) |
| BR-9 | Owner Completed→Re-check | **Chỉ** khi session **chưa** có dòng đã `apply-variance` (OQ-11); payload bắt buộc lý do; lưu **events** + `owner_notes` (OQ-13) |
| BR-10 | Staff PATCH lines | Khi `In Progress` hoặc **`Re-check`** (chưa apply variance); **không** PATCH khi `Completed`+đã apply |
| BR-11 | Owner / Staff ghi chú | **OQ-13:** `owner_notes` + `inventory_audit_session_events`; Staff `title`/`notes` theo field cho phép |
| BR-12 | DELETE (soft, OQ-9 + **OQ-16**) | Chỉ sau **`assertOwnerOnly`**; `UPDATE … SET deleted_at = now() WHERE id=? AND deleted_at IS NULL` |
| BR-13 | List/detail | Mọi query list mặc định `deleted_at IS NULL` |

---

## 10. Dữ liệu & SQL tham chiếu (Agent SQL)

### 10.1 Tên bảng vật lý PostgreSQL (Flyway V1)

PostgreSQL chuẩn hoá identifier không có dấu ngoặc kép về **chữ thường**. DDL Flyway dùng `CREATE TABLE InventoryAuditSessions` → tên bảng thực tế **`inventoryauditsessions`**; tương tự **`inventoryauditlines`**, **`inventory`**, **`inventorylogs`**, **`users`**, **`products`**, **`warehouselocations`**, **`productunits`**, **`systemlogs`**.

> **GAP tài liệu API:** các file API ghi `inventory_audit_sessions` (snake có gạch dưới) — **không** khớp tên vật lý trên. Dev dùng đúng tên PG hoặc quote identifier có chủ ý; SRS chốt theo **Flyway**.

### 10.2 Cột liên quan (rút gọn)

| Bảng | Cột / ghi chú |
| :--- | :--- |
| `inventoryauditsessions` | V1 + migration: `status` thêm **`Pending Owner Approval`**, **`Re-check`** (OQ-10, OQ-15); **`deleted_at`** TIMESTAMPTZ NULL (OQ-9); **`owner_notes`** TEXT (OQ-13); *`parent_session_id` **v2** (OQ-17 huỷ v1)*; `notes`, `created_by`, `completed_at`, `completed_by`, `cancel_reason` (V11), timestamps |
| `inventory_audit_session_events` | **Migration mới** (OQ-13): `id`, `session_id` FK, `event_type`, `body`/`payload` JSONB, `created_by`, `created_at` |
| `inventoryauditlines` | `id` SERIAL PK, `session_id` FK → sessions, `inventory_id` FK → `inventory`, `system_quantity` DECIMAL(12,4), `actual_quantity` DECIMAL(12,4) NULL, `is_counted` BOOLEAN, `notes` VARCHAR(500), **`variance_applied_at`** TIMESTAMP NULL (idempotency Task028) |
| `inventory` | `id`, `product_id`, `location_id`, `batch_number`, `expiry_date`, **`quantity` INT** ≥ 0 |

### 10.3 SQL mẫu — danh sách Task021 (ý tưởng)

```sql
-- Đếm tổng (filter giống query list)
SELECT COUNT(*) FROM inventoryauditsessions s
WHERE s.deleted_at IS NULL
  AND (:status = 'all' OR s.status = :status)
  AND ( :search IS NULL OR s.audit_code ILIKE :search OR s.title ILIKE :search
        OR EXISTS (SELECT 1 FROM users u WHERE u.id = s.created_by AND u.full_name ILIKE :search) );

-- Một dòng list: join users (created_by, completed_by) + aggregate từ lines
SELECT s.id, s.audit_code, ...,
       (SELECT COUNT(*) FROM inventoryauditlines l WHERE l.session_id = s.id) AS total_lines,
       (SELECT COUNT(*) FROM inventoryauditlines l WHERE l.session_id = s.id AND l.is_counted) AS counted_lines,
       (SELECT COUNT(*) FROM inventoryauditlines l WHERE l.session_id = s.id AND l.is_counted
          AND l.actual_quantity IS NOT NULL
          AND (l.actual_quantity - l.system_quantity) <> 0) AS variance_lines
FROM inventoryauditsessions s
JOIN users uc ON uc.id = s.created_by
LEFT JOIN users uf ON uf.id = s.completed_by
WHERE ...
ORDER BY s.audit_date DESC, s.id DESC
LIMIT :limit OFFSET :offset;
```

### 10.4 Transaction & khóa

| Luồng | Khuyến nghị |
| :--- | :--- |
| Task022 tạo đợt | Một transaction: sinh mã + INSERT session + INSERT N lines |
| Task024 / 025 / 026 / 027 / Owner Re-check | `SELECT … FROM inventoryauditsessions WHERE id = ? FOR UPDATE` trước UPDATE |
| Task028 | FOR UPDATE trên session ở trạng thái **đã duyệt** `Completed` (OQ-12 + OQ-15), từng `inventory` row, cập nhật `variance_applied_at` trong cùng transaction |
| DELETE C9 (OQ-9 + OQ-16) | FOR UPDATE → **`assertOwnerOnly`** → `UPDATE … SET deleted_at = now()` |

### 10.5 Index (đã có / đủ cho v1)

- `idx_audit_sessions_status` trên `inventoryauditsessions(status)` — lọc list.
- `idx_audit_lines_session` trên `inventoryauditlines(session_id)` — join + aggregate.

Đề xuất bổ sung (tùy volume): index `(audit_date DESC, id DESC)` nếu EXPLAIN list chậm.

### 10.6 Kiểm chứng cho Tester

- Sau Task022: số dòng `inventoryauditlines` = số dòng `inventory` khớp scope.
- Sau Task028: với dòng đã có `variance_applied_at`, gọi lại apply → 409; `inventory.quantity` khớp mode (sau làm tròn nếu OQ-5 = A).
- Sau Owner **Completed→Re-check**: GET chi tiết có mục timeline / sự kiện theo OQ-13; `status` khớp OQ-10.
- Sau DELETE (C9, OQ-9): `deleted_at` NOT NULL; GET list ẩn; GET by id → 404 hoặc 410 tùy policy API (**OQ-15**).

### 10.7 DDL / bảng mới — PO đã chốt hướng (Dev viết Flyway `V{n}__*.sql`)

Theo [`SQL_AGENT_INSTRUCTIONS.md`](../../AGENTS/SQL_AGENT_INSTRUCTIONS.md): bám OQ-15, OQ-10, OQ-13, OQ-9; **`parent_session_id` không bắt buộc v1** (OQ-17).

| Ưu tiên | Nội dung | Ghi chú SQL |
| :--- | :--- | :--- |
| **OQ-9** | `deleted_at TIMESTAMPTZ NULL` | List `WHERE deleted_at IS NULL` |
| **OQ-10 + OQ-15** | Mở rộng CHECK `status` | Thêm **`Pending Owner Approval`**, **`Re-check`** (+ giữ literal V1 có khoảng trắng); `ALTER TABLE … DROP/ADD CHECK` |
| **OQ-13** | `owner_notes` + `inventory_audit_session_events` | Timeline |
| **v2 (tùy)** | `parent_session_id` | Chỉ khi PO mở lại OQ-8 (A) sau OQ-17 |

**Transaction DELETE (soft):** `BEGIN` → `FOR UPDATE` → **assert Owner (app)** → `UPDATE deleted_at` → `COMMIT`.

---

## 11. Acceptance criteria (Given / When / Then) — rút gọn

```text
Given đợt ở trạng thái Pending và có ít nhất một dòng snapshot
When PATCH …/lines với actualQuantity hợp lệ
Then is_counted = true và GET by id trả đúng actualQuantity
```

```text
Given đợt In Progress và mọi dòng is_counted = true
When POST …/complete với requireAllCounted true
Then status = trạng thái chờ Owner duyệt (OQ-15) — không phải Completed cuối cùng trừ khi PO bác OQ-12
```

```text
Given đợt Pending Owner Approval
When Owner POST /api/v1/inventory/audit-sessions/{id}/approve
Then status = Completed; assertOwnerOnly đã chạy (OQ-16)
```

```text
Given đợt Completed và dòng có variance <> 0 chưa apply
When POST …/apply-variance (reason, mode)
Then inventory.quantity cập nhật đúng policy OQ-5; inventory_logs có bản ghi; variance_applied_at NOT NULL
```

```text
Given đã apply variance cho session
When POST …/apply-variance lần nữa
Then 409 (idempotent)
```

```text
Given đợt Completed và session chưa có dòng variance_applied (OQ-11)
When Owner PATCH …/sessions/{id} chuyển sang Re-check (OQ-10) kèm ghi chú bắt buộc
Then status và timeline (OQ-13) được lưu; GET by id trả đủ để hiển thị yêu cầu Owner
```

```text
Given đợt Completed và đã apply variance
When Owner PATCH …/sessions/{id} chuyển sang Re-check
Then 409 (OQ-11)
```

```text
Given đợt ở trạng thái cho phép đếm theo OQ-11
When Staff PATCH lines
Then actual_quantity / notes cập nhật và không vi phạm guard apply-variance đã chốt
```

```text
Given đợt tồn tại và deleted_at IS NULL
When Owner DELETE …/sessions/{id}
Then assertOwnerOnly; deleted_at được set; GET list ẩn bản ghi
```

---

## 12. GAP & giả định — **Quyết định BA đã hợp nhất** (không cần PO nếu không sai mục đích)

| # | Chủ đề | Quyết định |
| :---: | :--- | :--- |
| G1 | Tên bảng API vs Flyway | SRS & Dev bám **Flyway** (mục §10.1); API markdown giữ nguyên nhưng coi là **tên logic** — cập nhật doc sau (Doc Sync) hoặc ghi chú trong BRIDGE. |
| G2 | Kiểu `id` session/line | **SERIAL (INT)** theo V1; không dùng BIGSERIAL như phụ lục DDL mẫu trong Task022. |
| G3 | Hủy đợt | **`Cancelled` chỉ qua Task027**; PATCH Task024 **không** chuyển sang `Cancelled` (tránh trùng Task024 §2 vs Task027). |
| G4 | PATCH / complete / duyệt | Staff PATCH `Pending`→`In Progress`; Task026 → **`Pending Owner Approval`**; **`POST …/approve`** → `Completed` (OQ-15); Owner PATCH `Completed`→`Re-check` (OQ-11); **migration CHECK** + **Task030** + **OQ-16** service. |
| G9 | Task023 response | Bổ sung `events[]`, `ownerNotes` (OQ-13); *`childSessions` v2 nếu bật lại OQ-8.* — **GAP** API. |
| G10 | Task029 DELETE / Task030 approve | Chưa có `frontend/docs/api/` — path đã chốt OQ-15 (`POST …/approve`). |
| G5 | Đơn vị hiển thị Task023 | **Đơn vị cơ sở** (`productunits.is_base_unit = true`) cho `unitName` — nhất quán với các API tồn đã chốt base unit ở module nhập. |
| G6 | `location_filter` / `category_filter` | Text snapshot trên header theo scope (Task022 §7) — map từ `warehouse_code` gộp / `category_id` string hoá tùy Dev miễn hiển thị list Task021. |
| G7 | Task028 `InventoryLogs` | Dùng `action_type = 'ADJUSTMENT'`; `reference_note` ≤ 255 ký tự — nối mã đợt + lineId (truncate nếu cần). |
| G8 | Task028 mode mặc định | Mặc định **`delta`** (theo Zod Task028); `set_actual` vẫn hỗ trợ như spec với cảnh báo trong API doc. |

---

## 13. PO sign-off (chỉ điền khi Approved)

- [ ] Đã đồng bộ **OQ-15–18, OQ-3\*** vào API markdown + migration + `assertOwnerOnly` (§6.1)
- [ ] (Tùy) **OQ-19–20** nếu cần hành vi từ chối / GET sau xóa
- [ ] JSON / state machine khớp vận hành thực tế cửa hàng
- [ ] Đồng ý phạm vi In/Out §3

**Chữ ký / nhãn PR:** …
