# SRS — UC9 / UC10 — Trừ tồn kho khi thanh toán POS (retail checkout) — Task090

> **File (Spring / `smart-erp`):** `backend/docs/srs/SRS_Task090_uc9-retail-checkout-stock-deduction.md`  
> **Người soạn:** Agent BA (+ mục §10 bám `SQL_AGENT_INSTRUCTIONS.md`)  
> **Ngày:** 28/04/2026  
> **Trạng thái:** `Approved`  
> **PO duyệt (khi Approved):** PO (chốt OQ §4 — 29/04/2026), `29/04/2026`

---

## 0. Đầu vào & traceability

| Nguồn | Đường dẫn / ghi chú |
| :--- | :--- |
| API hiện tại (POS checkout) | [`../../../frontend/docs/api/API_Task060_sales_orders_retail_checkout.md`](../../../frontend/docs/api/API_Task060_sales_orders_retail_checkout.md) |
| API POS tìm hàng (tồn hiển thị) | [`../../../frontend/docs/api/API_Task059_pos_products_get_search.md`](../../../frontend/docs/api/API_Task059_pos_products_get_search.md) |
| SRS UC9 (Task054–060) — **đã ghi out-of-scope trừ tồn** | [`SRS_Task054-060_sales-orders-pos-and-retail-checkout.md`](SRS_Task054-060_sales-orders-pos-and-retail-checkout.md) §3.2 |
| SRS sản phẩm / `currentStock` read-model | [`SRS_Task034-041_products-management.md`](SRS_Task034-041_products-management.md) (tham chiếu `ProductJdbcRepository` — tổng `Inventory`) |
| UC / DB spec | [`../../../frontend/docs/UC/Database_Specification.md`](../../../frontend/docs/UC/Database_Specification.md) — kho, đơn, xuất kho |
| Flyway thực tế | [`../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql) — `Inventory`, `OrderDetails`, `SalesOrders`, `StockDispatches`, `InventoryLogs`, `ProductUnits`, `WarehouseLocations` |
| Ticket / pain | Sau **Thanh toán** tại **Đơn bán lẻ (POS)**, cột **Tồn kho** tại **Quản lý sản phẩm** không đổi — nguyên nhân: Task060 chưa ghi nhận xuất; read-model `currentStock` từ `Inventory` |

**GAP hợp đồng HTTP:** Chưa có file `frontend/docs/api/API_Task090_*.md` riêng. V1 giữ **cùng path** `POST /api/v1/sales-orders/retail/checkout`, mở rộng logic server; tài liệu đã được đồng bộ vào **`API_Task060`** (trừ tồn theo `StoreProfiles`, 409 thiếu tồn) sau khi SRS này **Approved**.

---

## 1. Tóm tắt điều hành

- **Vấn đề:** Checkout bán lẻ chỉ tạo `SalesOrders` + `OrderDetails` — **không** cập nhật `Inventory`, **không** tạo chứng từ xuất — nên tổng tồn (và cột **Tồn kho** trên danh sách sản phẩm) không phản ánh giao dịch POS.
- **Mục tiêu nghiệp vụ:** Trong **một giao dịch DB** (transaction), khi POS checkout thành công: **kiểm tra đủ tồn** (theo đơn vị cơ sở), **ghi nhận xuất** (phiếu xuất + log + trừ `Inventory.quantity`), cập nhật **`OrderDetails.dispatched_qty`** khớp số đã xuất — để dữ liệu thống nhất với luồng **hủy đơn** Task058 (đã kiểm tra `StockDispatches` / `dispatched_qty`).
- **Đối tượng:** Nhân viên POS (`can_manage_orders`), hệ thống kho/read-model sản phẩm.

### 1.1 Giao diện Mini-ERP

> Tra [`../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md).

