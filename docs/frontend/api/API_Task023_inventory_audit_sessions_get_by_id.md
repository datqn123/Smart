# 📄 API SPEC: `GET /api/v1/inventory/audit-sessions/{id}` — Chi tiết đợt kiểm kê - Task023

> **Trạng thái**: Draft  
> **Feature**: UC6 — `AuditSessionsTable` mở panel / xem chi tiết dòng

---

## 1. Mục tiêu Task

- Trả **một** session + **`items[]`** khớp `AuditItem` FE (join `Inventory`, `Products`, `WarehouseLocations`, `ProductUnits`).

---

## 2. Mục đích Endpoint

**`GET /api/v1/inventory/audit-sessions/{id}`** — read-only.

---

## 3. Thông tin chung (Overview)

| **Endpoint** | `/api/v1/inventory/audit-sessions/{id}` |
| **Method** | `GET` |
| **Auth** | `Bearer` |
| **API Design Ref** | §4.15 |

---

## 5. Request — path `id`; không body.

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "auditCode": "KK-2026-0001",
    "title": "Kiểm kê cuối tháng 3",
    "auditDate": "2026-03-31",
    "status": "Completed",
    "locationFilter": "WH01",
    "categoryFilter": null,
    "notes": "Kiểm kê toàn bộ kho chính",
    "createdBy": 2,
    "createdByName": "Nguyễn Văn A",
    "completedAt": "2026-04-01T16:00:00Z",
    "completedByName": "Trần Quản Lý",
    "createdAt": "2026-03-31T08:00:00Z",
    "updatedAt": "2026-04-01T16:00:00Z",
    "items": [
      {
        "id": 1,
        "auditSessionId": 1,
        "inventoryId": 101,
        "productId": 1,
        "productName": "Sữa Ông Thọ Hộp Giấy",
        "skuCode": "SP001",
        "unitName": "Hộp",
        "locationId": 1,
        "warehouseCode": "WH01",
        "shelfCode": "A1",
        "batchNumber": "B2026001",
        "systemQuantity": 150,
        "actualQuantity": 148,
        "variance": -2,
        "variancePercent": -1.33,
        "isCounted": true,
        "notes": "Thiếu 2 hộp"
      }
    ]
  },
  "message": "Thành công"
}
```

**Quy ước**: `variance` / `variancePercent` tính ở API khi `actualQuantity` có giá trị; nếu chưa đếm — `actualQuantity` null, `variance` 0, `isCounted` false.

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **`SELECT s.*, … FROM inventory_audit_sessions s`** join users. **`WHERE s.id = ?`** + RBAC — không có → **404**.
3. **`SELECT l.id, l.session_id, l.inventory_id, i.product_id, p.name, p.sku_code, …, l.system_quantity, l.actual_quantity, l.is_counted, l.notes`** từ `inventory_audit_lines l` join `inventory i` join `products p` join `warehouse_locations wl` join `product_units pu` (đơn vị hiển thị — **chốt**: đơn vị cơ sở) **`WHERE l.session_id = ?`**.

### 7.2 Các ràng buộc (Constraints)

- Không `SELECT *`.

---

## 8. Lỗi

_(401 / 403 / 404 / 500 — ví dụ như [`API_Task015_stock_receipts_get_by_id.md`](API_Task015_stock_receipts_get_by_id.md) §8.)_

---

## 9. Zod

`id` path int positive.
