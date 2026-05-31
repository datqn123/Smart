# SRS — Đơn bán hàng (UC9) — danh sách, CRUD, hủy, POS tìm hàng, checkout bán lẻ — Task054–Task060

> **File (Spring / `smart-erp`):** `backend/docs/srs/SRS_Task054-060_sales-orders-pos-and-retail-checkout.md`  
> **Người soạn:** Agent BA (+ SQL theo `backend/AGENTS/BA_AGENT_INSTRUCTIONS.md`, `backend/AGENTS/SQL_AGENT_INSTRUCTIONS.md`)  
> **Ngày:** 27/04/2026  
> **Trạng thái:** `Approved`  
> **PO duyệt (khi Approved):** `PO (chốt câu hỏi mục §4 — yêu cầu 27/04/2026)`, `27/04/2026`

---

## 0. Đầu vào & traceability

| Nguồn | Đường dẫn / ghi chú |
| :--- | :--- |
| API Task054 | [`../../../frontend/docs/api/API_Task054_sales_orders_get_list.md`](../../../frontend/docs/api/API_Task054_sales_orders_get_list.md) |
| API Task055 | [`../../../frontend/docs/api/API_Task055_sales_orders_get_by_id.md`](../../../frontend/docs/api/API_Task055_sales_orders_get_by_id.md) |
| API Task056 | [`../../../frontend/docs/api/API_Task056_sales_orders_post.md`](../../../frontend/docs/api/API_Task056_sales_orders_post.md) |
| API Task057 | [`../../../frontend/docs/api/API_Task057_sales_orders_patch.md`](../../../frontend/docs/api/API_Task057_sales_orders_patch.md) |
| API Task058 | [`../../../frontend/docs/api/API_Task058_sales_orders_cancel.md`](../../../frontend/docs/api/API_Task058_sales_orders_cancel.md) |
| API Task059 | [`../../../frontend/docs/api/API_Task059_pos_products_get_search.md`](../../../frontend/docs/api/API_Task059_pos_products_get_search.md) |
| API Task060 | [`../../../frontend/docs/api/API_Task060_sales_orders_retail_checkout.md`](../../../frontend/docs/api/API_Task060_sales_orders_retail_checkout.md) |
| PM / UI (không tác động BE) | [`../../../frontend/AGENT_TRIGGERS/PM_FIX_Task025_04_standardization.md`](../../../frontend/AGENT_TRIGGERS/PM_FIX_Task025_04_standardization.md) — chuẩn hóa bảng Inbound/Dispatch; **§3.2** dưới đây |
| Khung API | [`../../../frontend/docs/api/API_PROJECT_DESIGN.md`](../../../frontend/docs/api/API_PROJECT_DESIGN.md) §4.10 |
| Envelope | [`../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) |
| UC / DB (tham chiếu) | [`../../../frontend/docs/UC/Database_Specification.md`](../../../frontend/docs/UC/Database_Specification.md) §19–20 |
| Flyway thực tế | [`../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql) — `SalesOrders`, `OrderDetails`, `Customers`, `StockDispatches`, `Roles` seed |
| UI index | [`../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md) |

### 0.1 Đồng bộ (API markdown ↔ Flyway) — quyết định kỹ thuật trong phiên này

| Điểm | Trong API / ghi chú cũ | Cách xử lý trong SRS dự án `smart-erp` |
| :--- | :--- | :--- |
| Cột `order_channel`, `payment_status`, `ref_sales_order_id` | `API_Task054` §2 gợi ý `ALTER TABLE` vì “chưa có” | **đã có** trong **Flyway V1** (`SalesOrders`); Dev **không** lặp migration DDL từ §2 file Task054 — coi mục đó là lịch sử thiết kế; triển khai BE bám V1. |
| Ví dụ SQL dùng alias `sales_orders`, `order_details` | Một số spec viết kiểu snake | Object trong PG từ `CREATE TABLE SalesOrders` (không quote) ánh xạ tên thực tế theo convention (thường `salesorders`). Dev dùng **tên bảng/cột đúng ánh xạ** JPA/native; SRS §10 ghi tên cột từ Flyway. |
| Khách walk-in / `WALKIN` | Task060 yêu cầu bản ghi `Customers` seed | **Đã chốt (OQ-1a):** migration/seed bổ sung: `WALKIN`, tên *Khách lẻ*, phone dự phòng **0900000000**, `status=Active` (§4.1, §10.2). |
| Voucher (OQ-3) | v1 từng mô tả cấu hình/hard-code | **Đã chốt (OQ-3):** bảng **`Vouchers`** trong DB + join/lookup tại checkout; cần **migration mới** (Vn) — xem **§3.1**, **§10.1**. |
| `shiftReference` (OQ-4) | Prefix trong `notes` | **Đã chốt (OQ-4b):** cột mới trên `SalesOrders` lưu chuỗi tham chiếu ca (VD `pos_shift_ref`) — **không** bắt buộc ghép prefix `[CA:…]` vào `notes` nếu đã có cột. |
| PM `Task025_04` (chuẩn bảng) | Trigger PM | **Không** conflict API: chỉ thay đổi FE table layout / `RULES_UI_TABLE`; **out-of-scope** backend Task054–060. |

---

## 1. Tóm tắt điều hành

- **Vấn đề:** UC9 cần bộ API đọc/ghi đơn bán theo kênh (`Wholesale` / `Retail` / `Return`), tìm hàng cho màn POS, checkout bán lẻ một lần (kèm walk-in, giảm giá/voucher, thanh toán), hủy đơn có ghi danh tính.
- **Mục tiêu nghiệp vụ:** Một hợp đồng HTTP thống nhất envelope, RBAC `can_manage_orders` (kèm `401`/`403`), toàn vẹn giao dịch khi tạo/cập nhật/hủy/retail checkout.
- **Đối tượng:** User đăng nhập (Owner / Staff / Admin tùy seed), client Mini-ERP.

### 1.1 Giao diện Mini-ERP

> Nhãn menu theo [`Sidebar.tsx`](../../../frontend/mini-erp/src/components/shared/layout/Sidebar.tsx) → nhóm “Đơn hàng”.

| Nhãn menu (Sidebar) | Route | Page (export) | Component / vùng chính | File (dưới `frontend/mini-erp/src/features/`) |
| :--- | :--- | :--- | :--- | :--- |
| Đơn bán sỉ | `/orders/wholesale` | `WholesalePage` | `OrderTable`, `OrderToolbar`, `OrderFormDialog`, `OrderDetailDialog` | `orders/pages/WholesalePage.tsx` + `orders/components/*` |
| Đơn trả hàng | `/orders/returns` | `ReturnsPage` | `ReturnFormDialog`, `OrderTable` | `orders/pages/ReturnsPage.tsx` |
| Đơn bán lẻ (POS) | `/orders/retail` | `RetailPage` | `POSProductSelector`, `POSCartPanel` (`handleCheckout` → Task060) | `orders/pages/RetailPage.tsx` |
| (Lịch sử / theo dõi chung) | Tùy UX | *cùng `OrderTable`* | Có thể dùng `GET /sales-orders` lọc `orderChannel` | Khớp `FEATURES_UI_INDEX` §orders |

---

## 2. Bóc tách nghiệp vụ (capabilities)

| # | Capability | Kích hoạt bởi | Kết quả mong đợi | Ghi chú |
| :---: | :--- | :--- | :--- | :--- |
| C1 | Danh sách phân trang + lọc | `GET /api/v1/sales-orders` | `200` + `items`, `page`, `limit`, `total` + read-model | `orderChannel`, `search`, `status`, `paymentStatus` |
| C2 | Chi tiết + dòng | `GET /api/v1/sales-orders/{id}` | `200` + header + `lines` | `404` nếu không có; mapping `refSalesOrderId` |
| C3 | Tạo đơn sỉ / trả | `POST /api/v1/sales-orders` | `201` + body như Task055 | `orderChannel` ∈ {`Wholesale`,`Return`} — **không** tạo `Retail` từ endpoint này (→ Task060) |
| C4 | PATCH meta header | `PATCH /api/v1/sales-orders/{id}` | `200` | `Cancelled` → **409** (dùng C6); `SELECT FOR UPDATE` |
| C5 | Hủy đơn | `POST /api/v1/sales-orders/{id}/cancel` | `200` + `cancelledAt`/`cancelledBy` | **OQ-6:** 409 nếu đã xuất/đã giao từ kho; **OQ-5:** hủy lặp → **200** idempotent |
| C6 | Tìm hàng POS | `GET /api/v1/pos/products` | `200` + `items` | **OQ-7a:** `availableQty` tổng hợp từ tồn, quy đổi theo `ProductUnits` khi cần |
| C7 | Checkout bán lẻ | `POST /api/v1/sales-orders/retail/checkout` | `201` | **OQ-1** walk-in, **OQ-2** trạng thái mặc định = **Delivered**, voucher từ bảng **Vouchers (OQ-3)**, ca → cột `pos_shift_ref` **(OQ-4b)**; tồn/phiếu xuất tự động: vẫn **Out-of-scope** bước 1 theo **§3.2** |

---

## 3. Phạm vi

### 3.1 In-scope

- Bảy API Task054–Task060; envelope; mã lỗi; validation cốt lõi như mục 8.  
- Bảng Flyway **V1** + **bổ sung theo OQ-3 & OQ-4b (Approved):**  
  - Bảng **`Vouchers`**: lưu mã/cấu hình giảm (áp tại retail checkout theo `voucherCode` khi còn hiệu lực).  
  - Cột `SalesOrders.voucher_id` (FK, nullable) và/hoặc tham chiếu mã; tổng giảm vẫn ghi **`discount_amount`** tổng.  
  - Cột `SalesOrders.pos_shift_ref` (NULL, VARCHAR) — ánh xạ request `shiftReference`.  
- Seed/migration **WALKIN** theo OQ-1a.  
- Bảng V1: `OrderDetails`, join `Customers`, `Products`, `ProductUnits` (và tài nguyên lỗi 409 hủy: `OrderDetails.dispatched_qty`, `StockDispatches`).  
- RBAC: JWT; quyền `can_manage_orders: true` (seed V1) cho mọi thao tác CRUD/ POS **theo từng API**. Riêng **`GET /api/v1/sales-orders` không gửi `orderChannel` (xem mọi kênh)**: **chỉ** `role` **Owner** hoặc **Admin** (**OQ-8a**); user chỉ `Staff` → **403** hoặc bắt buộc lọc `orderChannel` (cần cùng chính sách 404/empty — Dev chọn 403 rõ nghĩa).  

### 3.2 Out-of-scope

- **PM_RUN** [`PM_FIX_Task025_04_standardization.md`](../../../frontend/AGENT_TRIGGERS/PM_FIX_Task025_04_standardization.md) — chuẩn hóa bảng Inbound/Dispatch; **không** tạo/đổi endpoint Task054–060.  
- **Tự động trừ tồn / tạo phiếu xuất** khi `POST` đơn hoặc khi `checkout` bán lẻ — theo API Task060 §6, Task056 ghi chú: backlog UC10; SRS ghi **TODO nội bộ** tới tích hợp kho, không bịa số bảng ngoài Flyway.  
- (Đã bỏ) voucher chỉ hard-code: **OQ-3** đã chuyển sang **bảng DB** — nằm ở **In-scope** §3.1; migration/CRUD tối thiểu theo **§10.1** (không cần UI quản lý voucher trong v1 nếu PO chưa yêu cầu — mặc định: seed/INSERT tay hoặc script).  
- Màn hình ngoài Mini-ERP.  

---

## 4. Câu hỏi cho PO (Open Questions) — **đã chốt 27/04/2026**

> Không còn câu hỏi mở; đồng bộ triển khai theo bảng dưới. Nếu sau này đổi **schema voucher** (trường tùy chọn, bảng ca) → CR + cập nhật SRS/ API doc.

### 4.1 Quyết định PO (áp dụng triển khai)

| ID | Quyết định (PO) | Diễn giải kỹ thuật |
| :--- | :--- | :--- |
| **OQ-1** | **(a)** | Seed/migration: `customer_code = 'WALKIN'`, `name = 'Khách lẻ'`, `phone = '0900000000'`, `status = Active` (đủ NOT NULL trên V1). App: không cho user đặt trùng mã `WALKIN` (policy CRUD KH nếu có). |
| **OQ-2** | **(a)** | `POST` retail checkout: mặc định `SalesOrders.status = 'Delivered'` (bán tại quầy). |
| **OQ-3** | **Bảng `Vouchers` trên DB + áp dụng tại checkout** | Migration tạo bảng, seed mã (VD `DISCOUNT10`) — **§10.1, §10.2**. Checkout: validate `voucherCode` từ DB (active, hạn, điều kiện tối thiểu nếu có cột tương ứng); tính hàng giảm **trên tổng dòng hàng (subtotal)** trước khi tính tổng cộng `total_amount` / `discount_amount` theo công thức đã chốt. |
| **OQ-4** | **(b)** Cột mới trên `SalesOrders` | Lưu `shiftReference` từ request (VD tên cột: `pos_shift_ref VARCHAR(100)`). **Không** bắt buộc dùng prefix `[CA:…]` trong `notes` khi đã có cột. Response chi tiết đơn: trả `posShiftRef` (hoặc giữ tên thống nhất với `API_Task060` — ưu tiên camelCase envelope). |
| **OQ-5** | **idempotent 200** | Lặp `POST …/cancel` khi đã `Cancelled` → **200** với cùng payload/ trạng thái. |
| **OQ-6** | **Đúng (409)** | Có xuất kho thực tế thỏa điều kiện (vd. `StockDispatches` tồn tại, hoặc `OrderDetails.dispatched_qty` > 0) → **409** + message nghiệp vụ. |
| **OQ-7** | **(a)** | `availableQty` = tổng từ `Inventory` theo sản phẩm, quy đổi theo `ProductUnits.conversion_rate` nếu đơn vị bán khác đơn vị tồn. |
| **OQ-8** | **(a)** | `GET /api/v1/sales-orders` **không** gửi `orderChannel` → **chỉ** JWT `role` = **Owner** hoặc **Admin**; Staff bị **403** (hoặc 400/403 thống nhất một mã rõ nghĩa). **Staff** luôn lọc theo `orderChannel` từ màn tương ứng. |

### 4.2 Bảng chữ ký theo mẫu (đã điền)

| ID | Quyết định PO | Ngày |
| :--- | :--- | :--- |
| OQ-1 | (a) — seed WALKIN, phone 0900000000 | 27/04/2026 |
| OQ-2 | (a) — `Delivered` mặc định retail | 27/04/2026 |
| OQ-3 | Bảng Vouchers trên DB + dùng khi thanh toán | 27/04/2026 |
| OQ-4 | (b) — cột `pos_shift_ref` (hoặc tên tương đương) | 27/04/2026 |
| OQ-5 | 200 idempotent hủy lặp | 27/04/2026 |
| OQ-6 | 409 nếu đã xuất/điều kiện Task058 | 27/04/2026 |
| OQ-7 | (a) — tồn từ Inventory + quy đổi đơn vị | 27/04/2026 |
| OQ-8 | (a) — list mọi kênh không filter: Owner/Admin | 27/04/2026 |

---

## 5. Phân tích scope tệp & bằng chứng

### 5.1 Tài liệu đã đối chiếu (read)

- 7 file API Task054–060; `API_PROJECT_DESIGN` §4.10; `API_RESPONSE_ENVELOPE.md`; `PM_FIX_Task025_04` (xác định không thuộc BE); `FEATURES_UI_INDEX.md` §orders.  
- Flyway **V1**: `SalesOrders`, `OrderDetails`, `Customers`, `ProductUnits`, `StockDispatches`, `Roles` seed.  

### 5.2 Mã / migration dự kiến (write / verify)

- `*SalesOrder*Controller`, `*Service`, repository/JPA hoặc JDBC; DTO list/detail/line; service **Voucher** (lookup theo mã, validate hạn, tính giảm).  
- **Migrations bổ sung (đã chốt OQ-1, OQ-3, OQ-4b):** seed WALKIN; tạo **`Vouchers`** + seed; `ALTER` **`SalesOrders`** thêm `voucher_id` (FK, nullable) và `pos_shift_ref` (VARCHAR(100) nullable) — tên cột ánh xạ entity JPA.  
- Bộ lọc an toàn tham số; phân trang; `EXPLAIN` khi list tải bảng lớn.  

### 5.3 Rủi ro phát hiện sớm

- **Concurrent**: tạo đơn + checkout cùng SKU — cần transaction; kiểm tồn sau này.  
- **Voucher + discount (OQ-3)**: tồn tại mã hết hạn/điều kiện không thỏa → **400**; tổng `discount_amount` = giảm tay (`discountAmount` request) + phần voucher (nếu có) — thống nhất công thức tại `OrderService` / tương đương, không tự ý tách cột từng nguồn trừ khi bổ sung cột tương lai.  
- Gộp số dòng: subquery `itemsCount` theo trang — index `OrderDetails(order_id)` đã có V1.  

---

## 6. Persona & RBAC

| Vai trò / quyền | `can_manage_orders` | `role` (claim JWT) | Task054 `GET` **không** gửi `orderChannel` | Các API còn lại (Task054 có filter, 055–058, 059, 060) |
| :--- | :---: | :--- | :--- | :--- |
| Thiếu/invalid token | — | — | **401** | **401** |
| Staff | Có | Staff | **403** (chỉ được list theo `orderChannel` từ màn) | **200/201/…** nếu thỏa nghiệp vụ từng API |
| Owner, Admin | Có | Owner / Admin | **200** (xem tất cả kênh) cùng filter khác nếu có | **200/201/…** nếu thỏa nghiệp vụ |
| Có `can_manage_orders: false` | Không | * | **403** | **403** |

*Không tự bịa `can_view_all_order_channels` tách biệt: **OQ-8a** dùng trực tiếp `role` Owner/Admin cho case list không filter.*

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Danh sách actor

| Actor | Mô tả |
| :--- | :--- |
| User | Nhân viên POS / bán sỉ |
| Client | `mini-erp` |
| API | `smart-erp` |
| DB | PostgreSQL |

### 7.2 Luồng checkout bán lẻ (narrative)

1. User thêm sản phẩm từ `GET /pos/products` (Task059) vào giỏ.  
2. `POST /sales-orders/retail/checkout` với `lines` + optional `walkIn` / `customerId`, `discountAmount`, `voucherCode`, `paymentStatus` (mặc định `Paid` nếu không gửi theo spec Task060).  
3. API resolve `customer_id` (WALKIN seed **OQ-1a**); tra **Vouchers** theo `voucherCode` (**OQ-3**); lưu `voucher_id` nếu áp dụng; ghi `pos_shift_ref` từ `shiftReference` (**OQ-4b**); validate đơn vị/giá; tính tổng; mặc định `status = Delivered` (**OQ-2a**); ghi `SalesOrders` + `OrderDetails` trong **một transaction**; tồn kho tự động **out of scope** bước 1.  
4. Trả `201` body như chuỗi Task055 + thêm trường ánh xạ `posShiftRef` nếu API public kỳ vọng (đồng bộ với cột mới).  

### 7.3 Sơ đồ (checkout bán lẻ)

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant A as API
  participant D as DB
  U->>C: Xác nhận thanh toán
  C->>A: POST /api/v1/sales-orders/retail/checkout
  A->>A: Auth + can_manage_orders
  A->>D: SELECT/resolve Customers (WALKIN hoặc by id)
  D-->>A: customer_id
  A->>A: Validate lines, lookup Vouchers, tính tổng
  A->>D: INSERT SalesOrders; INSERT OrderDetails
  D-->>A: ok
  A-->>C: 201 + chi tiết đơn
```

### 7.4 Sơ đồ (hủy đơn)

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API
  participant D as DB
  C->>A: POST /api/v1/sales-orders/{id}/cancel
  A->>D: Lock SalesOrders; read OrderDetails/StockDispatches
  D-->>A: rows
  alt đã hủy (idempotent — OQ-5)
    A-->>C: 200, giữ trạng thái Cancelled
  else đã xuất / dispatched
    A-->>C: 409
  else cho phép hủy lần đầu
    A->>D: UPDATE status Cancelled, cancelled_at, cancelled_by
    A-->>C: 200
  end
```

---

## 8. Hợp đồng HTTP & ví dụ JSON

> Chung: `Content-Type: application/json`; `Authorization: Bearer` khi cần. Tên thuộc tính **camelCase** trong JSON.

### 8.1 Tổng hợp endpoint

| Task | Method | Path | 2xx thành công |
| :---: | :--- | :--- | :--- |
| 054 | `GET` | `/api/v1/sales-orders` | `200` |
| 055 | `GET` | `/api/v1/sales-orders/{id}` | `200` |
| 056 | `POST` | `/api/v1/sales-orders` | `201` |
| 057 | `PATCH` | `/api/v1/sales-orders/{id}` | `200` |
| 058 | `POST` | `/api/v1/sales-orders/{id}/cancel` | `200` |
| 059 | `GET` | `/api/v1/pos/products` | `200` |
| 060 | `POST` | `/api/v1/sales-orders/retail/checkout` | `201` |

### 8.2 Lỗi (mỗi mã — ví dụ `message` tiếng Việt, nội dung đại diện nghiệp vụ)

**400 `BAD_REQUEST`** — validation, giá không hợp lệ, dòng rỗng, voucher lỗi, `discountAmount` vượt chuẩn.

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại giỏ hàng hoặc mã giảm giá.",
  "details": {}
}
```

**401 `UNAUTHORIZED`** — thiếu/không hợp lệ token.

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.",
  "details": {}
}
```

**403 `FORBIDDEN`** — thiếu `can_manage_orders` hoặc **Staff** gọi `GET /sales-orders` **không** gửi `orderChannel` (OQ-8a).

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền thực hiện thao tác này.",
  "details": {}
}
```

**404 `NOT_FOUND`** — `sales-orders` hoặc `customerId` không tồn tại (theo từng API).

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy đơn hàng.",
  "details": {}
}
```

**409 `CONFLICT`** — hủy không hợp lệ, Return sai `refSalesOrderId`/`customer`, tồn kho nếu đã siết, v.v.

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể hủy đơn do đã phát sinh xuất kho.",
  "details": { "reason": "HAS_DISPATCH" }
}
```

**500** — lỗi hệ thống (message không lộ kỹ thuật).

```json
{
  "success": false,
  "error": "INTERNAL_SERVER_ERROR",
  "message": "Không thể xử lý yêu cầu. Vui lòng thử lại sau.",
  "details": {}
}
```

### 8.3 Ví dụ thành công (đầy đủ tiêu biểu)

**8.3.1 Task054 — `GET /api/v1/sales-orders` — `200` (rút gọn 1 phần tử)**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "orderCode": "SO-2026-0001",
        "customerId": 12,
        "customerName": "Công ty TNHH Tuấn Phát",
        "totalAmount": 45000000,
        "discountAmount": 0,
        "finalAmount": 45000000,
        "status": "Delivered",
        "orderChannel": "Wholesale",
        "paymentStatus": "Paid",
        "itemsCount": 5,
        "notes": null,
        "createdAt": "2026-03-01T10:00:00Z",
        "updatedAt": "2026-03-02T08:00:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 120
  },
  "message": "Thành công"
}
```

**8.3.2 Task060 — `POST /api/v1/sales-orders/retail/checkout` — `201` (cấu trúc cùng Task055)**

Request:

```json
{
  "customerId": null,
  "walkIn": true,
  "lines": [
    {
      "productId": 12,
      "unitId": 101,
      "quantity": 2,
      "unitPrice": 6000
    }
  ],
  "discountAmount": 0,
  "voucherCode": "DISCOUNT10",
  "paymentStatus": "Paid",
  "notes": null,
  "shiftReference": "SHIFT-0418"
}
```

Response (cùng dạng object chi tiết như Task055 — mô tả: đơn `orderChannel: "Retail"`, đủ `lines`):

```json
{
  "success": true,
  "data": {
    "id": 2001,
    "orderCode": "SO-2026-0142",
    "customerId": 1,
    "customerName": "Khách lẻ",
    "totalAmount": 12000,
    "discountAmount": 1200,
    "finalAmount": 10800,
    "status": "Delivered",
    "orderChannel": "Retail",
    "paymentStatus": "Paid",
    "parentOrderId": null,
    "refSalesOrderId": null,
    "shippingAddress": null,
    "notes": null,
    "posShiftRef": "SHIFT-0418",
    "createdAt": "2026-04-27T10:00:00Z",
    "updatedAt": "2026-04-27T10:00:00Z",
    "lines": [
      {
        "id": 5001,
        "productId": 12,
        "productName": "Nước suối 500ml",
        "skuCode": "SP0001",
        "unitId": 101,
        "unitName": "Chai",
        "quantity": 2,
        "unitPrice": 6000,
        "lineTotal": 12000,
        "dispatchedQty": 0
      }
    ]
  },
  "message": "Tạo đơn thành công"
}
```

*Ghi chú: số liệu minh họa. **`status: Delivered`** theo **OQ-2a**; WALKIN theo **OQ-1a**; **`posShiftRef`** ánh xạ cột `pos_shift_ref` (**OQ-4b**). Response `GET` chi tiết/ list nên cùng pattern trường này. Chưa có tên field trong `API_Task060` cũ → xem **§12 (GAP)**: bổ sung tài liệu API/contract.*

**8.3.3 Task059 — `GET /api/v1/pos/products?limit=40` — `200` (một `item` mẫu)**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "productId": 12,
        "productName": "Nước suối 500ml",
        "skuCode": "SP0001",
        "barcode": "8934563123456",
        "unitId": 101,
        "unitName": "Chai",
        "unitPrice": 6000,
        "availableQty": 240,
        "imageUrl": null
      }
    ]
  },
  "message": "Thành công"
}
```

---

## 9. Quy tắc nghiệp vụ (bảng tóm tắt)

| Mã | Điều kiện | Hành động / kết quả |
| :--- | :--- | :--- |
| BR-1 | Tạo đơn sỉ/trả (Task056) | `order_channel` ∈ {`Wholesale`, `Return`}, `Customer` tồn tại, `ProductUnits` thuộc từng dòng. |
| BR-2 | Checkout retail (Task060) | Một `customerId` hợp lệ **hoặc** walk-in (resolve bản ghi WALKIN — **OQ-1a**); tính lại `total_amount` server-side; mặc định `status = Delivered` (**OQ-2a**). |
| BR-3 | Hủy (Task058) | Không cho hủy nếu điều vi phạm **OQ-6 (409)**; lần thứ hai trên đơn đã hủy → **200** idempotent (**OQ-5**); cập nhật `cancelled_at`, `cancelled_by` ở lần hủy hợp lệ. |
| BR-4 | PATCH (Task057) | Không PATCH khi `status = Cancelled` → **409**. |
| BR-5 | Voucher (Task060) | Lookup từ bảng **Vouchers** theo mã, kiểm tra còn hiệu lực; tổng `discount_amount` = **chiết khấu từ voucher (theo từng bản ghi: % hoặc số tiền)** + tiền giảm từ body `discountAmount` (không vượt quá nghiệp vụ cho phép) — công thức tối thiểu: tính subtotal dòng, áp `discountAmount` cố định + voucher, rồi ghi tổng lên `SalesOrders.discount_amount`. |
| BR-6 | List tất cả kênh (Task054) | Bỏ `orderChannel` query → chỉ **Owner, Admin** (**OQ-8a**). |

---

## 10. Dữ liệu & SQL tham chiếu (phối hợp Agent SQL)

> Tên bảng gốc **V1** + **migration bổ sung (OQ-1, OQ-3, OQ-4b)**. Dev dùng đúng tên ánh xạ JPA.  

### 10.1 Bảng / quan hệ (tên logic)

| Bảng / cột mới | Read / Write | Ghi chú |
| :--- | :---: | :--- |
| `SalesOrders` (V1 + **ALTER**) | R/W | Thêm **`voucher_id` INT NULL → FK `Vouchers(id)`**; **`pos_shift_ref` VARCHAR(100) NULL** (OQ-4b). Có sẵn: `order_channel`, `payment_status`, `ref_sales_order_id`, `cancelled_at`, `cancelled_by` |
| **`Vouchers` (bảng mới)** | R / W (CRUD nội bộ hoặc sau) | Cột tối thiểu gợi ý: `id`, `code` **UNIQUE**, `name`, `discount_type` (`Percent` \| `FixedAmount`), `discount_value` (NUMERIC; với `Percent` ∈ [0,100]), `is_active` BOOLEAN, `valid_from` / `valid_to` NULLABLE, `created_at` / `updated_at` — Tech Lead điều chỉnh kiểu ngày theo chuẩn dự án. |
| `OrderDetails` | R/W | `price_at_time` = `unitPrice` tạo đơn; `line_total` generated |
| `Customers` | R | WALKIN seed (OQ-1a) |
| `StockDispatches` | R | 409 hủy theo OQ-6 nếu tồn tại bản ghi theo `order_id` (và/hoặc dùng `OrderDetails.dispatched_qty` — ưu tiên đủ điều kiện Task058) |
| `ProductUnits` | R | Validate từng dòng; **OQ-7a** quy đổi tồn |
| `Inventory` | R | **OQ-7a** tổng tồn theo sản phẩm/location |
| `Products` | R | Tên, SKU, join Task055/059 |

**DDL mẫu (PostgreSQL) — cô đọng, Tech Lead/ SQL review tên/ ràng buộc:**

```sql
CREATE TABLE Vouchers (
  id SERIAL PRIMARY KEY,
  code varchar(50) NOT NULL UNIQUE,
  name varchar(255),
  discount_type varchar(20) NOT NULL
    CHECK (discount_type IN ('Percent', 'FixedAmount')),
  discount_value NUMERIC(12,2) NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  valid_from date,
  valid_to date,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Seed ví dụ: code DISCOUNT10, discount_type=Percent, discount_value=10

ALTER TABLE SalesOrders
  ADD COLUMN IF NOT EXISTS voucher_id INT NULL
    REFERENCES Vouchers(id) ON DELETE SET NULL;
ALTER TABLE SalesOrders
  ADD COLUMN IF NOT EXISTS pos_shift_ref VARCHAR(100) NULL;
CREATE INDEX IF NOT EXISTS idx_salesorders_voucher ON SalesOrders (voucher_id);
```

*Chỉ mục bổ sung khi cần tra cứu theo mã ca — có thể thêm `idx_salesorders_pos_shift` nếu báo cáo theo chuỗi.*

### 10.2 Gợi ý seed walk-in (OQ-1a — bắt buộc trước checkout retail)

```sql
INSERT INTO Customers (customer_code, name, phone, status)
SELECT 'WALKIN', 'Khách lẻ', '0900000000', 'Active'
WHERE NOT EXISTS (SELECT 1 FROM Customers WHERE customer_code = 'WALKIN');
```

### 10.3 Transaction (checkout retail)

- Một transaction: resolve `customer_id` (WALKIN/đã chọn) → **gán `voucher_id` (sau khi `SELECT` Voucher hợp lệ)**, tính `total_amount`/`discount_amount`, ghi `pos_shift_ref` nếu có; **`INSERT` `SalesOrders` với `order_channel=Retail`**, `status=Delivered` mặc định; **`INSERT` từng dòng `OrderDetails`**.  
- Cùng tư tưởng (ít trường) cho Task056.  
- Task057: `SELECT ... FOR UPDATE` rồi `UPDATE` một phần.  
- Task058: lock header + read `StockDispatches`/`OrderDetails` trước khi cập nhật hủy; hủy lặp → xử lý theo OQ-5.  

### 10.4 Index (đã có / gợi ý bổ sung)

- V1: `idx_so_order_channel`, `idx_so_payment_status`, `idx_od_order` — dùng cho lọc list và đếm dòng.  
- Tìm POS: index trên `Products(sku_code`, `barcode`, `name)` nếu chưa thấy (grep migration bổ sung) — nếu thiếu → open CR migration nhỏ (không bịa tên: đối chiếu `Products` V1).  

### 10.5 Kiểm chứng dữ liệu cho Tester

- Sau seed WALKIN + seed **Voucher** mẫu: checkout có `voucherCode` hợp lệ → `voucher_id` khác null, `discount_amount` khớp tính.  
- `pos_shift_ref` = giá trị gửi trong `shiftReference` (OQ-4b).  
- Hủy: đơn chưa xuất (theo OQ-6) → thành `Cancelled` + `cancelled_by` = user hiện tại.  
- Hủy lặp trên cùng đơn: **OQ-5** → **200**, không lỗi, không tăng số bản ghi.  
- **Task059 (OQ-7a):** tồn từ `Inventory` hợp lý khi sản phẩm có từng đơn vị/kho.  

---

## 11. Acceptance criteria (Given / When / Then) — tóm tắt

```text
Given user có can_manage_orders, WALKIN + Voucher seed (OQ-1a, OQ-3)
When POST retail checkout hợp lệ
Then 201, order_channel=Retail, status=Delivered (OQ-2a), final_amount đúng công thức, >=1 dòng OrderDetails, voucher_id/pos_shift_ref theo mã/lý do gửi
```

```text
Given sales order id tồn tại
When GET by id
Then 200, lines join đúng product/unit, posShiftRef (nếu lưu), voucher_id/ join voucher khi cần hiển thị, dispatched_qty từ DB
```

```text
Given order chưa Cancelled và OQ-6 cho phép hủy
When POST cancel lần 1
Then 200, status=Cancelled, cancelledAt và cancelledBy hợp lệ; When POST cancel lần 2 thì 200 idempotent cùng trạng thái (OQ-5)
```

```text
Given user Staff, can_manage_orders=true
When GET /sales-orders bỏ orderChannel
Then 403
```

```text
Given user Owner hoặc Admin, can_manage_orders=true
When GET /sales-orders bỏ orderChannel
Then 200 với tất cả kênh (OQ-8a)
```

```text
Given query GET list với orderChannel=Wholesale
When DB có đơn Wholesale và Return
Then chỉ thấy Wholesale
```

```text
Given thiếu can_manage_orders
When bất kỳ endpoint Task054–060
Then 403 (hoặc 401 nếu không xác thực)
```

---

## 12. GAP & giả định

| GAP / Giả định | Tác động | Hành động đề xuất |
| :--- | :--- | :--- |
| API doc Task054 gợi `ALTER` trùng cột với V1 | Nhầm tưởng cần migration mới | Dev bỏ qua DDL trùng; SRS §0.1. |
| SQL mẫu dùng `sales_orders` | Sai tên bảng nếu copy nộp | Dùng entity/Flyway; §10.1. |
| **`API_Task060` / `API_Task055` chưa mô tả** `posShiftRef` trên body response / chi tiết đơn, voucher qua bảng | Client chưa biết tên trường ổn định | **DOC_SYNC:** cập nhật `API_Task060` + `Task055/054` theo cột `voucher_id` mapping & `posShiftRef`; ghi cách tính voucher từ DB. |
| Check constraint `Vouchers` / tên bảng PG | DDL §10.1 mang tính mẫu | Tech Lead duyệt 1 lần trước merge Flyway; thứ tự: tạo `Vouchers` → `ALTER` `SalesOrders` → seed. |
| Tích hợp trừ tồn UC10 chưa có | Checkout không giảm kho tự động | Bước 2/ UC10; TODO code nội bộ. |
| PM Task025_04 chuẩn bảng | Không tác động API | `RULES_UI_TABLE` — FE. |

---

## 13. PO sign-off (Approved — 27/04/2026)

- [x] Đã trả lời **OQ-1..OQ-8** (§4.1–4.2); không còn câu hỏi mở
- [x] JSON mẫu (§8) thống nhất với quyết định PO; **GAP** §12 theo dõi đồng bộ tài liệu API
- [x] In/Out (§3) bao gồm bảng **Vouchers** + cột ca + WALKIN seed theo OQ

**Nhãn trạng thái tài liệu:** `Approved` — sẵn sàng bàn giao **PM** / **Tech Lead** / **Dev** theo `WORKFLOW_RULE` (bước tiếp: migration + mã, DOC_SYNC tùy thứ tự team).  
**Ngày / chữ ký mềm (repo):** `27/04/2026` — cùng bảng trả lời §4.2

---

**Tổng kết nhanh**

- **Đã làm:** Đồng bộ SRS theo câu trả lời PO §4.2: **WALKIN + `Delivered` + bảng Vouchers + cột ca + 200 hủy lặp + 409 theo OQ-6 + tồn POS 7a + list kênh Owner/Admin (8a)**. Trạng thái: **Approved** (§13).  
- **Việc tiếp theo (Dev/Doc):** viết **Flyway** tạo `Vouchers` + cột + seed; triển khai BE; **DOC_SYNC** tài liệu API theo **§12 GAP** (posShiftRef, response voucher).  
- **Rủi ro / ngoài SRS:** tự động trừ tồn Kho (UC10); UI quản lý Voucher nếu sau này PO mở scope.