| Nhãn menu (Sidebar) | Route | Page (export) | Component / vùng chính | File (dưới `frontend/mini-erp/src/features/`) |
| :--- | :--- | :--- | :--- | :--- |
| Đơn bán lẻ (POS) | `/orders/retail` | `RetailPage` | `POSCartPanel` (mutation checkout Task060), `POSProductSelector` (Task059) | `orders/pages/RetailPage.tsx`, `orders/components/POSCartPanel.tsx`, `POSProductSelector.tsx` |
| Quản lý sản phẩm | `/products/list` | `ProductsPage` | `ProductTable` (cột **Tồn kho** = `currentStock`) | `product-management/pages/ProductsPage.tsx`, `product-management/components/ProductTable.tsx` |
| Tồn kho (chi tiết vị trí) | `/inventory/stock` | `StockPage` | `StockTable` — sau xuất POS, bản ghi `Inventory` tương ứng giảm | `inventory/pages/StockPage.tsx` |

**FE tối thiểu (ngoài phạm vi BE SRS, ghi để PM/FE không sót):** sau `201` checkout, **invalidate** query danh sách sản phẩm (`["product-management","products","list"]`) và tùy chính sách UX: summary tồn (`inventory` KPI) — xem §12.

---

## 2. Bóc tách nghiệp vụ (capabilities)

| # | Capability | Kích hoạt bởi | Kết quả mong đợi | Ghi chú |
| :---: | :--- | :--- | :--- | :--- |
| C1 | Quy đổi SL dòng đơn sang **đơn vị cơ sở** | `POST …/retail/checkout` | Mỗi dòng có `qty_base` integer > 0 | Dùng `ProductUnits.conversion_rate` (đã dùng cho Task059 `availableQty` — **OQ-1** chốt công thức giống Task054 OQ-7a) |
| C2 | Xác định **phạm vi kho** (vị trí) để trừ | Checkout | Tập `Inventory` rows bị trừ là tập hợp rõ ràng | **OQ-2** — `locationId` trên request vs kho mặc định vs tổng toàn vị trí |
| C3 | Kiểm tra tồn khả dụng (pessimistic hoặc tương đương) | Trước khi INSERT đơn | Không commit nếu thiếu hàng | Trả **409** với `message` nghiệp vụ + `details` theo SKU/dòng (**§8**) |
| C4 | Cấp phát tồn (allocation) theo lô / vị trí | Checkout | Giảm `Inventory.quantity` đúng tổng `qty_base` | **OQ-3** FEFO theo `expiry_date` / `batch_number` vs “một dòng tồn gộp” |
| C5 | Ghi chứng từ xuất | Checkout | Một bản ghi **`StockDispatches`** cho đơn POS (order_id), `status = 'Full'` sau khi xuất đủ; hoặc policy khác **OQ-4** | Khớp schema V1; `dispatch_code` unique |
| C6 | Ghi **`InventoryLogs`** | Mỗi lần trừ bucket `Inventory` | `action_type = 'OUTBOUND'`, `quantity_change` **âm**, `dispatch_id` FK, `unit_id` = đơn vị cơ sở | Comment V1: SL log theo convention hiện có inbound |
| C7 | Cập nhật **`OrderDetails.dispatched_qty`** | Sau insert dòng đơn | `dispatched_qty = quantity` (POS đủ hàng ngay) | Giữ invariant `dispatched_qty <= quantity` |
| C8 | Giữ nguyên RBAC / validation Task060 | Checkout | Voucher, walk-in, giá, `payment_status` như hiện tại | Không làm yếu validation đã có |
| C9 | Tương thích **hủy đơn** Task058 | `POST …/sales-orders/{id}/cancel` | Sau checkout có xuất: **409** “đã có phiếu xuất / đã giao từ kho” (đã implement) | Không mở rộng **hoàn tồn khi hủy** trong v1 SRS này — **OQ-5** |

---

## 3. Phạm vi

### 3.1 In-scope

