# 📄 API SPEC: `POST /api/v1/debts` — Tạo khoản nợ — Task070

> **Trạng thái**: Approved  
> **Feature**: Cashflow — **Sổ nợ**

---

## 1. Mục tiêu

Tạo bản ghi trong **`partnerdebts`** (Flyway `PartnerDebts`) — công nợ phải thu hoặc phải trả theo KH/NCC.

---

## 2. Endpoint

**`POST /api/v1/debts`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) §12.2 — constraint `chk_partner_debts_partner`.  
**SRS (BE):** [`../../../backend/docs/srs/SRS_Task069-072_debts-api.md`](../../../backend/docs/srs/SRS_Task069-072_debts-api.md) — **Approved** 30/04/2026; **POST** yêu cầu **`can_view_finance`**; **`created_by = sub`** khi INSERT (cột thêm qua Flyway **V26** — SRS **§4 OQ-2**).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Authentication** | `Bearer` |
| **RBAC** | **`mp.can_view_finance === true`**. Thiếu → **403**. Server gán **`created_by`** = user hiện tại (JWT `sub`) — **SRS §4 OQ-2**. |

---

## 5. Request body

| Trường | Kiểu | Bắt buộc | Mô tả |
| :----- | :--- | :------- | :---- |
| `partnerType` | `Customer` \| `Supplier` | Có | |
| `customerId` | int | Điều kiện | Bắt buộc nếu `partnerType = Customer` |
| `supplierId` | int | Điều kiện | Bắt buộc nếu `partnerType = Supplier` |
| `totalAmount` | number ≥ 0 | Có | |
| `paidAmount` | number ≥ 0 | Không | Mặc định `0`; phải `<= totalAmount` |
| `dueDate` | date | Không | |
| `notes` | string | Không | |

Server sinh **`debtCode`** (unique), ví dụ `NO-2026-{seq}` — trong **một transaction**, seq theo **`MAX`** cùng năm (**SRS §4 OQ-3**).  
**`status`**: tự set `InDebt` nếu `paidAmount < totalAmount`, ngược lại `Cleared`.

---

## 6. `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 6,
    "debtCode": "NO-2026-0004",
    "partnerType": "Supplier",
    "customerId": null,
    "supplierId": 3,
    "partnerName": "NCC XYZ",
    "totalAmount": 5000000,
    "paidAmount": 0,
    "remainingAmount": 5000000,
    "dueDate": "2026-04-30",
    "status": "InDebt",
    "notes": null,
    "createdAt": "2026-04-23T09:00:00Z",
    "updatedAt": "2026-04-23T09:00:00Z"
  },
  "message": "Đã tạo khoản nợ"
}
```

---

## 7. Database

`INSERT INTO partnerdebts (..., created_by, ...)` — validate FK `customer_id` / `supplier_id` tồn tại và khớp `partner_type` → **400** nếu không. Cột **`created_by`** bắt buộc sau migration **V26** (xem SRS **§10**).

---

## 8. Lỗi

| Mã | Tình huống |
| :--- | :----------- |
| 400 | Thiếu `customerId`/`supplierId` đúng cặp với `partnerType`; `paidAmount > totalAmount` |
| 401 | |
| 403 | Thiếu `can_view_finance` |
| 500 | |

---

## 9. Zod

```typescript
import { z } from "zod";

export const DebtCreateBodySchema = z
  .object({
    partnerType: z.enum(["Customer", "Supplier"]),
    customerId: z.number().int().positive().optional(),
    supplierId: z.number().int().positive().optional(),
    totalAmount: z.number().min(0),
    paidAmount: z.number().min(0).optional().default(0),
    dueDate: z.string().date().optional().nullable(),
    notes: z.string().max(5000).optional().nullable(),
  })
  .superRefine((val, ctx) => {
    if (val.partnerType === "Customer" && !val.customerId) {
      ctx.addIssue({ code: "custom", message: "customerId là bắt buộc" });
    }
    if (val.partnerType === "Supplier" && !val.supplierId) {
      ctx.addIssue({ code: "custom", message: "supplierId là bắt buộc" });
    }
    if (val.paidAmount > val.totalAmount) {
      ctx.addIssue({ code: "custom", message: "paidAmount không được vượt totalAmount" });
    }
  });
```

---

## 10. Ghi chú FE

Sau POST, điều hướng hoặc refresh Task069.
