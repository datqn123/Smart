# 📄 API SPEC: `PATCH /api/v1/stock-receipts/{id}` — Sửa phiếu nhập (Draft) - Task016

> **Trạng thái**: Draft  
> **Feature**: UC7 — `ReceiptForm` khi `receipt.status === 'Draft'`

---

## 1. Mục tiêu Task

- Cập nhật **partial** header + **thay thế toàn bộ** danh sách `details` (khuyến nghị đơn giản) hoặc **diff** từng dòng — mặc định spec: **replace all details** trong một transaction khi gửi body có `details`.

- **Out of scope**: `Pending`/`Approved` — **409**; gửi duyệt → Task018; tạo mới → Task014.

---

## 2. Mục đích Endpoint

**`PATCH /api/v1/stock-receipts/{id}`** chỉ khi **`status = 'Draft'`**.

---

## 3. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8** |
| **Endpoint** | `/api/v1/stock-receipts/{id}` |
| **Method** | `PATCH` |
| **Authentication** | `Bearer` |
| **RBAC** | `can_manage_inventory` + **chỉ người tạo phiếu** (`stockreceipts.staff_id` = JWT `sub`); SRS §6. |
| **Use Case Ref** | UC7 |

---

## 4. Đặc tả Request (Request Specification)

### 4.1 Headers

```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

### 4.2 Path — `id` (StockReceipts.id)

### 4.3 Query — _Không có_

### 4.4 Request body (partial)

```json
{
  "supplierId": 2,
  "receiptDate": "2026-04-24",
  "invoiceNumber": "",
  "notes": "Cập nhật",
  "details": [
    {
      "productId": 12,
      "unitId": 5,
      "quantity": 10,
      "costPrice": 46000,
      "batchNumber": "LOT-2026-02",
      "expiryDate": "2028-01-01"
    }
  ]
}
```

Ít nhất một field hoặc `details` phải có mặt. Nếu có `details`: **xóa** `StockReceiptDetails` cũ của `receipt_id` rồi insert lại (trong transaction) hoặc diff có kiểm soát.

---

## 5. Thành công — `200 OK`

Trả về cùng shape **`data`** như [`API_Task015_stock_receipts_get_by_id.md`](API_Task015_stock_receipts_get_by_id.md) §6.

---

## 6. Logic nghiệp vụ & Database (Business Logic)

### 6.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **`SELECT id, status FROM StockReceipts WHERE id = ? FOR UPDATE`** — không có → **404**; `status <> 'Draft'` → **409**.
3. Validate body giống Task014 (trừ `saveMode`).
4. **`BEGIN`** (nếu chưa FOR UPDATE).
5. **`UPDATE StockReceipts SET …, updated_at = NOW()`** chỉ các cột gửi; **tính lại `total_amount`**.
6. Nếu có `details`: **`DELETE FROM StockReceiptDetails WHERE receipt_id = ?`** rồi **`INSERT`** lại từng dòng.
7. **`INSERT SystemLogs`** (meta update).
8. **`COMMIT`**.

### 6.2 Các ràng buộc (Constraints)

- Giữ `uq_srd_receipt_product_batch`; FK.  
- **`PATCH` không được** sửa các cột quyết định duyệt: `approved_by`, `approved_at`, `reviewed_by`, `reviewed_at`, `rejection_reason` — chỉ thay đổi qua Task019/020 (kể cả khi mở rộng body PATCH sau này, phải **400** nếu client gửi các key này).

---

## 7. Lỗi (Error Responses)

- **400** validation; **401**; **403**; **404**; **409** (không phải Draft); **500**.

Ví dụ **409**:

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Chỉ được sửa phiếu ở trạng thái Nháp"
}
```

---

## 8. Zod

Giống Task014 (bỏ `saveMode`, thêm `details` optional nếu partial không gửi details — hoặc bắt buộc `details` khi đổi dòng; chốt triển khai: **khi đổi dòng phải gửi full `details`**).