- Mở rộng **một transaction** `retailCheckout`: thêm bước **đọc tồn → trừ tồn → ghi log + dispatch + dispatched_qty** với bảng **đã có Flyway V1** (không bịa bảng mới trừ khi OQ bắt buộc DDL).
- Mã lỗi mới / mở rộng: **409** thiếu tồn; có thể **423 Locked** hoặc **409** khi race (chọn một — **OQ-6**).
- Đồng bộ thông điệp lỗi **tiếng Việt, nghiệp vụ** (không lộ kỹ thuật) — bám `BA_AGENT_INSTRUCTIONS.md` §3.7.

### 3.2 Out-of-scope

- **Tự động trừ tồn** cho `POST /api/v1/sales-orders` (đơn **Wholesale** / **Return**) — có thể reuse service nội bộ sau; không bắt buộc trong Task090.
- **Ghi FinanceLedger / Cash** theo doanh thu POS — tách task tài chính nếu PO yêu cầu.
- UI chỉnh sửa phiếu xuất thủ công, in PX — không bắt buộc Task090.

---

## 4. Câu hỏi cho PO (Open Questions) — **đã chốt 29/04/2026**

| ID | Câu hỏi | Ảnh hưởng nếu không trả lời | Blocker? |
| :--- | :--- | :--- | :---: |
| **OQ-1** | Quy đổi `quantity` (đơn vị bán) → đơn vị cơ sở: Đề xuất các phương án: (a) Luôn theo đúng công thức của Task059 / OQ-7a Task054 (áp dụng `conversion_rate` nhân), (b) Cho phép hệ số tùy chỉnh từng mặt hàng, (c) Định nghĩa lại công thức chuyển đổi (nhân hoặc chia, làm tròn giá trị). |
| **OQ-2** | POS checkout trừ tồn theo phương án: (a) Dùng **`locationId`** FE gửi lên (đồng bộ filter Task059), (b) Mặc định một kho lưu trữ chính (cần cấu hình `StoreProfiles` hoặc migration bổ sung), (c) Tự động chọn tổng tồn kho tại tất cả các vị trí (allocation tự động). |
| **OQ-3** | Khi một `product_id` có nhiều dòng tồn kho (Inventory khác lô/kệ): (a) Luôn áp dụng FEFO với hướng xử lý `expiry_date` NULL là sắp sau cùng, (b) Gộp tất cả dòng tồn thành một bucket tổng hợp, (c) Cho phép tùy chọn trên từng nhóm sản phẩm hoặc theo policy từng kỳ. |
| **OQ-4** | Đơn POS tạo chứng từ xuất: (a) Một `StockDispatches` duy nhất cho toàn bộ đơn, (b) Tạo nhiều phiếu xuất theo từng dòng hoặc mặt hàng/lô trong đơn, (c) Policy linh hoạt chọn nhóm tạo chứng từ dựa vào phân loại sản phẩm/kho. |
| **OQ-5** | Sau khi đã trừ tồn POS, khi hủy đơn: (a) Bắt buộc hoàn kho (reverse toàn bộ log và dispatch, delete mềm), (b) Không hoàn kho, chỉ cho phép xuất lại khi tạo đơn trả riêng, (c) Policy cho phép một số trường hợp đặc biệt hoàn tồn tự động dựa vào trạng thái đơn/phiếu xuất. |
| **OQ-6** | Xử lý cạnh tranh khi hai request checkout cùng SKU: (a) Áp dụng transaction mức serializable hoặc dùng `SELECT ... FOR UPDATE` để tránh race condition, (b) Nhận lỗi **409** nếu hết hàng do đã có đơn khác xuất trước, (c) Chỉ cảnh báo FE, backend không kiểm tra (tăng hiệu năng, chấp nhận lệch nhẹ tồn). |

**Trả lời PO (điền khi chốt):**

