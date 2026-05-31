# 📄 API SPEC: `GET /api/v1/inventory` — Danh sách tồn kho + KPI - Task005

> **Trạng thái**: Draft  
> **Feature**: Inventory / UC6 — màn **Tồn kho** (`StockPage`, `StockTable`, `StockToolbar`)  
> **Tags**: RESTful, Inventory, Pagination, KPI

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Hỗ trợ **UC6 — Manage inventory list**: nhân viên kho / Owner xem **toàn cảnh tồn** (theo SKU–vị trí–lô), lọc theo trạng thái còn hàng / sắp hết / hết hàng, tìm nhanh theo tên hoặc mã sản phẩm, đồng thời có **chỉ số KPI** để ưu tiên xử lý (giá trị kho, sắp hết, cận date).
- **Ai được lợi**: người vận hành màn **Danh sách tồn kho**; hệ thống có một **hợp đồng đọc** thống nhất thay cho mock cục bộ.
- **Phạm vi Task này**: **chỉ** đặc tả **một** endpoint `GET /inventory` (danh sách phân trang + `summary` trong cùng response).
- **Out of scope**: chi tiết một dòng → [`API_Task006_inventory_get_by_id.md`](API_Task006_inventory_get_by_id.md); KPI tách riêng (cache) → [`API_Task009_inventory_get_summary.md`](API_Task009_inventory_get_summary.md); cập nhật meta / số lượng → Task007,008,010.

---

## 2. Mục đích Endpoint

**`GET /api/v1/inventory`** cung cấp **dữ liệu đọc** cho bảng tồn kho và (trong cùng response) khối **`summary`** phục vụ bốn thẻ KPI trên UI — tức là **một lần gọi** (hoặc FE có thể kết hợp Task009 nếu tách tải).

**Khi nào gọi**: mở màn Tồn kho; **khi tải thêm** (giao diện chuẩn: `page=1, limit=20` rồi tăng `page` khi người dùng **cuộn tới gần cuối** bảng) hoặc đổi `page` / `limit` tương đương; đổi ô tìm kiếm hoặc bộ lọc trạng thái; cần refresh sau khi các endpoint ghi (Task007/008/010) đã thành công.

**Sau khi thành công**: client nhận danh sách `items` đã join sản phẩm + vị trí + đơn vị + cờ read-model (`isLowStock`, …) và tổng hợp `summary` trên **toàn phạm vi quyền** (không chỉ trang hiện tại), để render đúng KPI.

**Endpoint này KHÔNG:**

- Không ghi / sửa / xóa bất kỳ bản ghi `Inventory` nào (read-only).
- Không trả chi tiết đủ cho popup “xem lô” nếu cần thêm `relatedLines` — dùng **Task006**.
- Không thay cho báo cáo tài chính hay dashboard tổng hợp cấp cao (chỉ phục vụ màn tồn kho UC6).

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §2–§3, **§4.7**.  
**DB**: [`Database_Specification.md`](../UC/Database_Specification.md) — `Inventory` (§16), `Products`, `WarehouseLocations`, `ProductUnits`.

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.7** |
| **Endpoint** | `/api/v1/inventory` |
| **Method** | `GET` |
| **Authentication** | `Bearer` (bắt buộc) |
| **RBAC** | Owner, Staff, Admin — chỉ đọc tồn trong phạm vi tenant / quyền UC6 |
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
| `search` | string | Không | — | `Products.name` hoặc `sku_code` (ILIKE) |
| `stockLevel` | string | Không | `all` | `all`, `in_stock`, `low_stock`, `out_of_stock` |
| `locationId` | number (int > 0) | Không | — | Lọc `Inventory.location_id` |
| `categoryId` | number (int > 0) | Không | — | Lọc `Products.category_id` |
| `productId` | number (int > 0) | Không | — | Lọc `Inventory.product_id` (ví dụ lấy các dòng tồn / lô của một SKU cho form phiếu nhập) |
| `page` | number (int ≥ 1) | Không | `1` | Số trang |
| `limit` | number (int 1–100) | Không | `20` | Số bản ghi mỗi trang |
| `sort` | string | Không | (theo policy backend) | Whitelist, ví dụ `updatedAt:desc` |

**`stockLevel`**: `in_stock` → `quantity > min_quantity`; `low_stock` → `0 < quantity <= min_quantity`; `out_of_stock` → `quantity = 0`.

### 5.3 Request body

_Không có_

---

## 6. Ánh xạ UI → endpoint này

| Khu vực UI | Nội dung | Ghi chú |
| :----------- | :-------- | :------ |
| KPI *Tổng mặt hàng*, *Tổng giá trị*, *Sắp hết*, *Cận hạn SD* | `data.summary` | Hoặc Task009 nếu tách |
| Ô tìm kiếm “tên hoặc mã SP” | Query `search` | `Products.name` / `sku_code` |
| Lọc *Còn hàng / Sắp hết / Hết hàng* | Query `stockLevel` | Giống `StockPage` |
| Bảng danh sách | `data.items` + phân trang | |

**Read-model từng phần tử `items`**: `isLowStock`; `isExpiringSoon` (HSD trong 30 ngày); `totalValue = quantity * costPrice` (giá vốn đơn vị cơ sở — join giá hiện hành / policy backend).

