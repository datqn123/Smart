# 📄 API SPEC: Thông báo Owner khi Staff thay đổi dữ liệu tồn kho - Task012

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — **cảnh báo Owner** khi Staff ghi DB  
> **Tags**: Notifications, Inventory, RBAC, Cross-cutting

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Khi **Staff** (hoặc vai không phải Owner) thực hiện các thao tác trên màn / API tồn kho làm **thay đổi dữ liệu** (`PATCH` meta, `PATCH` bulk, `POST` điều chỉnh số lượng, sau này `DELETE`…), **Owner** của doanh nghiệp cần được **thông báo** (in-app tối thiểu) để giám sát — tránh thay đổi “im lặng”.
- **Ai được lợi**: Owner; Staff vẫn làm việc bình thường trong phạm vi quyền.
- **Phạm vi Task này**: quy tắc **ghi `Notifications`** (bảng optional trong DB) hoặc tương đương; **không** bắt buộc một REST path riêng nếu triển khai nội bộ trong service xử lý Task007/008/010.
- **Out of scope**: template email marketing; push mobile app riêng — có thể bổ sung sau.

---

## 2. Mục đích “Endpoint” / cơ chế

**Mục đích**: Sau khi mutation tồn kho **thành công** (và đã / sẽ ghi log theo [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md)), nếu **actor không phải Owner** (ví dụ `Staff`), hệ thống **tạo thông báo** cho **mọi User có vai Owner** thuộc cùng phạm vi tenant (policy đơn cửa hàng: thường 1 Owner).

**Khi kích hoạt**: cùng các sự kiện Task011 gắn với Task007, 008, 010 (và DELETE tương lai).

**Kết quả**: bản ghi `Notifications` (hoặc queue) để Owner đọc trên màn thông báo / bell icon.

**Cơ chế này KHÔNG:**

- Không thay thế việc ghi **SystemLogs / InventoryLogs** (Task011).  
- Không bắt buộc gửi email — tuỳ cấu hình sau.  
- **Không** gửi thông báo cho chính Staff nếu không có yêu cầu (mặc định chỉ Owner).

**Ghi chú enum DB**: [`Notifications.notification_type`](../UC/Database_Specification.md) hiện CHECK: `ApprovalResult`, `LowStock`, `ExpiryWarning`, `SystemAlert`. **Khuyến nghị v1**: dùng **`SystemAlert`** cho loại “Staff đã chỉnh tồn kho”, `title` / `message` tiếng Việt mô tả hành động + SKU/ảnh hưởng; `reference_type` = `Inventory`, `reference_id` = `inventory.id` (hoặc `0` + chi tiết trong `message` nếu bulk). Nếu cần loại riêng, **migration** mở rộng CHECK (ghi rõ trong backlog DB).

---

## 3. Tham chiếu