| ID | Quyết định PO | Ngày |
| :--- | :--- | :--- |
| OQ-1 | (a) Theo đúng công thức Task059 / OQ-7a Task054: **`qty_base = qty_sale * conversion_rate`** (làm tròn theo rule §10, không dùng chia). | 29/04/2026 |
| OQ-2 | (b) Trừ tồn theo **kho mặc định** cấu hình trong `StoreProfiles` (Owner) → không nhận `locationId` từ client. | 29/04/2026 |
| OQ-3 | (a) **FEFO** theo `expiry_date ASC NULLS LAST`, sau đó `id ASC` (ổn định). | 29/04/2026 |
| OQ-4 | (c) Policy linh hoạt: **v1 triển khai 1 `StockDispatches`/đơn POS**; tương lai có thể tách theo nhóm sản phẩm/kho mà không đổi contract checkout. | 29/04/2026 |
| OQ-5 | (a) **Bắt buộc hoàn kho khi hủy đơn POS** (reverse log + cập nhật tồn + cập nhật dispatched_qty + trạng thái chứng từ xuất). | 29/04/2026 |
| OQ-6 | (a) Chống race bằng **`SELECT ... FOR UPDATE`** trên các dòng `Inventory` liên quan; nếu thiếu tồn sau khi lock → **409** nghiệp vụ. | 29/04/2026 |

---

## 5. Phân tích scope tệp & bằng chứng (Evidence scope)

### 5.1 Tài liệu đã đối chiếu (read)

- `API_Task060`, `API_Task059`, `SRS_Task054-060`, Flyway **V1** (`Inventory`, `OrderDetails`, `StockDispatches`, `InventoryLogs`, `ProductUnits`).
- `SalesOrderService.java` — `retailCheckout`, `cancel` (điều kiện 409 đã có).
- `ProductJdbcRepository` / `PosProductJdbcRepository` — cách tính tồn tổng / theo location.

### 5.2 Mã / migration dự kiến (write / verify)

- `SalesOrderService.retailCheckout` — orchestration; có thể tách `RetailStockAllocationService` / `StockDispatchService` để test.
- JDBC repository mới hoặc mở rộng: **lock + update** `Inventory`, **insert** `StockDispatches`, `InventoryLogs`, **update** `OrderDetails.dispatched_qty`.
- **Flyway (bắt buộc theo OQ-2):** thêm cột cấu hình kho mặc định cho POS vào `StoreProfiles` (vd. `default_retail_location_id INT NULL REFERENCES WarehouseLocations(id)`), seed/UPDATE cho store hiện có để POS checkout luôn có kho trừ tồn.
- Test: integration hoặc `@Transactional` test — hai luồng concurrent (OQ-6).

### 5.3 Rủi ro phát hiện sớm

- **Deadlock:** thứ tự khóa `Inventory` rows (sort theo `inventory.id`).
- **Partial failure:** phải rollback toàn bộ nếu một dòng không đủ tồn.
- **Double submit:** idempotency-Key header — **OQ** nếu PO yêu cầu; mặc định v1 có thể bỏ qua.

---

## 6. Persona & RBAC

| Vai trò | Điều kiện | Ghi chú |
| :--- | :--- | :--- |
| Staff / Owner / Admin | `can_manage_orders: true` (JWT) | Giữ nguyên Task060 |
| Thiếu quyền | **403** | Như Task060 |

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Danh sách actor

| Actor | Mô tả |
| :--- | :--- |
| User | Nhân viên POS |
| Client | `mini-erp` |
| API | `smart-erp` |
| DB | PostgreSQL |

### 7.2 Luồng chính (narrative)

