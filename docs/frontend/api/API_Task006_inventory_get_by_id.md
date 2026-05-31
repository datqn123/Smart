# 📄 API SPEC: `GET /api/v1/inventory/{id}` — Chi tiết một dòng tồn - Task006

> **Trạng thái**: Draft *(SRS backend Approved 25/04/2026 — `backend/docs/srs/SRS_Task006_inventory-get-by-id.md`: `relatedLines` chỉ lô **còn hàng** `quantity > 0`; ngoài phạm vi dữ liệu → **404**.)*  
> **Feature**: Inventory / UC6 — dialog **chi tiết lô** (`StockBatchDetailsDialog`)  
> **Tags**: RESTful, Inventory, Read

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Cho phép người dùng **đào sâu một dòng tồn** (một bản ghi `Inventory` cụ thể: SKU + vị trí + lô + HSD + số lượng) để đối chiếu trước khi điều chỉnh hoặc khi cần hiển thị **các lô / dòng liên quan** cùng sản phẩm.
- **Ai được lợi**: người xem popup chi tiết trên màn Tồn kho; có thể tái sử dụng cho màn hình khác cần “chi tiết một dòng”.
- **Phạm vi Task này**: **chỉ** `GET /inventory/{id}` — một bản ghi + payload tùy chọn `relatedLines`.
- **Out of scope**: danh sách phân trang → Task005; ghi cập nhật meta → Task007/008; thay đổi số lượng → Task010.

---

## 2. Mục đích Endpoint

**`GET /api/v1/inventory/{id}`** trả về **đúng một** dòng tồn (đủ trường hiển thị như trên bảng + thông tin bổ sung nếu cần) và tùy chọn **`relatedLines`** để UI mô phỏng “nhiều lô” của cùng sản phẩm mà không phải tự ghép từ toàn bộ list.

**Khi nào gọi**: người dùng bấm **xem chi tiết** (icon mắt) trên một hàng; hoặc trước khi mở form sửa nếu FE muốn hydrate từ server.

**Sau khi thành công**: client có object chuẩn để render dialog; có thể cache ngắn hạn theo `id`.

**Endpoint này KHÔNG:**

- Không thay thế **danh sách** (không có phân trang, không trả toàn kho).
- Không cập nhật dữ liệu (read-only).
- Không trả lịch sử biến động tồn — tra cứu log thuộc màn/API riêng (catalog `GET /inventory/logs`, chưa có Task spec).

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7**.  
**DB**: `Inventory`, join `Products`, `WarehouseLocations`, `ProductUnits`.

**Task liên quan**: [`API_Task005_inventory_get_list.md`](API_Task005_inventory_get_list.md), [`API_Task007_inventory_patch.md`](API_Task007_inventory_patch.md).

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7** |
| **Endpoint** | `/api/v1/inventory/{id}` |
| **Method** | `GET` |
| **Path** | `id` — `BIGINT`, khóa `Inventory.id` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin — trong phạm vi dữ liệu được phép |
| **Use Case Ref** | UC6 |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
```

### 5.2 Path parameters

| Tham số | Kiểu | Bắt buộc | Mô tả |
| :------ | :--- | :------- | :---- |
| `id` | number (int > 0) | Có | Khóa `Inventory.id` |

### 5.3 Query parameters

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
| :------ | :--- | :------- | :------- | :---- |
| `include` | string | Không | — | **Chốt:** chỉ nhận giá trị `relatedLines` (whitelist). **Không** có `include` hoặc để trống → backend **không** chạy truy vấn phụ, trả `relatedLines: []`. Giá trị khác whitelist → **400** + `details.include`. |

### 5.4 Request body

_Không có_

### 5.5 Ánh xạ UI → endpoint này

| Khu vực UI | Nội dung | Ghi chú |
| :----------- | :-------- | :------ |
| Popup chi tiết lô (`StockBatchDetailsDialog`) | `GET …/inventory/{id}` | Hydrate từ server thay mock |
| Khối “các lô cùng SP” trong dialog | `?include=relatedLines` | Tránh ghép tay từ `GET /inventory` (Task005) |

---

## 6. Thành công — `200 OK`

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
    "minQuantity": 50,
    "unitId": 5,
    "unitName": "Chai",
    "costPrice": 4500,
    "updatedAt": "2026-04-23T08:00:00Z",
    "isLowStock": false,
    "isExpiringSoon": false,
    "totalValue": 1080000,
    "relatedLines": [
      {
        "id": 102,
        "batchNumber": "LOT-2026-02",
        "quantity": 100,
        "expiryDate": "2027-06-01",
        "warehouseCode": "WH01",
        "shelfCode": "A1"
      }
    ]
  },
  "message": "Thành công"
}
```

