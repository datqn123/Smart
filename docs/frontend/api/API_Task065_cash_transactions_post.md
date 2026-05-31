# 📄 API SPEC: `POST /api/v1/cash-transactions` — Tạo giao dịch thu chi — Task065

> **Trạng thái**: Approved (đồng bộ SRS Task064–068 + PRD quỹ — 02/05/2026)  
> **SRS backend:** [`../../../backend/docs/srs/SRS_Task064-068_cash-transactions-api.md`](../../../backend/docs/srs/SRS_Task064-068_cash-transactions-api.md), [`../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md`](../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md)  
> **Feature**: Cashflow — **Giao dịch thu chi**  
> **Tags**: RESTful, Finance, Create

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Tạo bản ghi **`cash_transactions`** mới **luôn** `Pending`; hoàn tất / ghi sổ chỉ qua **PATCH** Task067 (SRS **OQ-2**).
- **Out of scope**: Sửa/xóa → Task067, 068.

---

## 2. Endpoint

**`POST /api/v1/cash-transactions`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) §12.1 — rule hoàn tất & `FinanceLedger`.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Authentication** | `Bearer` |
| **RBAC** | **`mp.can_view_finance === true`** (chi tiết & ngoại lệ Staff → SRS §4 **OQ-1**). Không đủ → **403** |

---

## 5. Request body (JSON, camelCase)

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `direction` | `Income` \| `Expense` | Có | |
| `amount` | number > 0 | Có | |
| `category` | string 1–500 | Có | PRD / Flyway **V41** |
| `description` | string | Không | |
| `paymentMethod` | string | Không | Mặc định `Cash` |
| `transactionDate` | date ISO | Có | |
| `fundId` | int > 0 | Có | Phải trỏ tới `cash_funds` đang hoạt động (PRD) |
| `status` | — | **Không gửi** | Server luôn lưu `Pending`. Client gửi `Completed` / `Cancelled` → **400** |

**Sinh `transaction_code`**: server-side (unique), ví dụ `PT-2026-{seq}` / `PC-2026-{seq}` theo `direction`.

---

## 6. Thành công — `201 Created`

Trả về bản ghi đầy đủ như Task066 (cùng shape `data`).

```json
{
  "success": true,
  "data": {
    "id": 13,
    "transactionCode": "PC-2026-0002",
    "direction": "Expense",
    "amount": 120000,
    "category": "Chi phí vận hành",
    "description": "Mua văn phòng phẩm",
    "paymentMethod": "Cash",
    "status": "Pending",
    "transactionDate": "2026-04-23",
    "financeLedgerId": null,
    "createdBy": 3,
    "createdByName": "Nguyễn Văn A",
    "performedBy": 3,
    "performedByName": "Nguyễn Văn A",
    "createdAt": "2026-04-23T08:00:00Z",
    "updatedAt": "2026-04-23T08:00:00Z",
    "fundId": 1,
    "fundCode": "CASH"
  },
  "message": "Đã tạo giao dịch"
}
```

---

## 7. Logic & Database

1. Validate body → **400** (gồm cả khi client gửi `status` khác `Pending` hoặc gửi `Completed`/`Cancelled`).  
2. `INSERT INTO cashtransactions (...)` gồm `fund_id`, với `created_by = current_user_id`, **`performed_by = current_user_id`**, `status = 'Pending'`, không ghi `finance_ledger`.  
3. Ghi sổ **chỉ** tại Task067 (PATCH `Completed`).

---

## 8. Lỗi

| Mã | Tình huống |
| :--- | :----------- |
| 400 | `amount <= 0`, thiếu trường bắt buộc (gồm `fundId`), `category` quá 500 ký tự, body có `status` không hợp lệ (chỉ được bỏ qua hoặc `Pending`) |
| 401 | Chưa đăng nhập |
| 403 | Không quyền |
| 409 | Trùng `transaction_code` (hiếm nếu retry race — xử lý idempotent theo policy) |
| 500 | Lỗi server |

---

## 9. Zod (body)

```typescript
import { z } from "zod";

export const CashTransactionCreateBodySchema = z.object({
  direction: z.enum(["Income", "Expense"]),
  amount: z.number().positive(),
  category: z.string().min(1).max(500),
  description: z.string().max(2000).optional(),
  paymentMethod: z.string().max(30).optional().default("Cash"),
  transactionDate: z.string().date(),
  fundId: z.number().int().positive(),
  status: z.literal("Pending").optional(),
});
```

---

## 10. Ghi chú FE

Sau khi tạo, refresh danh sách Task064; hoàn tất bằng Task067 rồi mới có dòng sổ cái Task063 (ghi `financeledger` kèm `fund_id` từ phiếu).
