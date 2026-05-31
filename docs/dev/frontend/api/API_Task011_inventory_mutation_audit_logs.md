# 📄 API SPEC: Ghi nhật ký DB khi thay đổi tồn kho (SystemLogs + InventoryLogs) - Task011

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — **hậu kiểm & audit** (không phải endpoint REST độc lập)  
> **Tags**: Inventory, SystemLogs, InventoryLogs, Cross-cutting

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Bổ sung **hợp đồng triển khai backend** để mọi thao tác **ghi** dữ liệu tồn kho từ giao diện / API (sửa meta, sửa hàng loạt, điều chỉnh số lượng, sau này xóa dòng tồn…) đều **lưu vết trên DB** đúng bảng quy định, phục vụ truy vết và đối soát — tránh chỉ cập nhật `Inventory` mà không log.
- **Ai được lợi**: Owner, kiểm toán nội bộ, hỗ trợ sự cố; hệ thống đạt yêu cầu minh bạch thay đổi.
- **Phạm vi Task này**: **chính sách + ma trận** ghi `SystemLogs` và/hoặc `InventoryLogs` gắn với các Task endpoint **007, 008, 010** (và endpoint xóa tồn khi được bổ sung).
- **Out of scope**: định nghĩa request/response của `GET /inventory/logs` (màn tra cứu sau); chi tiết từng field HTTP của Task007/008/010 — vẫn nằm trong file Task tương ứng.

---

## 2. Mục đích “Endpoint” / phạm vi kỹ thuật

Task này **không** định nghĩa URL HTTP mới. Mục đích là: **sau khi** các handler của `PATCH /inventory/{id}`, `PATCH /inventory/bulk`, `POST /inventory/adjustments` (và DELETE tương lai) **commit** thay đổi `Inventory` thành công, backend **phải** thực hiện thêm bước ghi log theo bảng dưới (cùng transaction hoặc ngay sau transaction chính — **ưu tiên cùng transaction** nếu DB cho phép).

**Task này KHÔNG:**

- Không thay thế spec chi tiết body/response của Task007, 008, 010.  
- Không bắt buộc FE gọi thêm API — log là **nội bộ server**.

---

## 3. Tham chiếu

- [`Database_Specification.md`](../UC/Database_Specification.md): **§11 SystemLogs**, **§22 InventoryLogs**, cột `Inventory` (§16).  
- Task triển khai gọi: [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md), [`API_Task008_inventory_bulk_patch.md`](API_Task008_inventory_bulk_patch.md), [`API_Task010_inventory_post_adjustments.md`](API_Task010_inventory_post_adjustments.md).  
- Thông báo Owner (song song): [`API_Task012_inventory_staff_change_notify_owner.md`](API_Task012_inventory_staff_change_notify_owner.md).

---

## 4. Ma trận: thao tác → bảng log

| Nguồn (API / hành vi) | `SystemLogs` | `InventoryLogs` | Ghi chú |
| :--------------------- | :----------- | :--------------- | :------ |
| `PATCH` meta tồn (Task007, 008) — **không** đổi `quantity` | **Bắt buộc** `INSERT`: `log_level=INFO`, `module=INVENTORY`, `action` ví dụ `INVENTORY_META_UPDATE` hoặc `INVENTORY_BULK_META_UPDATE`, `user_id` = actor, `context_data` JSON **before/after** (ít nhất: `inventoryId`, `productId`, các field đổi) | **Không bắt buộc** nếu `quantity` không đổi — `InventoryLogs` theo DB spec là biến động số lượng / luân chuyển | Nếu sau này mở rộng schema `InventoryLogs` cho meta-only, cập nhật lại ma trận |
| `POST` điều chỉnh số lượng (Task010) | **Khuyến nghị** `INSERT` cùng mức INFO + `context_data` tóm tắt (link tới dòng log kho) | **Bắt buộc** `INSERT` theo từng dòng: `action_type=ADJUSTMENT`, `quantity_change=deltaQty`, `product_id`, `unit_id`, `user_id`, `reference_note` hoặc FK phiếu nếu có | Khớp CHECK `action_type` trong DB |
| `DELETE` / soft-delete dòng tồn (khi có spec) | **Bắt buộc** WARNING hoặc INFO + `context_data` đủ để tái hiện | Theo nghiệp vụ: có thể `OUTBOUND` / `ADJUSTMENT` tùy cách hạ tồn — thống nhất khi viết Task DELETE | |

**Ràng buộc**: `InventoryLogs` trong DB hiện có **không** có cột `inventory_id` — mapper `product_id` + `from_location_id`/`to_location_id` + `reference_note` (JSON chứa `inventoryId`) hoặc **migration** thêm `inventory_id` (khuyến nghị PM/DB chốt một hướng).

---

## 5. Ví dụ payload nội bộ (đặc tả đầy đủ — không có HTTP request/response riêng)

Task này **không** định nghĩa URL mới; dưới đây là **dữ liệu tối thiểu** service nội bộ phải có/gi khi `INSERT` log (để dev không suy diễn). Envelope JSON trả về cho client vẫn theo Task007 / Task008 / Task010.

### 5.1 `SystemLogs` — `context_data` (JSON gợi ý, cột meta-change)

