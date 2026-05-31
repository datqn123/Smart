# 📄 API SPEC: `PATCH /api/v1/inventory/{id}` — Cập nhật một dòng tồn - Task007

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — dialog **Sửa** (một dòng)  
> **Tags**: RESTful, Inventory, Update

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Cho phép cập nhật **thông tin cấu hình** của một dòng tồn (vị trí lưu, định mức tối thiểu, số lô, hạn SD, …) theo quyền UC6 — **không** “âm thầm” thay đổi số lượng tồn thực tế.
- **Ai được lợi**: nhân viên được phép chỉnh master data tồn; Owner kiểm soát đúng vị trí–lô trên kệ.
- **Phạm vi Task này**: **một** endpoint `PATCH /inventory/{id}` (partial update).
- **Out of scope**: sửa nhiều dòng một lần → Task008; điều chỉnh `quantity` có log → Task010; đọc danh sách → Task005.

---

## 2. Mục đích Endpoint

**`PATCH /api/v1/inventory/{id}`** áp dụng các thay đổi **một phần** trên **một** bản ghi `Inventory` (và ràng buộc liên quan), ví dụ đổi `location_id`, `min_quantity`, `batch_number`, `expiry_date` — phục vụ luồng “Sửa thông tin tồn kho” khi user chỉnh **một** hàng.

**Khi nào gọi**: sau khi user chỉnh form và xác nhận **một** dòng (hoặc FE gọi lần lượt từng `id` nếu không dùng bulk).

**Sau khi thành công**: dòng tồn trên DB phản ánh meta mới; client nhận object đã cập nhật để đồng bộ UI.

**Endpoint này KHÔNG:**

- **Không** dùng để tăng/giảm `quantity` (tránh không có `InventoryLogs`) — mọi thay đổi số lượng thực tế phải qua **Task010** hoặc phiếu nhập/xuất chuẩn.
- Không thay thế **bulk** nhiều `id` trong một request — dùng **Task008**.
- **Giá vốn** không là cột `Inventory` trong DB spec — không ép endpoint này phải sửa giá; nếu FE gửi, backend có thể **400** + hướng dẫn API giá sản phẩm.

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7**.  
**DB**: `Inventory`, FK `WarehouseLocations`.

**Task liên quan**: [`API_Task010_inventory_post_adjustments.md`](API_Task010_inventory_post_adjustments.md), [`API_Task008_inventory_bulk_patch.md`](API_Task008_inventory_bulk_patch.md).

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7** |
| **Endpoint** | `/api/v1/inventory/{id}` |
| **Method** | `PATCH` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner / Staff (theo policy UC6) |
| **Use Case Ref** | UC6 |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

### 5.2 Path parameters

| Tham số | Kiểu | Bắt buộc | Mô tả |
| :------ | :--- | :------- | :---- |
| `id` | number (int > 0) | Có | `Inventory.id` cần cập nhật |

### 5.3 Query parameters

_Không có_

### 5.4 Request body (JSON partial, camelCase)

Ít nhất **một** trong các trường dưới phải có trong body (PATCH partial).

```json
{
  "locationId": 3,
  "minQuantity": 60,
  "batchNumber": "LOT-2026-01",
  "expiryDate": "2026-12-31",
  "unitId": 5
}
```

| Trường | Kiểu | Bắt buộc | Mô tả / ràng buộc |
| :----- | :--- | :------- | :---------------- |
| `locationId` | number | Tùy chọn | FK `WarehouseLocations.id` |
| `minQuantity` | number | Tùy chọn | `>= 0` |
| `batchNumber` | string \| null | Tùy chọn | UNIQUE theo cặp `product_id` + `location_id` (policy DB) |
| `expiryDate` | string \| null | Tùy chọn | `YYYY-MM-DD` |
| `unitId` | number | Tùy chọn | Chỉ khi policy nghiệp vụ cho phép đổi đơn vị |

---

## 6. Thành công — `200 OK`

**Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 101,
    "productId": 12,
    "productName": "Nước suối 500ml",
    "skuCode": "SKU-WAT-500",
    "barcode": "8934563123456",
    "locationId": 3,
    "warehouseCode": "WH01",
    "shelfCode": "A1",
    "batchNumber": "LOT-2026-01",
    "expiryDate": "2026-12-31",
    "quantity": 240,
    "minQuantity": 60,
    "unitId": 5,
    "unitName": "Chai",
    "costPrice": 4500,
    "updatedAt": "2026-04-23T10:15:00Z",
    "isLowStock": false,
    "isExpiringSoon": false,
    "totalValue": 1080000
  },
  "message": "Đã cập nhật thông tin tồn kho"
}
```

Shape `data` **khớp** phần tử `items` trong [`API_Task005_inventory_get_list.md`](API_Task005_inventory_get_list.md) (sau khi backend join đầy đủ).

---

## 7. Logic nghiệp vụ & Database (Business Logic)

Tham chiếu: [`Database_Specification.md`](../UC/Database_Specification.md) §16 `Inventory`, §5 `WarehouseLocations`, §7 `Products`. Sau commit: [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md), [`API_Task012_inventory_staff_change_notify_owner.md`](API_Task012_inventory_staff_change_notify_owner.md).

### 7.1 Quy trình thực thi (Step-by-Step)

1. **Xác thực JWT** → `user_id`, vai trò. Thất bại → **401**. Không đủ quyền UC6 → **403**.

2. **Validation body**  
   - Body rỗng / không có field nào được phép → **400**.  
   - Field lạ hoặc field cấm (`quantity`, `costPrice`, …) → **400** (`details`).  
   - `expiry_date` sai định dạng → **400**.

3. **Khóa & đọc bản ghi hiện tại** (khuyến nghị trong transaction)

```sql
SELECT
  i.id,
  i.product_id,
  i.location_id,
  i.batch_number,
  i.expiry_date,
  i.min_quantity,
  i.quantity,
  p.status AS product_status,
  wl.status AS location_status
