# 📄 API SPEC: `POST /api/v1/inventory/adjustments` — Điều chỉnh số lượng tồn (có log) - Task010

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — toolbar **Nhập** / **Xuất** điều chỉnh nhanh  
> **Tags**: RESTful, Inventory, InventoryLogs

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Mọi thay đổi **số lượng tồn thực tế** (`Inventory.quantity`) từ UI “điều chỉnh nhanh” phải đi qua luồng **có ghi nhận** (`InventoryLogs`) để audit và truy vết — thay cho cập nhật im lặng trên mock FE.
- **Ai được lợi**: chủ hàng / kiểm soát nội bộ; sau này đối chiếu qua **màn tra cứu log** (API `GET /inventory/logs` — chưa có spec Task, ngoài màn Tồn kho).
- **Phạm vi Task này**: **chỉ** `POST /inventory/adjustments` (một hoặc nhiều dòng trong body).
- **Out of scope**: sửa meta (vị trí, HSD, …) không đổi số lượng → Task007/008; phiếu nhập/xuất chuẩn UC7/UC10 → spec khác.

---

## 2. Mục đích Endpoint

**`POST /api/v1/inventory/adjustments`** áp dụng **biên độ** `deltaQty` lên từng `inventoryId` trong cùng request, trong transaction, và **ghi log** từng biến động.

**Khi nào gọi**: user chọn nhiều dòng và xác nhận **Nhập** hoặc **Xuất** số lượng trên toolbar (điều chỉnh nhanh); hoặc luồng điều chỉnh sau kiểm kê có `reason`.

**Sau khi thành công**: `quantity` mới trên DB; có bản ghi `InventoryLogs` để tra cứu khi có màn/API đọc log.

**Endpoint này KHÔNG:**

- **Không** thay thế **PATCH meta** (Task007) — không dùng để chỉ đổi `min_quantity` / `location_id` mà không đụng số lượng.
- Không thay phiếu nhập có nhà cung cấp / duyệt (UC7) — đây là kênh **điều chỉnh / hiệu chỉnh** có lý do.
- Không đọc danh sách (Task005) hay chỉ đọc chi tiết (Task006).

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7**.  
**DB**: `Inventory.quantity`, `InventoryLogs` — [`Database_Specification.md`](../UC/Database_Specification.md) §22.

**Task liên quan**: [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md).

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7** |
| **Endpoint** | `/api/v1/inventory/adjustments` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner / Staff có quyền điều chỉnh tồn |
| **Use Case Ref** | UC6 (và liên quan audit) |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

### 5.2 Path & query parameters

_Không có_

### 5.3 Request body

`deltaQty` > 0: nhập thêm; < 0: xuất/trừ (phải còn đủ tồn sau điều chỉnh).

```json
{
  "lines": [
    {
      "inventoryId": 101,
      "deltaQty": 24,
      "reason": "Điều chỉnh sau kiểm kê nhanh",
      "referenceType": "MANUAL_ADJUSTMENT",
      "referenceId": null
    }
  ]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `lines` | array | Có | Ít nhất 1 dòng điều chỉnh |
| `lines[].inventoryId` | number | Có | `Inventory.id` |
| `lines[].deltaQty` | number | Có | Khác 0; tổng `quantity + deltaQty` phải `>= 0` |
| `lines[].reason` | string | Có | Ghi chú lý do (audit), ví dụ max 500 ký tự |
| `lines[].referenceType` | string | Không | Ví dụ `MANUAL_ADJUSTMENT` |
| `lines[].referenceId` | number \| null | Không | FK tham chiếu nghiệp vụ nếu có |

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "updated": [{ "inventoryId": 101, "quantity": 264 }]
  },
  "message": "Đã cập nhật tồn kho"
}
```

---

## 7. Logic nghiệp vụ & Database (Business Logic)

Tham chiếu: [`Database_Specification.md`](../UC/Database_Specification.md) §16 `Inventory`, §22 `InventoryLogs`, §11 `SystemLogs`. Hậu xử lý: [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md), [`API_Task012_inventory_staff_change_notify_owner.md`](API_Task012_inventory_staff_change_notify_owner.md).

### 7.1 Quy trình thực thi (Step-by-Step)

1. **Xác thực JWT** → lấy `user_id`. **401** / **403** nếu không đủ quyền điều chỉnh tồn.

2. **Validation body** — `lines` rỗng, thiếu `reason`, `deltaQty` = 0, chuỗi quá dài → **400** (`details`).  
   - `reference_note` trong DB (InventoryLogs) tối đa **255** ký tự — nếu embed JSON, giữ ngắn.

