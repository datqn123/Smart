# 📄 API SPEC: `DELETE /api/v1/suppliers/{id}` — Xóa nhà cung cấp - Task046

> **Trạng thái**: Draft  
> **Feature**: UC8 — `SuppliersPage` / `ConfirmDialog` xóa một NCC  
> **Tags**: RESTful, Suppliers, Delete

---

## 1. Mục tiêu Task

- Xóa NCC khi **không còn** phiếu nhập liên quan — khớp quy tắc DB §3: **RESTRICT** từ `StockReceipts`.

---

## 2. Endpoint

**`DELETE /api/v1/suppliers/{id}`**

---

## 3. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/suppliers/{id}` |
| **Method** | `DELETE` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner (khuyến nghị) |
| **Use Case Ref** | UC8 |

---

## 4. Thành công — `200 OK`

```json
{
  "success": true,
  "data": { "id": 3, "deleted": true },
  "message": "Đã xóa nhà cung cấp"
}
```

---

## 5. Logic DB

1. **`SELECT id FROM Suppliers WHERE id = ? FOR UPDATE`** → không có → **404**.
2. **`SELECT 1 FROM StockReceipts WHERE supplier_id = ? LIMIT 1`** → có → **409** (`details.reason`: `HAS_RECEIPTS`) — message tiếng Việt theo envelope.
3. **`SELECT 1 FROM PartnerDebts WHERE supplier_id = ? LIMIT 1`** → có → **409** (`details.reason`: `HAS_PARTNER_DEBTS`) — Flyway V1: FK `partnerdebts.supplier_id` **ON DELETE RESTRICT** (đồng bộ SRS / schema; tránh **500** nếu chỉ kiểm phiếu nhập).
4. **`DELETE FROM Suppliers WHERE id = ?`**.

---

## 6. Lỗi

#### 409 Conflict — còn phiếu nhập

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa nhà cung cấp đã có phiếu nhập kho",
  "details": { "reason": "HAS_RECEIPTS" }
}
```

#### 409 Conflict — còn công nợ đối tác (`PartnerDebts`)

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa nhà cung cấp đang có công nợ",
  "details": { "reason": "HAS_PARTNER_DEBTS" }
}
```

**404** / **401** / **403** / **500**.

---

## 7. Zod (params)

```typescript
import { z } from "zod";
export const SupplierIdParamsSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
