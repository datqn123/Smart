# 📄 API SPEC: `PATCH /api/v1/debts/{id}` — Cập nhật / trả nợ — Task072

> **Trạng thái**: Approved  
> **Feature**: Cashflow — **Sổ nợ**

---

## 1. Mục tiêu

- Cập nhật `dueDate`, `notes`, `totalAmount` (khi chưa thanh toán nhiều — theo policy).  
- **Ghi nhận trả nợ**: tăng `paidAmount` (hoặc gửi `paymentAmount` cộng dồn server-side).  
- Tự cập nhật **`status = Cleared`** khi `paidAmount >= totalAmount`.

**Out of scope (backlog)**: Đồng bộ `INSERT finance_ledger` khi trả nợ — ghi trong policy riêng nếu BA yêu cầu.

---

## 2. Endpoint

**`PATCH /api/v1/debts/{id}`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) §12.2 — `chk_paid_le_total`.  
**SRS (BE):** [`../../../backend/docs/srs/SRS_Task069-072_debts-api.md`](../../../backend/docs/srs/SRS_Task069-072_debts-api.md) — **Approved** 30/04/2026; **§4** — Cleared + tiền → **409**; `paymentAmount` → **cắt trần**; PATCH chỉ **người tạo** (`created_by`).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Authentication** | `Bearer` |
| **RBAC** | **`mp.can_view_finance === true`** và **`created_by`** bản ghi **= JWT `sub`**. Không phải người tạo → **403**. |

---

## 5. Request body (partial)

| Trường | Kiểu | Mô tả |
| :----- | :--- | :---- |
| `totalAmount` | number ≥ 0 | Optional; không giảm dưới `paidAmount` hiện tại |
| `paidAmount` | number ≥ 0 | Set tuyệt đối **hoặc** dùng `paymentAmount` (xem dưới) |
| `paymentAmount` | number > 0 | Cộng vào `paidAmount` hiện có (mutually exclusive với set trực tiếp `paidAmount` — chọn một chuẩn trong BE) |
| `dueDate` | date \| null | |
| `notes` | string \| null | |

**UI “Trả một phần”**: `paymentAmount` — server (**SRS OQ-4**):  
`newPaid = LEAST(paid_amount + paymentAmount, total_amount)` (**cắt trần**, không **400** khi vượt số còn lại).

**Khoản `status = Cleared` (SRS OQ-1):** nếu body có **`totalAmount`**, **`paidAmount`** hoặc **`paymentAmount`** → **409**. Vẫn cho PATCH **`notes`** / **`dueDate`**.

---

## 6. `200 OK`

Trả về bản ghi đầy đủ sau cập nhật (shape Task071).

---

## 7. Logic & Database

1. Kiểm tra **`can_view_finance`** và **`created_by = sub`** → **403** nếu không.  
2. `SELECT … FOR UPDATE` từ **`partnerdebts`** (có **`created_by`** sau V26).  
3. Nếu **`status = Cleared`** và body chứa bất kỳ **`totalAmount` / `paidAmount` / `paymentAmount`** → **409** (không `UPDATE` tiền).  
4. Ngược lại: tính `newPaid` (cắt trần **LEAST** nếu có `paymentAmount`); validate **`newPaid ≤ total`** và **`totalAmount` ≥ `paid`** → **400** nếu vi phạm.  
5. `UPDATE partnerdebts SET …` (trigger **`trg_partnerdebts_updated`** trên `PartnerDebts` hoặc set `updated_at` explicit).  
6. Nếu `newPaid >= total_amount` → `status = Cleared`, else `InDebt`.

---

## 8. Lỗi

| Mã | Tình huống |
| :--- | :----------- |
| 400 | Validation; `totalAmount` < `paidAmount` |
| 401 | |
| 403 | Thiếu `can_view_finance` hoặc **không** phải người tạo (`created_by`) |
| 404 | Không tìm thấy `id` |
| 409 | **Cleared** và body có trường số tiền (`totalAmount` / `paidAmount` / `paymentAmount`) |
| 500 | |

---

## 9. Zod

```typescript
import { z } from "zod";

export const DebtPatchBodySchema = z
  .object({
    totalAmount: z.number().min(0).optional(),
    paidAmount: z.number().min(0).optional(),
    paymentAmount: z.number().positive().optional(),
    dueDate: z.string().date().optional().nullable(),
    notes: z.string().max(5000).optional().nullable(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" })
  .refine((o) => !(o.paidAmount != null && o.paymentAmount != null), {
    message: "Chỉ dùng paidAmount hoặc paymentAmount, không dùng cả hai",
  });
```

---

## 10. Ghi chú FE

Nút “Ghi nhận thanh toán” → `PATCH` với `{ "paymentAmount": value }`; hiển thị `remainingAmount` từ response.