- [`Database_Specification.md`](../UC/Database_Specification.md) §23 **Notifications** (optional).  
- Audit: [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md).  
- [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §4.14 `GET /notifications`.

---

## 4. Payload gợi ý (`INSERT Notifications`)

| Cột | Giá trị gợi ý |
| :-- | :------------ |
| `user_id` | `Users.id` của **Owner** nhận |
| `notification_type` | `SystemAlert` (v1) |
| `title` | Ví dụ: `Nhân viên cập nhật tồn kho` |
| `message` | Ví dụ: `staff01 vừa điều chỉnh số lượng SKU SKU-WAT-500 (+24).` |
| `reference_type` | `Inventory` |
| `reference_id` | `Inventory.id` (hoặc quy ước bulk — xem Task008) |
| `is_read` | `false` |

Lặp `INSERT` cho **từng** Owner nếu nhiều hơn một (hiếu khi đơn cửa hàng).

### 4.1 Ví dụ JSON một bản ghi cần `INSERT` (đủ field theo DB §23)

Giá trị minh họa (snake_case theo bảng; `id` / `created_at` do DB sinh):

```json
{
  "user_id": 2,
  "notification_type": "SystemAlert",
  "title": "Nhân viên cập nhật tồn kho",
  "message": "staff01 vừa điều chỉnh số lượng SKU SKU-WAT-500 (+24) tại WH01/A1.",
  "is_read": false,
  "reference_type": "Inventory",
  "reference_id": 101,
  "read_at": null
}
```

---

## 5. Đặc tả HTTP (Request/Response) — phạm vi Task012

| Hạng mục | Nội dung |
| :------- | :------- |
| **Request từ FE cho Task012** | _Không có_. Cơ chế chạy **nội bộ** trong pipeline sau Task007 / Task008 / Task010. |
| **Response JSON của “Task012”** | _Không có_. Owner đọc thông báo qua API đã catalog (ví dụ `GET /api/v1/notifications` — khi có spec chi tiết envelope/`data`, bám theo đó). |

---

## 6. Điều kiện kích hoạt (RBAC)

| Actor | Gửi thông báo Owner? |
| :---- | :------------------- |
| **Staff** | **Có** (mặc định), sau mỗi mutation thành công nêu trên |
| **Owner** tự thực hiện | **Không** (mặc định) — tránh spam; PM có thể đổi thành “có” cho multi-owner |
| **Admin** | Theo policy dự án (mặc định: coi như Staff nếu không phải Owner data) |

---

## 7. Optional REST (khi có màn bell)

`GET /api/v1/notifications` đã nằm catalog §4.14 — FE Owner poll hoặc SSE sau này; **không** bắt buộc trong Task012.

---

## 8. Zod

_Không áp dụng trực tiếp (server-side insert)._

---

## 9. Logic nghiệp vụ & Database (Business Logic)

Hook chạy **sau** khi mutation tồn kho (Task007/008/010) **đã** được phép ghi DB và (theo Task011) đã/đang trong transaction hợp lệ. **Không** có request HTTP riêng — bước dưới là **nội bộ service**.

### 9.1 Quy trình thực thi (Step-by-Step)

1. **Đọc actor** từ JWT / context: `actor_user_id`, `role_name` (hoặc `role_id`).

2. **Nếu actor là Owner** (theo policy mặc định task này) → **bỏ qua** (không `INSERT Notifications`) — kết thúc.

3. **Truy vấn danh sách Owner nhận thông báo** (ví dụ một Owner mỗi cửa hàng):

```sql
SELECT u.id
FROM Users u
JOIN Roles r ON r.id = u.role_id
WHERE r.name = 'Owner'
  AND u.status = 'Active'
  /* AND điều kiện phạm vi cửa hàng / tenant theo policy dự án */;
```

4. **Với mỗi `owner_user_id`** — `INSERT`:

```sql
INSERT INTO Notifications (
  user_id,
  notification_type,
  title,
  message,
  is_read,
  reference_type,
  reference_id
) VALUES (
  :owner_user_id,
  'SystemAlert',
  :title_vi,
  :message_vi,
  FALSE,
  'Inventory',
  :inventory_id_int
);
```

- `notification_type` phải thuộc CHECK (`SystemAlert` khuyến nghị v1 — xem §2).  
- `reference_id` kiểu INT trong DB §23 — nếu `Inventory.id` kiểu BIGINT vượt phạm vi hoặc bulk không map một `id`, dùng quy ước Task012 §2 (ví dụ `0` + chi tiết trong `message`).

5. **Nếu bảng `Notifications` không tồn tại** trong môi trường triển khai — **no-op** hoặc ghi `SystemLogs` WARNING (chốt PM).

### 9.2 Các ràng buộc (Constraints)

- **CHECK** `notification_type` trên bảng §23.  
- **FK** `user_id` → `Users.id`.  
- **Không** spam: một mutation bulk có thể gộp **một** thông báo tóm tắt thay vì N dòng (chốt UX).  
- **Trigger**: không giả định trừ khi `schema.sql` có.

---

## 10. QA

- [ ] Staff mutation → có ít nhất một `Notifications` cho Owner (khi bảng tồn tại).  
- [ ] Owner tự sửa → không spam (trừ khi cấu hình bật).
