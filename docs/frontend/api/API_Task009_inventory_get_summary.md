# 📄 API SPEC: `GET /api/v1/inventory/summary` — Chỉ KPI tồn kho - Task009

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — thẻ KPI màn **Tồn kho** (tách tải tùy chọn)  
> **Tags**: RESTful, Inventory, Aggregate

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Tách **tổng hợp KPI** khỏi API danh sách phân trang khi bảng `Inventory` lớn hoặc khi FE cần **refresh KPI** thường xuyên mà không tải lại toàn bộ `items`.
- **Ai được lợi**: frontend giảm payload; backend có thể cache TTL / materialized view cho dashboard nhỏ trên cùng màn.
- **Phạm vi Task này**: **chỉ** `GET /inventory/summary`.
- **Out of scope**: danh sách + KPI trong một response → Task005; chi tiết / ghi — Task006,007,010.

---

## 2. Mục đích Endpoint

**`GET /api/v1/inventory/summary`** trả về **duy nhất** khối số liệu tổng hợp (`totalSkus`, `totalValue`, `lowStockCount`, `expiringSoonCount`) trên phạm vi quyền và **cùng bộ lọc** như Task005: `search`, `stockLevel`, `locationId`, `categoryId` (tất cả tùy chọn).

**Khi nào gọi**: định kỳ poll KPI; sau khi Task010 thành công chỉ cần làm mới số trên thẻ; khi Task005 intentionally không gửi `summary` để giảm tải.

**Sau khi thành công**: client cập nhật bốn KPI card.

**Endpoint này KHÔNG:**

- Không trả `items` / không phân trang danh sách tồn — đó là **Task005**.
- Không ghi DB.
- Không thay thế báo cáo kho đầy đủ cấp doanh nghiệp (chỉ phục vụ cùng định nghĩa KPI với Task005).

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7**.  
**DB**: `Inventory`, `Products` — cùng logic `summary` như [`API_Task005_inventory_get_list.md`](API_Task005_inventory_get_list.md).

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7** |
| **Endpoint** | `/api/v1/inventory/summary` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Giống Task005 — `can_manage_inventory` (JWT) |
| **Use Case Ref** | UC6 |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
```

### 5.2 Query parameters

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
| :------ | :--- | :------- | :------- | :---- |
| `search` | string | Không | — | Giống Task005 — `ILIKE` tên hoặc SKU |
| `stockLevel` | string | Không | `all` | Giống Task005: `all` \| `in_stock` \| `low_stock` \| `out_of_stock` |
| `locationId` | number (int > 0) | Không | — | Giới hạn tổng hợp theo `Inventory.location_id` |
| `categoryId` | number (int > 0) | Không | — | Giới hạn theo `Products.category_id` |

### 5.3 Request body

_Không có_

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "totalSkus": 128,
    "totalValue": 452300000.5,
    "lowStockCount": 12,
    "expiringSoonCount": 5
  },
  "message": "Thành công"
}
```

Định nghĩa cột giống `data.summary` trong Task005.

---

## 7. Logic nghiệp vụ & Database (Business Logic)

Kết quả **cùng định nghĩa** `data.summary` trong [`API_Task005_inventory_get_list.md`](API_Task005_inventory_get_list.md) khi truyền **cùng** `search` / `stockLevel` / `locationId` / `categoryId`, nhưng **không** trả `items` (và không dùng `page` / `limit` / `sort`).

### 7.1 Quy trình thực thi (Step-by-Step)

1. **Xác thực JWT** → **401** / **403** nếu không hợp lệ.

2. **Validation query** (`stockLevel`, `locationId`, `categoryId`, …) → **400** nếu sai (cùng quy tắc Task005).

3. **Một query aggregate** (cùng JOIN + `WHERE` filter như Task005 `loadSummary`, không `LIMIT/OFFSET`):

```sql
SELECT
  COUNT(*) AS total_skus,
  COALESCE(SUM(i.quantity * COALESCE(latest_pph.cost_price, 0)), 0) AS total_value,
  COUNT(*) FILTER (WHERE i.quantity > 0 AND i.quantity <= i.min_quantity) AS low_stock_count,
  COUNT(*) FILTER (
    WHERE i.expiry_date IS NOT NULL
      AND i.expiry_date <= CURRENT_DATE + INTERVAL '30 day'
      AND i.quantity > 0
  ) AS expiring_soon_count
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
WHERE /* RBAC + stockLevel + search + optional locationId / categoryId — đồng bộ Task005 */;
```

4. Map 4 cột aggregate → JSON `data`.

### 7.2 Các ràng buộc (Constraints)

- Cùng ràng buộc JOIN/FK như Task005; endpoint **read-only**.  
- **Cache / materialized view** (tuỳ chọn): nếu bật — ghi rõ TTL và invalidation khi Task010 ghi `Inventory`.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request (Query không hợp lệ)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Tham số truy vấn không hợp lệ",
  "details": {
    "locationId": "Giá trị phải là số nguyên dương"
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
  "message": "Bạn không có quyền xem tổng hợp KPI tồn kho"
}
```

#### 404 Not Found

_Không áp dụng_ cho `GET /inventory/summary`.

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

export const InventorySummaryQuerySchema = z.object({
  search: z.string().optional(),
  stockLevel: z.enum(["all", "in_stock", "low_stock", "out_of_stock"]).optional(),
  locationId: z.coerce.number().int().positive().optional(),
  categoryId: z.coerce.number().int().positive().optional(),
});
```