1. Client gửi `POST …/retail/checkout` (body như Task060; **không** nhận `locationId` từ client theo OQ-2).  
2. API xác thực JWT + quyền; resolve customer / voucher / tổng tiền **như hiện tại**.  
3. **Quy đổi** từng dòng sang `qty_base`; **tổng hợp** nhu cầu theo `product_id`.  
4. **Khóa / kiểm tra** tồn theo policy OQ-2–OQ-3; nếu không đủ → **409**, không ghi đơn.  
5. **INSERT** `SalesOrders` + `OrderDetails` (như hiện tại).  
6. **INSERT** `StockDispatches` (theo OQ-4); **INSERT** `InventoryLogs` + **UPDATE** `Inventory.quantity` (giảm); **UPDATE** `OrderDetails.dispatched_qty`.  
7. **Commit**; trả **201** + body chi tiết đơn (Task055 shape).  
8. Người dùng mở **Quản lý sản phẩm**: sau refetch, `currentStock` giảm (read-model từ `Inventory`).

### 7.3 Sơ đồ (checkout có trừ tồn)

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API
  participant D as DB
  C->>A: POST /api/v1/sales-orders/retail/checkout
  A->>A: Auth, validate, pricing, voucher
  A->>D: BEGIN (implicit @Transactional)
  A->>D: Lock/SELECT Inventory (policy OQ-2, OQ-3)
  alt thiếu tồn
    A->>D: ROLLBACK
    A-->>C: 409 + details
  else đủ tồn
    A->>D: INSERT SalesOrders, OrderDetails
    A->>D: INSERT StockDispatches
    A->>D: UPDATE Inventory; INSERT InventoryLogs
    A->>D: UPDATE OrderDetails.dispatched_qty
    A->>D: COMMIT
    A-->>C: 201 + order detail
  end
```

---

## 8. Hợp đồng HTTP & ví dụ JSON

### 8.1 Tổng quan endpoint

| Thuộc tính | Giá trị |
| :--- | :--- |
| Method + path | `POST /api/v1/sales-orders/retail/checkout` *(không đổi path v1)* |
| Auth | Bearer JWT |
| Content-Type | `application/json` |

**Đã chốt OQ-2:** không bổ sung `locationId` vào body. API dùng kho mặc định cấu hình trong `StoreProfiles` để trừ tồn.

### 8.2 Request — schema logic (bổ sung)

| Field | Vị trí | Kiểu | Bắt buộc | Validation | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| *(kho trừ tồn)* | server config | — | — | — | Dùng `StoreProfiles.default_retail_location_id` (OQ-2). Nếu chưa cấu hình → **500** hoặc **409** theo policy Dev/Tech Lead (khuyến nghị 500 + message cấu hình thiếu). |
| *(các field Task060)* | body | — | theo Task060 | theo Task060 | `lines`, `walkIn`, … |

### 8.3 Request — ví dụ JSON đầy đủ

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
  "voucherCode": null,
  "paymentStatus": "Paid",
  "notes": null,
  "shiftReference": "SHIFT-0418"
}
```

### 8.4 Response thành công — `201`

Giữ nguyên envelope + shape **Task055 / Task060** (chi tiết đơn vừa tạo). Không bắt buộc thêm block “stock” trong response v1.

```json
{
  "success": true,
  "data": {
    "id": 501,
    "orderCode": "SO-2026-000501",
    "orderChannel": "Retail",
    "status": "Delivered",
    "paymentStatus": "Paid",
    "lines": [
      {
        "id": 9001,
        "productId": 12,
        "unitId": 101,
        "quantity": 2,
        "dispatchedQty": 2,
        "unitPrice": 6000,
        "lineTotal": 12000
      }
    ]
  },
  "message": "Tạo đơn thành công"
}
```

> Ghi chú: `dispatchedQty` trong JSON public phải **khớp** cột `OrderDetails.dispatched_qty` sau Task090.

### 8.5 Response lỗi — ví dụ đầy đủ

**400 — validation (như Task060)**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Thông tin thanh toán không hợp lệ. Vui lòng kiểm tra lại giỏ hàng.",
  "details": {}
}
```

**401 / 403** — giữ mẫu [`API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md).