---

## 7. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "summary": {
      "totalSkus": 128,
      "totalValue": 452300000.5,
      "lowStockCount": 12,
      "expiringSoonCount": 5
    },
    "items": [
      {
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
        "totalValue": 1080000
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 128
  },
  "message": "Thành công"
}
```

`summary` tính trên **toàn bộ** tồn trong phạm vi quyền (không chỉ trang hiện tại).

---

## 8. Logic nghiệp vụ & Database (Business Logic)

Tham chiếu cột: [`Database_Specification.md`](../UC/Database_Specification.md) §5 `WarehouseLocations`, §7 `Products`, §8 `ProductUnits`, §9 `ProductPriceHistory`, §16 `Inventory`.

### 8.1 Quy trình thực thi (Step-by-Step)

1. **Xác thực JWT**  
   - Parse Bearer token → `user_id`, `role_id` / tên vai. Token sai / hết hạn → **401**.  
   - Kiểm tra quyền đọc tồn UC6 (Owner / Staff / Admin theo policy). Không đủ quyền → **403**.

2. **Validation query**  
   - `stockLevel`, `page`, `limit`, `sort`, `locationId`, `categoryId`, `search` theo schema API (Zod §10). Sai định dạng → **400** + `details`.

3. **Tổng hợp `summary` (toàn phạm vi lọc, không phân trang)**  
   - Base `FROM Inventory i INNER JOIN Products p ON p.id = i.product_id INNER JOIN WarehouseLocations wl ON wl.id = i.location_id` + `WHERE` phạm vi quyền (ví dụ lọc kho theo user nếu policy có).  
   - Áp dụng cùng bộ lọc query với danh sách: `search` (ILIKE trên `p.name`, `p.sku_code`), `stockLevel` (điều kiện trên `i.quantity`, `i.min_quantity`), `locationId`, `categoryId`.  
   - Một query aggregate (ví dụ):

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
WHERE /* RBAC + filters */;
```

_(Nếu định nghĩa KPI “totalSkus” khác `COUNT(*)` dòng `Inventory`, chỉnh query cho khớp `API_PROJECT_DESIGN` / BA.)_

4. **Đếm tổng bản ghi phân trang (`total`)**  
   - `SELECT COUNT(*) FROM …` cùng `JOIN`/`WHERE` như bước list (không `SELECT *`).

5. **Truy vấn trang `items`**  
   - `ORDER BY` theo whitelist `sort` (mặc định ví dụ `i.updated_at DESC`).  
   - `LIMIT :limit OFFSET (:page - 1) * :limit`.  
   - Cột đọc tối thiểu (ví dụ):

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
WHERE /* RBAC + filters */
ORDER BY /* whitelist */
LIMIT :limit OFFSET :offset;
```

6. **Map sang JSON**  
   - Ứng dụng tính `isLowStock`, `isExpiringSoon`, `totalValue = quantity * costPrice` (hoặc tương đưồng DECIMAL) trước khi trả `data.items` + `data.summary` + `page`/`limit`/`total`.

### 8.2 Các ràng buộc (Constraints)

- **`Inventory`**: `chk_quantity` (`quantity >= 0`); `uq_inventory_product_location_batch` (`product_id`, `location_id`, `batch_number`).  
- **FK**: `i.product_id → Products.id`, `i.location_id → WarehouseLocations.id` (ON DELETE RESTRICT trên vị trí).  
- **`WarehouseLocations.status`**: nếu policy UC6 ẩn vị trí `Maintenance`/`Inactive` khỏi danh sách — ghi rõ trong `WHERE`; không thì vẫn hiển thị nhưng có thể cảnh báo UI.  
- **Không** trả về cột nhạy cảm không thuộc read-model (ví dụ không leak dữ liệu nội bộ khác bảng join).  
- **Trigger**: không bắt buộc trigger DB cho GET; chỉ đọc.

---

## 9. Lỗi (Error Responses)

#### 400 Bad Request (Tham số query không hợp lệ)

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Tham số truy vấn không hợp lệ",
  "details": {
    "stockLevel": "Giá trị phải là all, in_stock, low_stock hoặc out_of_stock",
    "limit": "Giá trị phải từ 1 đến 100"
  }
}
```

#### 401 Unauthorized (Thiếu hoặc hết hạn token)

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
}
```

#### 403 Forbidden (Không đủ quyền xem tồn kho)

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền xem dữ liệu tồn kho trong phạm vi này"
}
```

#### 404 Not Found

_Không áp dụng_ cho endpoint danh sách tài nguyên cố định `GET /inventory` (không có `{id}` trên path).

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

---

## 10. Zod (query — FE)

```typescript
import { z } from "zod";

export const InventoryListQuerySchema = z.object({
  search: z.string().optional(),
  stockLevel: z.enum(["all", "in_stock", "low_stock", "out_of_stock"]).optional(),
  locationId: z.coerce.number().int().positive().optional(),
  categoryId: z.coerce.number().int().positive().optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  sort: z.string().optional(),
});
```

---

## 11. Ghi chú FE

Thay `mockInventory` + `recalculateKPIs` bằng `data.items` và `data.summary` (hoặc kết hợp Task009).
