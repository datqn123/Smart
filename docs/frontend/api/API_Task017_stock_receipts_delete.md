# 📄 API SPEC: `DELETE /api/v1/stock-receipts/{id}` — Xóa phiếu nhập - Task017

> **Trạng thái**: Draft  
> **Feature**: UC7 — nút xóa trên `ReceiptTable` (mock chỉ cho phép `Draft`)

---

## 1. Mục tiêu Task

- Xóa phiếu nhập **chỉ khi** trạng thái cho phép (mặc định: **`Draft`**; có thể mở **`Pending`** nếu PM cho phép hủy yêu cầu — ghi rõ trong triển khai).

- **Out of scope**: `Approved`/`Rejected` — **409** (business rule DB §17).

---

## 2. Mục đích Endpoint

**`DELETE /api/v1/stock-receipts/{id}`** — CASCADE xóa `StockReceiptDetails` theo FK.

---

## 3. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8** |
| **Endpoint** | `/api/v1/stock-receipts/{id}` |
| **Method** | `DELETE` |
| **Authentication** | `Bearer` |
| **RBAC** | `hasAuthority('can_manage_inventory')` + **chỉ Owner** (`JWT claim role` = Owner, không phân biệt hoa thường) mới xóa được phiếu **Draft** hoặc **Pending** — SRS §6. |
| **Use Case Ref** | UC7 |

---

## 4. Request — không body; path `id`.

---

## 5. Thành công — `200 OK` hoặc `204 No Content`

```json
{
  "success": true,
  "data": { "id": 42, "deleted": true },
  "message": "Đã xóa phiếu nhập kho"
}
```

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **`SELECT id, status FROM StockReceipts WHERE id = ? FOR UPDATE`**.
3. `status` không cho xóa → **409**.
4. **`DELETE FROM StockReceipts WHERE id = ?`** (CASCADE details).
5. **`INSERT SystemLogs`**.

### 7.2 Các ràng buộc (Constraints)

- Nếu sau này có FK khác trỏ tới receipt — RESTRICT có thể chặn xóa → **409** với message phù hợp.  
- Xóa header xóa luôn các cột audit **`reviewed_*` / `rejection_reason`** theo bản ghi (CASCADE theo `id`).

---

## 8. Lỗi (Error Responses)

#### 404 Not Found

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy phiếu nhập kho yêu cầu"
}
```

#### 409 Conflict

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Chỉ được xóa phiếu ở trạng thái Nháp"
}
```

#### 403 Forbidden — không phải Owner

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Chỉ tài khoản Owner mới được xóa phiếu (Nháp/Chờ duyệt), phê duyệt hoặc từ chối phiếu Chờ duyệt"
}
```

#### 401 / 403 / 500

_(Giống [`API_Task013_stock_receipts_get_list.md`](API_Task013_stock_receipts_get_list.md) §9.)_

---

## 9. Zod

`id` path int positive.
