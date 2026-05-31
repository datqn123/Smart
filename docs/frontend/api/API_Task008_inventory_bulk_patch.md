# 📄 API SPEC: `PATCH /api/v1/inventory/bulk` — Cập nhật nhiều dòng tồn - Task008

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — dialog **Sửa thông tin tồn kho** (nhiều dòng)  
> **Tags**: RESTful, Inventory, Bulk

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Giảm số lần round-trip khi user chọn **nhiều** dòng tồn và chỉnh meta (vị trí, định mức, lô, HSD) trong **một** thao tác lưu — phù hợp dialog bulk trên UI.
- **Ai được lợi**: nhân viên kho thao tác hàng loạt; hệ thống đảm bảo **nhất quán transaction** (tất cả hoặc không).
- **Phạm vi Task này**: **chỉ** `PATCH /inventory/bulk`.
- **Out of scope**: cập nhật **một** dòng → Task007; thay đổi **quantity** → Task010.

---

## 2. Mục đích Endpoint

**`PATCH /api/v1/inventory/bulk`** nhận một mảng các `{ id, ...partialFields }` và áp dụng **cùng quy tắc** như Task007 cho **từng** `id` trong **một** yêu cầu HTTP.

**Khi nào gọi**: user bấm **Lưu** trên dialog sửa nhiều hàng đã chọn trên bảng tồn kho.

**Sau khi thành công**: tất cả các dòng được cập nhật (hoặc rollback toàn bộ nếu chọn mô hình all-or-nothing).

**Endpoint này KHÔNG:**

- Không dùng để **tạo** dòng tồn mới (không POST).
- **Không** chứa `deltaQty` / thay `quantity` — dùng **Task010** hoặc phiếu nghiệp vụ.
- Không thay thế đọc danh sách (Task005) hay chi tiết một dòng (Task006).

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7**.  
**DB**: giống [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md).

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7** |
| **Endpoint** | `/api/v1/inventory/bulk` |
| **Method** | `PATCH` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner / Staff theo UC6 |
| **Use Case Ref** | UC6 |

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