**409 — thiếu tồn kho (nghiệp vụ)**

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không đủ tồn kho để hoàn tất thanh toán. Vui lòng giảm số lượng hoặc kiểm tra nhập hàng.",
  "details": {
    "lines": [
      {
        "productId": 12,
        "requestedQuantity": 2,
        "availableQuantity": 1
      }
    ]
  }
}
```

> `details` có thể thu gọn/chi tiết hơn theo Dev — không chứa URL hay stack trace.

**500**

```json
{
  "success": false,
  "error": "INTERNAL_SERVER_ERROR",
  "message": "Không thể hoàn tất thanh toán. Vui lòng thử lại hoặc liên hệ quản trị.",
  "details": {}
}
```

---

## 9. Quy tắc nghiệp vụ (bảng)

| Mã | Điều kiện | Hành động / kết quả |
| :--- | :--- | :--- |
| BR-1 | Tổng `qty_base` theo `product_id` > tổng `Inventory.quantity` khả dụng (theo OQ-2) | **409**, không tạo đơn |
| BR-2 | Mọi bước ghi `SalesOrders` / tồn / log thành công | `OrderDetails.dispatched_qty` = `quantity` cho từng dòng POS đủ hàng |
| BR-3 | Hủy đơn POS đã xuất kho (OQ-5) | `POST …/cancel` **thực hiện hoàn kho** (reverse log + cập nhật `Inventory` + set `StockDispatches.status='Cancelled'` + reset `OrderDetails.dispatched_qty`) rồi mới set đơn `Cancelled` |
| BR-4 | `Inventory.quantity` sau xuất | Không âm — CHECK constraint V1; transaction rollback nếu vi phạm |

---

## 10. Dữ liệu & SQL tham chiếu (phối hợp Agent SQL)

> Bám [`../../AGENTS/SQL_AGENT_INSTRUCTIONS.md`](../../AGENTS/SQL_AGENT_INSTRUCTIONS.md): tên bảng/cột đúng Flyway V1.

### 10.1 Bảng / quan hệ

| Bảng | Read / Write | Ghi chú |
| :--- | :--- | :--- |
| `ProductUnits` | R | `conversion_rate` — quy đổi sang base unit (OQ-1) |
| `Inventory` | R + U | `quantity` giảm; khóa theo `id` hoặc `product_id+location_id` tùy allocation |
| `SalesOrders` | W | Giữ nguyên retail insert |
| `OrderDetails` | W + U | INSERT line; UPDATE `dispatched_qty` |
| `StockDispatches` | W | `order_id`, `user_id`, `dispatch_date`, `status` |
| `InventoryLogs` | W | `OUTBOUND`, `quantity_change` < 0, `dispatch_id`, `product_id`, `unit_id` (base) |
| `WarehouseLocations` | R | Validate `StoreProfiles.default_retail_location_id` |

### 10.2 SQL / ranh giới transaction

Tất cả trong **một** `@Transactional` của use-case checkout (isolation tối thiểu **READ COMMITTED**; nâng lên nếu OQ-6 chốt).

**Pseudocode — kiểm tra tổng tồn theo product (theo kho mặc định OQ-2):**

```sql
-- :pid = product_id; :loc = location_id (nullable theo OQ-2)
SELECT COALESCE(SUM(i.quantity), 0) AS avail
FROM Inventory i
WHERE i.product_id = :pid
  AND (CAST(:loc AS INTEGER) IS NULL OR i.location_id = :loc);
```

**Pseudocode — lock một dòng tồn để cập nhật (FEFO — OQ-3):**

```sql
SELECT i.id, i.quantity, i.batch_number, i.expiry_date
FROM Inventory i
WHERE i.product_id = :pid
  AND (CAST(:loc AS INTEGER) IS NULL OR i.location_id = :loc)
  AND i.quantity > 0
ORDER BY i.expiry_date NULLS LAST, i.id
FOR UPDATE;
```

**Pseudocode — sau insert `StockDispatches` (`:did`):**

```sql
UPDATE Inventory
SET quantity = quantity - :deduct
WHERE id = :inv_id;

