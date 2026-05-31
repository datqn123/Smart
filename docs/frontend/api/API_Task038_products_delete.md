# 📄 API SPEC: `DELETE /api/v1/products/{id}` — Xóa sản phẩm - Task038

> **Trạng thái**: Draft  
> **Feature**: UC8 — xóa một / bulk (lần lượt) trên `ProductsPage`  
> **Tags**: RESTful, Products, Delete

---

## 1. Mục tiêu Task

- Xóa sản phẩm khi **không còn ràng buộc RESTRICT** từ nghiệp vụ (phiếu nhập chi tiết, dòng đơn hàng, …).  
- **`Inventory`**: theo DB §7 quan hệ `ON DELETE CASCADE` — xóa SP sẽ xóa tồn; cần **cảnh báo nghiệp vụ**: khuyến nghị **chỉ Owner** hoặc **409** nếu còn bất kỳ tồn > 0 (policy an toàn).

---

## 2. Endpoint

**`DELETE /api/v1/products/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.9** |
| **Endpoint** | `/api/v1/products/{id}` |
| **Method** | `DELETE` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner (khuyến nghị) |
| **Use Case Ref** | UC8 |

---

## 4. Thành công — `200 OK`

```json
{
  "success": true,
  "data": { "id": 12, "deleted": true },
  "message": "Đã xóa sản phẩm"
}
```

---

## 5. Logic DB (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **`SELECT id FROM Products WHERE id = ? FOR UPDATE`** → **404**.
3. **`SELECT 1 FROM StockReceiptDetails WHERE product_id = ? LIMIT 1`** (khi đã có bảng phiếu nhập) → **409** "Đã có trong phiếu nhập".
4. **`SELECT 1 FROM OrderDetails WHERE product_id = ? LIMIT 1`** → **409** "Đã có trong đơn hàng".
5. (Policy an toàn) **`SELECT SUM(quantity) FROM Inventory WHERE product_id = ?`** > 0 → **409** "Còn tồn kho".
6. **`DELETE FROM Products WHERE id = ?`** — CASCADE `ProductUnits`, `ProductPriceHistory`, `Inventory` theo schema hiện tại.

---

## 6. Lỗi

#### 409 Conflict

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa sản phẩm đã xuất hiện trên phiếu nhập hoặc đơn hàng"
}
```

#### 404 / 401 / 403 / 500

Theo chuẩn dự án.

---

## 7. Ghi chú

Nếu team quyết định **soft delete** (`status` chỉ `Inactive` + ẩn khỏi list): đổi Task này thành policy **PATCH** thay vì `DELETE`.