Sau `PATCH` một dòng meta (Task007), ví dụ giá trị lưu vào cột JSON `context_data` (tên cột theo [`Database_Specification.md`](../UC/Database_Specification.md) §11):

```json
{
  "action": "INVENTORY_META_UPDATE",
  "inventoryId": 101,
  "productId": 12,
  "skuCode": "SKU-WAT-500",
  "before": {
    "locationId": 2,
    "minQuantity": 50,
    "batchNumber": "LOT-2026-00",
    "expiryDate": "2026-06-01"
  },
  "after": {
    "locationId": 3,
    "minQuantity": 60,
    "batchNumber": "LOT-2026-01",
    "expiryDate": "2026-12-31"
  },
  "actorUserId": 5,
  "correlationId": "req-9f2c1a8b-4d3e-4c1a-9c2e-111111111111"
}
```

Các cột scalar đi kèm (ví dụ): `log_level` = `INFO`, `module` = `INVENTORY`, `action` = `INVENTORY_META_UPDATE`, `user_id` = actor, `message` = mô tả ngắn tiếng Việt.

### 5.2 `InventoryLogs` — một dòng sau `POST` điều chỉnh (Task010)

Ví dụ **bản ghi logic** (map sang cột DB thực tế; có thể nhúng `inventoryId` trong `reference_note` nếu chưa migration cột `inventory_id`):

```json
{
  "action_type": "ADJUSTMENT",
  "product_id": 12,
  "unit_id": 5,
  "quantity_change": 24,
  "user_id": 5,
  "reference_note": "{\"inventoryId\":101,\"reason\":\"Điều chỉnh sau kiểm kê nhanh\",\"referenceType\":\"MANUAL_ADJUSTMENT\"}",
  "from_location_id": 3,
  "to_location_id": null
}
```

### 5.3 `SystemLogs` — tóm tắt sau điều chỉnh số lượng (Task010)

```json
{
  "action": "INVENTORY_QUANTITY_ADJUSTMENT",
  "lines": [
    { "inventoryId": 101, "deltaQty": 24, "quantityAfter": 264 }
  ],
  "actorUserId": 5,
  "correlationId": "req-7a1b2c3d-5e6f-7890-abcd-222222222222"
}
```

---

## 6. Logic nghiệp vụ & Database (Business Logic)

Áp dụng **sau** khi handler Task007 / Task008 / Task010 đã **validate** xong và chuẩn bị ghi `Inventory` (hoặc ngay trong cùng transaction).

### 6.1 Quy trình thực thi (Step-by-Step)

1. **`BEGIN`** (hoặc tham gia transaction đã mở bởi handler Task007 / Task008 / Task010).

2. **Mutation chính trên `Inventory`** — thực hiện **trong cùng transaction** theo đúng thứ tự đã đặc tả trong task cha (ví dụ Task010: `SELECT … FOR UPDATE` → `UPDATE Inventory` → `INSERT InventoryLogs` từng dòng; Task007/008: `SELECT … FOR UPDATE` → `UPDATE Inventory`).

3. **`INSERT InventoryLogs`** — **chỉ** khi ma trận §4 yêu cầu (bắt buộc với điều chỉnh `quantity` / Task010). Câu lệnh mẫu:

```sql
INSERT INTO InventoryLogs (
  product_id, action_type, quantity_change, unit_id, user_id,
  from_location_id, to_location_id, dispatch_id, receipt_id, reference_note
) VALUES (/* xem API_Task010 §7.1 */);
```

4. **`INSERT SystemLogs`** — meta / tóm tắt:

```sql
INSERT INTO SystemLogs (log_level, module, action, user_id, message, context_data)
VALUES (
  'INFO',
  'INVENTORY',
  'INVENTORY_META_UPDATE', /* hoặc INVENTORY_BULK_META_UPDATE / INVENTORY_QUANTITY_ADJUSTMENT */
  :actor_user_id,
  :message_vi,
  :context_jsonb /* before/after — xem §5 */
);
```

5. **Task012 (Staff)** — `INSERT INTO Notifications (...)` với `notification_type` hợp CHECK.

6. **`COMMIT`**.  
   - Nếu bất kỳ bước **2–5** lỗi: **`ROLLBACK` toàn bộ** — không để `Inventory` đổi mà thiếu log/notify theo policy.

### 6.2 Các ràng buộc (Constraints)

- **`SystemLogs`**: `log_level` ∈ CHECK; `message` NOT NULL; `context_data` JSONB — không chứa secret, không vượt quá kích thước hợp lý (archiving theo §11).  
- **`InventoryLogs`**: `action_type` CHECK; `reference_note` VARCHAR(255) — nội dung JSON phải ngắn hoặc dùng bảng phụ.  
- **Không** log `password_hash` hay PII không cần thiết.  
- **Trigger**: không giả định trigger DB tự ghi thay cho bước trên trừ khi `schema.sql` quy định rõ.

---

## 7. Zod

_Không áp dụng trực tiếp (logic server)._

---

## 8. QA

- [ ] Task007/008/010 (và DELETE sau này) có đoạn “Implementation note: tuân Task011” trong file spec.  
- [ ] `context_data` không chứa secret; kích thước hợp lý.
