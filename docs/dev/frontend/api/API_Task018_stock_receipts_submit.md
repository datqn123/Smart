# 📄 API SPEC: `POST /api/v1/stock-receipts/{id}/submit` — Gửi duyệt (Draft → Pending) - Task018

> **Trạng thái**: Draft  
> **Feature**: UC7 — nút **Gửi yêu cầu duyệt** (`ReceiptForm`); thay `submitReceiptForApproval` mock

---

## 1. Mục tiêu Task

- Chuyển phiếu từ **`Draft`** sang **`Pending`** sau khi đã nhập đủ dữ liệu hợp lệ.
- **Out of scope**: tạo phiếu mới (Task014 đã có `saveMode: pending`); phê duyệt (Task019).

---

## 2. Mục đích Endpoint

**`POST /api/v1/stock-receipts/{id}/submit`** — không body hoặc body rỗng `{}`; có thể thêm `confirm: true` tùy chọn.

**KHÔNG** cộng tồn kho.

---

## 3. Overview

| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8** |
| **Endpoint** | `/api/v1/stock-receipts/{id}/submit` |
| **Method** | `POST` |
| **Auth** | `Bearer` |
| **RBAC** | `can_manage_inventory` + **chỉ người tạo phiếu** (`staff_id` = JWT `sub`); SRS §6. |

---

## 4. Request

### 4.1 Headers — `Authorization` + `Content-Type: application/json`

### 4.2 Body — `{}` (optional)

---

## 5. Thành công — `200 OK`

`data` giống Task015 (phiếu sau khi `status: "Pending"`).

---

## 6. Logic nghiệp vụ & Database (Business Logic)

### 6.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **`SELECT id, status FROM StockReceipts WHERE id = ? FOR UPDATE`**.
3. Nếu không phải `Draft` → **409** (hoặc **400** — chốt một).
4. **`SELECT COUNT(*) FROM StockReceiptDetails WHERE receipt_id = ?`** = 0 → **400**.
5. **`UPDATE StockReceipts SET status = 'Pending', updated_at = NOW() WHERE id = ?`** — **không** gán `reviewed_at` / `reviewed_by` / `rejection_reason` (vẫn NULL cho đến Task019/020).
6. **`INSERT SystemLogs`**.
7. **`COMMIT`**.

### 6.2 Các ràng buộc (Constraints)

- CHECK `status` hợp lệ.

---

## 7. Lỗi (Error Responses)

_(Ví dụ JSON đầy đủ: tham chiếu [`API_Task013_stock_receipts_get_list.md`](API_Task013_stock_receipts_get_list.md) §9; bổ sung **409** khi không phải `Draft`.)_

---

## 8. Zod

`id` path; body `z.object({}).optional()`.