INSERT INTO InventoryLogs (
  product_id, action_type, quantity_change, unit_id, user_id,
  dispatch_id, from_location_id, to_location_id, reference_note
) VALUES (
  :pid, 'OUTBOUND', -:deduct_base, :base_unit_id, :uid,
  :did, :loc_id, NULL, :note
);

UPDATE OrderDetails
SET dispatched_qty = quantity
WHERE id = :order_detail_id;
```

> Dev map `:deduct` / `:deduct_base` thống nhất đơn vị — **OQ-1**.

### 10.3 Index & hiệu năng

- Đã có: `idx_inv_product`, `idx_od_order`, `idx_sd_order`, `idx_il_dispatch`.  
- Nếu query allocation theo `product_id + location_id + expiry_date` nặng: cân nhắc composite index **`(product_id, location_id, expiry_date, id)`** — chỉ thêm sau `EXPLAIN` thực tế (ADR).

### 10.4 Kiểm chứng dữ liệu cho Tester

- **Given** `Inventory` product P tại location L có tổng 10 (base), **When** checkout 3 (base), **Then** tổng còn 7; `InventoryLogs` có 1+ dòng `OUTBOUND` với `dispatch_id` FK; `StockDispatches.order_id` = đơn mới; `OrderDetails.dispatched_qty` = `quantity`.  
- **Given** tồn 1, **When** checkout 2, **Then** **409**, không có `SalesOrders` mới.

---

## 11. Acceptance criteria (Given / When / Then)

```text
Given tồn kho đủ cho toàn bộ dòng trong giỏ (theo OQ-2, OQ-3)
When POST retail checkout hợp lệ
Then HTTP 201; đơn Retail tồn tại; tổng Inventory giảm đúng; dispatched_qty đầy đủ; có StockDispatches + InventoryLogs liên kết
```

```text
Given tồn không đủ cho ít nhất một sản phẩm
When POST retail checkout
Then HTTP 409; message tiếng Việt nghiệp vụ; không tạo đơn; không thay đổi Inventory
```

```text
Given đơn POS đã checkout thành công (đã có xuất kho)
When POST cancel đơn đó
Then HTTP 200; đơn chuyển Cancelled; tồn kho được hoàn đúng số lượng; dispatch bị huỷ; log có dòng đối ứng INBOUND
```

```text
Given người dùng đang xem danh sách sản phẩm
When họ F5 hoặc app invalidate query sau 201 checkout (FE)
Then cột Tồn kho phản ánh số mới từ API GET products
```

---

## 12. GAP & giả định

| GAP / Giả định | Tác động | Hành động đề xuất |
| :--- | :--- | :--- |
| Chưa có `API_Task090` riêng | FE/Bridge có thể nhầm “không đổi contract” | Cập nhật **`API_Task060`** + (tuỳ chọn) `BRIDGE_Task060` sau Approved |
| `locationId` không có trong body Task060 | Nếu Dev/FE hiểu nhầm sẽ gửi field thừa hoặc trừ sai kho | Đồng bộ `API_Task060` §6–§8: trừ tồn theo **StoreProfiles.default_retail_location_id** (OQ-2) |
| FE không invalidate `products/list` | UX vẫn thấy tồn cũ dù DB đúng | PR FE nhỏ: `POSCartPanel` `onSuccess` thêm invalidate |

---

## 13. PO sign-off (Approved — 29/04/2026)

- [x] Đã trả lời / đóng các **OQ** §4 (OQ-1…OQ-6)
- [x] Phạm vi In/Out đã đồng ý (POS checkout trừ tồn + tạo chứng từ xuất + log + dispatched_qty)
- [x] Đồng ý mã lỗi **409** khi thiếu tồn; đồng ý chiến lược lock `FOR UPDATE` (OQ-6)
- [x] Đồng ý cấu hình kho mặc định trong `StoreProfiles` (OQ-2)

**Chữ ký / nhãn PR:** `Approved` — 29/04/2026