**`relatedLines`**: các bản ghi `Inventory` khác cùng `product_id`, **`quantity > 0`** (lô hết hàng không nằm trong response này — UX “Xem thêm” / API bổ sung theo backlog). Có thể `[]`.

---

## 7. Logic nghiệp vụ & Database (Business Logic)

Tham chiếu: [`Database_Specification.md`](../UC/Database_Specification.md) §16 `Inventory`, §5 `WarehouseLocations`, §7 `Products`, §8 `ProductUnits`, §9 `ProductPriceHistory`.

### 7.1 Quy trình thực thi (Step-by-Step)

1. **Xác thực JWT** → lấy `user_id`, vai trò. Lỗi token → **401**. Không có quyền đọc tồn → **403**.

2. **Validation path `id`**  
   - `id` không phải số nguyên dương → **400** + `details.id`.

3. **Đọc một dòng tồn (chính)**

```sql
SELECT
  i.id,
  i.product_id,
  p.name AS product_name,
  p.sku_code,
  p.barcode,
  i.location_id,
  wl.warehouse_code,
  wl.shelf_code,
  i.batch_number,
  i.expiry_date,
  i.quantity,
  i.min_quantity,
  pu.id AS unit_id,
  pu.unit_name,
  latest_pph.cost_price,
  i.updated_at
FROM Inventory i
JOIN Products p ON p.id = i.product_id
JOIN WarehouseLocations wl ON wl.id = i.location_id
JOIN ProductUnits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
LEFT JOIN LATERAL (
  SELECT pph.cost_price
  FROM ProductPriceHistory pph
  WHERE pph.product_id = p.id AND pph.unit_id = pu.id
  ORDER BY pph.effective_date DESC, pph.id DESC
  LIMIT 1
) latest_pph ON true
WHERE i.id = :id /* AND RBAC scope */;
```

- Không có dòng → **404** (hoặc **403** nếu policy che giấu tồn tại).  
- Map sang JSON `data` + cờ read-model (`isLowStock`, `isExpiringSoon`, `totalValue`).

4. **`relatedLines` (chỉ khi `include=relatedLines`)**

```sql
SELECT
  i2.id,
  i2.batch_number,
  i2.quantity,
  i2.expiry_date,
  wl2.warehouse_code,
  wl2.shelf_code
FROM Inventory i2
JOIN WarehouseLocations wl2 ON wl2.id = i2.location_id
WHERE i2.product_id = :product_id_from_step3
  AND i2.id <> :id
  AND i2.quantity > 0
  AND /* RBAC */;
```

- Có thể trả `[]` nếu không có lô khác.

### 7.2 Các ràng buộc (Constraints)

- **FK**: `Inventory.product_id`, `Inventory.location_id`; `ProductPriceHistory.unit_id` phải khớp đơn vị cơ sở khi lấy `cost_price`.  
- **`uq_inventory_product_location_batch`**: không ảnh hưởng GET.  
- **Không** trả `password_hash`, dữ liệu người dùng không liên quan.  
- **Trigger**: không bắt buộc cho GET.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request (Định dạng `id` hoặc `include` không hợp lệ)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Tham số yêu cầu không hợp lệ",
  "details": {
    "id": "Giá trị phải là số nguyên dương",
    "include": "Giá trị hợp lệ: relatedLines (hoặc bỏ qua tham số)"
  }
}
```

_(Một trong các khóa `details` có thể vắng tùy lỗi thực tế.)_

#### 401 Unauthorized

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
}
```

#### 403 Forbidden (Có token nhưng không được phép xem dòng này)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền xem bản ghi tồn kho này"
}
```

#### 404 Not Found (Không tồn tại hoặc ngoài phạm vi tenant / quyền)

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy dòng tồn kho yêu cầu"
}
```

_(Có thể dùng chung 404 cho “ẩn” tài nguyên ngoài phạm vi — không tiết lộ tồn tại bản ghi.)_

#### 409 Conflict

_Không áp dụng_ cho `GET` chỉ đọc.

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

---

## 9. Zod (path + query — FE)

```typescript
import { z } from "zod";

export const InventoryIdParamSchema = z.object({
  id: z.coerce.number().int().positive(),
});

/** Query tùy chọn; omit = không tải relatedLines (server trả []). */
export const InventoryGetByIdQuerySchema = z.object({
  include: z.literal("relatedLines").optional(),
});
```

---

## 10. Ghi chú FE

- Gọi chi tiết tối thiểu: `GET /api/v1/inventory/:id` — đủ render dialog; thêm `?include=relatedLines` khi cần danh sách lô liên quan.
- Sau Task007 (PATCH), có thể gọi lại GET này để refresh dialog.
