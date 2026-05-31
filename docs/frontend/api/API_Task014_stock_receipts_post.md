# 📄 API SPEC: `POST /api/v1/stock-receipts` — Tạo phiếu nhập kho - Task014

> **Trạng thái**: Draft  
> **Feature**: Inventory / **UC7** — `ReceiptForm` (Tạo mới / logic tách **Lưu nháp** vs **Gửi yêu cầu duyệt**)  
> **Tags**: RESTful, StockReceipts, StockReceiptDetails, Transaction

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Cho phép tạo **phiếu nhập kho mới** kèm **ít nhất một dòng** chi tiết; hỗ trợ **`saveMode`** để lưu **`Draft`** hoặc gửi thẳng **`Pending`** (tương ứng hai nút trên UI).
- **Phạm vi**: **chỉ** `POST /stock-receipts` (một transaction header + details).
- **Out of scope**: sửa phiếu → Task016; gửi duyệt từ Draft đã tồn tại → Task018; phê duyệt → Task019.

---

## 2. Mục đích Endpoint

**`POST /api/v1/stock-receipts`** tạo bản ghi `StockReceipts` + các `StockReceiptDetails`, sinh **`receipt_code`** (PN-YYYY-NNNN), gán **`staff_id`** từ JWT, tính **`total_amount`** từ tổng dòng (khớp CHECK tổng ≥ 0).

**Endpoint này KHÔNG:**

- Không phê duyệt / không cộng `Inventory` / không ghi `FinanceLedger` — chỉ khi **Task019** sau này.
- Không thay `PATCH` cập nhật phiếu đã tồn tại.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8**.  
DB §17, §18; validation HSD vs ngày nhập giống `ReceiptForm` + `isExpiryValid`.

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8** |
| **Endpoint** | `/api/v1/stock-receipts` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Staff / Owner (UC7) |
| **Use Case Ref** | UC7 |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

### 5.2 Query parameters

_Không có_

### 5.3 Request body

```json
{
  "supplierId": 1,
  "receiptDate": "2026-04-23",
  "invoiceNumber": "HD-2026-01",
  "notes": "Ghi chú phiếu",
  "saveMode": "draft",
  "details": [
    {
      "productId": 12,
      "unitId": 5,
      "quantity": 24,
      "costPrice": 45000,
      "batchNumber": "LOT-2026-01",
      "expiryDate": "2027-12-31"
    }
  ]
}
```

| Field | Kiểu | Bắt buộc | Mô tả |
| :---- | :--- | :------- | :---- |
| `supplierId` | number | Có | FK `Suppliers.id` |
| `receiptDate` | string (YYYY-MM-DD) | Có | `receipt_date` |
| `invoiceNumber` | string | Không | max 100 |
| `notes` | string | Không | |
| `saveMode` | string | Có | `draft` → `status='Draft'`; `pending` → `status='Pending'` |
| `details` | array | Có | min 1 phần tử |
| `details[].productId` | number | Có | FK `Products.id` |
| `details[].unitId` | number | Có | FK `ProductUnits.id` (phải thuộc `product_id`) |
| `details[].quantity` | number | Có | > 0 |
| `details[].costPrice` | number | Có | ≥ 0 |
| `details[].batchNumber` | string \| null | Không | UNIQUE per receipt + product |
| `details[].expiryDate` | string \| null | Không | nếu có: ≥ `receiptDate` |

---

## 6. Thành công — `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 42,
    "receiptCode": "PN-2026-0042",
    "supplierId": 1,
    "supplierName": "Công ty TNHH Vinamilk",
    "staffId": 5,
    "staffName": "Nguyễn Văn A",
    "receiptDate": "2026-04-23",
    "status": "Draft",
    "invoiceNumber": "HD-2026-01",
    "totalAmount": 1080000,
    "notes": "Ghi chú phiếu",
    "approvedBy": null,
    "approvedByName": null,
    "approvedAt": null,
    "reviewedBy": null,
    "reviewedByName": null,
    "reviewedAt": null,
    "rejectionReason": null,
    "createdAt": "2026-04-23T10:00:00Z",
    "updatedAt": "2026-04-23T10:00:00Z",
    "details": [
      {
        "id": 1001,
        "receiptId": 42,
        "productId": 12,
        "productName": "Nước suối 500ml",
        "skuCode": "SKU-WAT-500",
        "unitId": 5,
        "unitName": "Chai",
        "quantity": 24,
        "costPrice": 45000,
        "batchNumber": "LOT-2026-01",
        "expiryDate": "2027-12-31",
        "lineTotal": 1080000
      }
    ]
  },
  "message": "Đã tạo phiếu nhập kho"
}
```

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → `staff_id` = `user_id` từ token. **401** / **403**.
2. **Validate body** + expiry ≥ receiptDate → **400**.
3. **`SELECT id FROM Suppliers WHERE id = ?`** — không có → **400**.
4. **Mỗi dòng**: kiểm `Products.status = 'Active'`; `ProductUnits` thuộc `product_id`; → **400** nếu sai.
5. **`BEGIN`**.
6. **Sinh `receipt_code`** duy nhất (transaction-safe: lock sequence hoặc `INSERT … ON CONFLICT` / bảng counter theo năm).
7. **`INSERT INTO StockReceipts`** các cột: `receipt_code`, `supplier_id`, `staff_id`, `receipt_date`, `status`, `invoice_number`, `total_amount` (tổng dòng sau khi quy đổi nếu có policy), `notes`, `created_at`, `updated_at` — các cột **`approved_by`**, **`approved_at`**, **`reviewed_by`**, **`reviewed_at`**, **`rejection_reason`** để **NULL** (mặc định DB sau migration §17).
8. **`INSERT INTO StockReceiptDetails`** từng dòng: `receipt_id`, `product_id`, `unit_id`, `quantity`, `cost_price`, `batch_number`, `expiry_date` — **không** ghi `line_total` (generated).
9. **`INSERT SystemLogs`** (INFO, `INVENTORY`, `STOCK_RECEIPT_CREATE`, …).
10. **`COMMIT`**; trả `201` + payload đọc lại bằng join (supplier, staff, product, unit names).

### 7.2 Các ràng buộc (Constraints)

- `uq_srd_receipt_product_batch`, FK receipt/product/unit.  
- `total_amount` khớp tổng `line_total` logic ứng dụng (so với generated rows).  
- **Không** trả `password_hash`.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": {
    "saveMode": "Giá trị phải là draft hoặc pending",
    "details[0].expiryDate": "Hạn sử dụng không được nhỏ hơn ngày nhập kho"
  }
}
```

#### 401 Unauthorized

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
}
```

#### 403 Forbidden

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền tạo phiếu nhập kho"
}
```

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

#### 409 Conflict

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Trùng mã phiếu hoặc trùng lô trong cùng phiếu, vui lòng thử lại"
}
```

---

## 9. Zod (body — FE)

```typescript
import { z } from "zod";

const DetailSchema = z.object({
  productId: z.number().int().positive(),
  unitId: z.number().int().positive(),
  quantity: z.number().positive(),
  costPrice: z.number().nonnegative(),
  batchNumber: z.string().max(100).nullable().optional(),
  expiryDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable().optional(),
});

export const StockReceiptCreateSchema = z.object({
  supplierId: z.number().int().positive(),
  receiptDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  invoiceNumber: z.string().max(100).optional(),
  notes: z.string().optional(),
  saveMode: z.enum(["draft", "pending"]),
  details: z.array(DetailSchema).min(1),
});
```