3. **`BEGIN` transaction.**

4. **Với mỗi dòng `lines[k]`** (theo thứ tự):

```sql
SELECT
  i.id,
  i.product_id,
  i.location_id,
  i.quantity,
  pu.id AS base_unit_id
FROM Inventory i
JOIN Products p ON p.id = i.product_id
JOIN ProductUnits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
WHERE i.id = :inventory_id
FOR UPDATE OF i;
```

- Không có dòng → **ROLLBACK** → **404**.  
- `p.status = 'Inactive'` (nếu policy chặn điều chỉnh) → **ROLLBACK** → **409**.  
- Kiểm tra `i.quantity + :delta_qty >= 0` (DECIMAL). Sai → **ROLLBACK** → **400** (`details.lines[k].deltaQty`).

```sql
UPDATE Inventory
SET quantity = quantity + :delta_qty,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :inventory_id;
```

- Ghi nhận `quantity_after` trong biến ứng dụng để trả `data.updated` và để log.

```sql
INSERT INTO InventoryLogs (
  product_id,
  action_type,
  quantity_change,
  unit_id,
  user_id,
  from_location_id,
  to_location_id,
  dispatch_id,
  receipt_id,
  reference_note
) VALUES (
  :product_id,
  'ADJUSTMENT',
  :delta_qty,
  :base_unit_id,
  :user_id,
  :location_id,
  NULL,
  NULL,
  NULL,
  :reference_note_short
);
```

- `:reference_note_short`: ví dụ chuỗi ≤255 chứa `inventoryId`, `reason`, `referenceType` (truncate có kiểm soát hoặc bảng mở rộng sau).

5. **`COMMIT`.**

6. **Sau khi transaction thành công** (cùng TX hoặc TX tiếp theo — Task011):

```sql
INSERT INTO SystemLogs (log_level, module, action, user_id, message, context_data)
VALUES (
  'INFO',
  'INVENTORY',
  'INVENTORY_QUANTITY_ADJUSTMENT',
  :user_id,
  'Điều chỉnh số lượng tồn kho (nhiều dòng)',
  :context_jsonb
);
```

7. **Task012** — nếu actor là Staff: `INSERT INTO Notifications (...)` cho từng Owner; `notification_type` phải nằm trong CHECK (`SystemAlert` khuyến nghị v1).

### 7.2 Các ràng buộc (Constraints)

- **`Inventory.chk_quantity`**: sau `UPDATE` phải `quantity >= 0`.  
- **`InventoryLogs.action_type`**: chỉ `'INBOUND'|'OUTBOUND'|'TRANSFER'|'ADJUSTMENT'` — luồng này dùng **`ADJUSTMENT`**.  
- **`InventoryLogs.unit_id`**: NOT NULL — luôn dùng **đơn vị cơ sở** của sản phẩm (join `ProductUnits.is_base_unit = TRUE`).  
- **FK** trên `InventoryLogs`: `product_id`, `unit_id`, `user_id`, `from_location_id`.  
- **Xung đột đồng thời**: nếu triển khai optimistic lock / versioning — mô tả thêm cột và trả **409**; nếu không, `FOR UPDATE` trong bước 4 đã giảm race.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request (Thiếu `lines`, `reason`, hoặc `deltaQty` làm âm tồn)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "lines": "Cần ít nhất một dòng điều chỉnh",
    "lines[0].reason": "Lý do là bắt buộc",
    "lines[0].deltaQty": "Sau điều chỉnh, số lượng tồn không được âm"
  }
}
```

#### 401 Unauthorized

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
}
```

#### 403 Forbidden

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền thực hiện điều chỉnh tồn kho"
}
```

#### 404 Not Found (Một hoặc nhiều `inventoryId` không tồn tại)

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy một hoặc nhiều dòng tồn kho trong yêu cầu"
}
```

#### 409 Conflict (Xung đột đồng thời / khóa optimistic — nếu có triển khai)

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Dữ liệu tồn kho đã thay đổi, vui lòng tải lại và thử lại"
}
```

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

---

## 9. Zod

```typescript
import { z } from "zod";

export const InventoryAdjustmentLineSchema = z.object({
  inventoryId: z.number().int().positive(),
  deltaQty: z.number(),
  reason: z.string().min(1).max(500),
  referenceType: z.string().max(50).optional(),
  referenceId: z.number().int().positive().nullable().optional(),
});

export const InventoryAdjustmentsBodySchema = z.object({
  lines: z.array(InventoryAdjustmentLineSchema).min(1),
});
```