```json
{
  "items": [
    {
      "id": 101,
      "locationId": 3,
      "minQuantity": 60,
      "batchNumber": "LOT-2026-01",
      "expiryDate": "2026-12-31",
      "unitId": 5
    },
    {
      "id": 102,
      "minQuantity": 10
    }
  ]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `items` | array | Có | Ít nhất 1 phần tử |
| `items[].id` | number | Có (mỗi phần tử) | `Inventory.id` |
| `items[].locationId` | number | Tùy chọn | Giống Task007 |
| `items[].minQuantity` | number | Tùy chọn | `>= 0` |
| `items[].batchNumber` | string \| null | Tùy chọn | Giống Task007 |
| `items[].expiryDate` | string \| null | Tùy chọn | `YYYY-MM-DD` |
| `items[].unitId` | number | Tùy chọn | Giống Task007 |

**Không** gửi `quantity` — mọi thay đổi số lượng thực tế qua Task010.

---

## 6. Thành công — `200 OK` (all-or-nothing)

**Code**: `200 OK`

Khuyến nghị triển khai: **một transaction** — hoặc tất cả dòng hợp lệ đều commit, hoặc rollback toàn bộ.

```json
{
  "success": true,
  "data": {
    "updated": [
      {
        "id": 101,
        "productId": 12,
        "skuCode": "SKU-WAT-500",
        "locationId": 3,
        "minQuantity": 60,
        "batchNumber": "LOT-2026-01",
        "expiryDate": "2026-12-31",
        "unitId": 5,
        "updatedAt": "2026-04-23T10:20:00Z"
      },
      {
        "id": 102,
        "productId": 12,
        "skuCode": "SKU-WAT-500",
        "locationId": 2,
        "minQuantity": 10,
        "batchNumber": "LOT-2026-02",
        "expiryDate": "2027-06-01",
        "unitId": 5,
        "updatedAt": "2026-04-23T10:20:00Z"
      }
    ],
    "failed": []
  },
  "message": "Đã cập nhật thông tin tồn kho (hàng loạt)"
}
```

_(Nếu sau này chọn mô hình “một phần thành công”: có thể dùng **207** và điền `failed[]` với `id` + `error` + `message` — cần spec riêng; mặc định task này là **all-or-nothing**.)_

---

## 7. Logic nghiệp vụ & Database (Business Logic)

Mỗi phần tử `items[]` áp dụng **cùng quy tắc** như [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md) §7. Tất cả trong **một transaction** (all-or-nothing).

### 7.1 Quy trình thực thi (Step-by-Step)

1. **Xác thực JWT** → **401** / **403** nếu không hợp lệ.

2. **Validation body** — `items` rỗng, thiếu `id`, field cấm → **400**.

3. **`BEGIN` transaction.**

4. **Với mỗi phần tử `items[k]`** (theo thứ tự mảng):

   a. `SELECT … FROM Inventory i JOIN Products p … JOIN WarehouseLocations wl … WHERE i.id = :id FOR UPDATE OF i` — không có dòng → **ROLLBACK** → **404** (hoặc gom lỗi thành một thông điệp).  
   b. Kiểm tra `product_status`, `location_status`, FK `location_id` mới (nếu có), UNIQUE batch — giống Task007 §7.1 bước 3–5. Vi phạm → **ROLLBACK** → **409** hoặc **404**.  
   c. `UPDATE Inventory SET … WHERE id = :id` (chỉ cột gửi cho phần tử đó).

5. **Nếu mọi `UPDATE` thành công — `COMMIT`.**  
   - Một lỗi ở bất kỳ phần tử nào → **ROLLBACK** toàn bộ (mặc định task này).

6. **Hậu xử lý Task011 / Task012** (ưu tiên cùng transaction với bước 4–5 nếu DB cho phép ghi log trong cùng TX; nếu không — transaction thứ 2 ngay sau `COMMIT` của bước 5, nhưng khi đó phải có chiến lược bù nếu log fail):

   - Một `INSERT SystemLogs` với `action = 'INVENTORY_BULK_META_UPDATE'` và `context_data` chứa mảng `inventoryId` + before/after tóm tắt, **hoặc** nhiều dòng log per item (chốt triển khai).  
   - Staff → `INSERT Notifications` theo Task012.

### 7.2 Các ràng buộc (Constraints)

- Giống Task007: `uq_inventory_product_location_batch`, FK `location_id`, `chk_quantity` (không đổi quantity).  
- **Độ dài gói request**: giới hạn số phần tử `items` (ví dụ max 100) để tránh timeout — ghi rõ trong triển khai, vượt → **400**.  
- **Không** `SELECT *` ở mọi bước đọc.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request (Mảng rỗng hoặc phần tử thiếu `id` / field không hợp lệ)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "items": "Cần ít nhất một phần tử",
    "items[0].id": "Trường id là bắt buộc"
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
  "message": "Bạn không có quyền sửa thông tin tồn kho hàng loạt"
}
```

#### 404 Not Found (Một hoặc nhiều `id` không tồn tại — với mô hình all-or-nothing)

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Một hoặc nhiều dòng tồn kho không tồn tại hoặc ngoài phạm vi quyền"
}
```

#### 409 Conflict (Ít nhất một dòng vi phạm ràng buộc nghiệp vụ / UNIQUE)

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể cập nhật do xung đột trạng thái hoặc trùng lô tại cùng vị trí (một hoặc nhiều dòng trong yêu cầu)"
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

const BulkItemSchema = z.object({
  id: z.number().int().positive(),
  locationId: z.number().int().positive().optional(),
  minQuantity: z.number().nonnegative().optional(),
  batchNumber: z.string().max(100).nullable().optional(),
  expiryDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable().optional(),
  unitId: z.number().int().positive().optional(),
});

export const InventoryBulkPatchSchema = z.object({
  items: z.array(BulkItemSchema).min(1),
});
```