FROM Inventory i
JOIN Products p ON p.id = i.product_id
JOIN WarehouseLocations wl ON wl.id = i.location_id
WHERE i.id = :id
FOR UPDATE OF i;
```

- Không có dòng → **404**.  
- `wl.status = 'Maintenance'` hoặc `p.status = 'Inactive'` (và policy từ chối sửa meta) → **409**.

4. **Nếu body có `locationId`** — xác nhận vị trí đích hợp lệ

```sql
SELECT id, status FROM WarehouseLocations WHERE id = :new_location_id;
```

- Không tồn tại → **400** hoặc **404** (chốt một mã).  
- `status = 'Maintenance'` và policy chặn → **409**.

5. **Kiểm tra UNIQUE** `uq_inventory_product_location_batch`  
   - Sau khi áp dụng giá trị mới (merge logic ứng dụng), kiểm tra trùng `(product_id, location_id, batch_number)` với dòng khác:

```sql
SELECT COUNT(*) FROM Inventory
WHERE product_id = :product_id
  AND location_id = :effective_location_id
  AND COALESCE(batch_number, '') = COALESCE(:effective_batch_number, '')
  AND id <> :id;
```

- `COUNT(*) > 0` → **409**.

6. **`UPDATE` chỉ các cột cho phép** (theo DB §16 — **không** có `unit_id` trên `Inventory`; xem §7.2 cho `unitId` API)

```sql
UPDATE Inventory
SET
  location_id = :location_id,       -- chỉ SET nếu client gửi field
  min_quantity = :min_quantity,
  batch_number = :batch_number,
  expiry_date = :expiry_date,
  updated_at = CURRENT_TIMESTAMP
WHERE id = :id;
```

_(Backend build câu `UPDATE` động chỉ gồm các cột có trong body hợp lệ.)_

7. **`COMMIT`** (hoặc rollback nếu lỗi).

8. **Hậu xử lý (cùng transaction hoặc transaction phụ ngay sau — bám Task011/012)**  
   - `INSERT INTO SystemLogs (log_level, module, action, user_id, message, context_data) VALUES (...)` với `context_data` before/after.  
   - Nếu actor là Staff: `INSERT INTO Notifications ...` theo Task012 (nếu bảng tồn tại).

### 7.2 Các ràng buộc (Constraints)

- **`Inventory`**: `chk_quantity` — PATCH này **không** đổi `quantity`; không vi phạm CHECK nếu không đụng cột.  
- **`uq_inventory_product_location_batch`**: UNIQUE (`product_id`, `location_id`, `batch_number`) — bước 5.  
- **FK**: `location_id` → `WarehouseLocations.id` (RESTRICT).  
- **`unitId` trong JSON API**: bảng `Inventory` **chưa** có `unit_id` trong `Database_Specification.md` §16 — triển khai phải **400** “chưa hỗ trợ” **hoặc** migration + cập nhật spec DB trước khi nhận field.  
- **Không** ghi `InventoryLogs` bắt buộc khi không đổi `quantity` (theo ma trận Task011).  
- **Trigger**: theo `schema.sql` nếu có `updated_at` tự động — tránh ghi đè mâu thuẫn.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request (Body rỗng hoặc field không hợp lệ)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "body": "Cần ít nhất một trường để cập nhật",
    "expiryDate": "Định dạng phải là YYYY-MM-DD"
  }
}
```

#### 400 Bad Request (Client gửi field không được phép — ví dụ `costPrice` / `quantity`)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Không được phép cập nhật trường này qua API này",
  "details": {
    "quantity": "Thay đổi số lượng thực tế phải dùng POST /api/v1/inventory/adjustments (Task010)"
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
  "message": "Bạn không có quyền sửa thông tin tồn kho"
}
```

#### 404 Not Found

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy dòng tồn kho yêu cầu"
}
```

#### 409 Conflict (Vị trí bảo trì, sản phẩm ngừng kinh doanh, hoặc vi phạm UNIQUE lô–vị trí)

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể cập nhật do xung đột trạng thái hoặc trùng lô tại cùng vị trí"
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

export const InventoryPatchSchema = z.object({
  locationId: z.number().int().positive().optional(),
  minQuantity: z.number().nonnegative().optional(),
  batchNumber: z.string().max(100).nullable().optional(),
  expiryDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable().optional(),
  unitId: z.number().int().positive().optional(),
});
```
