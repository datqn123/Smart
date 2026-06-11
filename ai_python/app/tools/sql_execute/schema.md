# DB Schema ERP — Tham chiếu bắt buộc cho sql_execute

## QUY TẮC CỐT LÕI — ĐỌC TRƯỚC KHI SINH SQL

### Tồn kho
- Tồn kho nằm ở bảng `inventory.quantity` — KHÔNG có cột tồn trong bảng `products`
- "sản phẩm còn nhiều nhất / tồn kho / hết hàng / còn bao nhiêu" → JOIN `inventory` theo `product_id`
- `inventory.min_quantity` = ngưỡng cảnh báo hết hàng

### Doanh thu / Tài chính
- Doanh thu chính thức: `financeledger WHERE transaction_type = 'SalesRevenue'`, tổng = `SUM(amount)`
- `transaction_type`: `SalesRevenue` (doanh thu), `PurchaseCost` (chi phí mua hàng), `OperatingExpense` (chi phí vận hành), `Refund` (hoàn trả)
- `amount` dương = thu, âm = chi
- KHÔNG dùng `salesorders.final_amount` để tính tổng doanh thu đã hạch toán
- Phân tích theo kênh/khách: JOIN `financeledger fl JOIN salesorders so ON fl.reference_type='SalesOrder' AND fl.reference_id=so.id`

### Join phiếu xuất
- Chuỗi đúng: `salesorders → stockdispatches (order_id) → stockdispatch_lines (dispatch_id)`
- `stockdispatch_lines.dispatch_id` là FK của `stockdispatches.id`, KHÔNG phải `salesorders.id`

---

## Bảng và cột

### inventory — Tồn kho vật lý theo lô
```
id, product_id (FK products), location_id (FK warehouselocations),
batch_number, expiry_date, quantity (SL tồn đơn vị cơ sở), min_quantity, updated_at
```

### products — Sản phẩm master
```
id, sku_code, barcode, name, category_id (FK categories),
image_url, description, weight, status (Active|Inactive), created_at, updated_at
```
Không có cột giá hay tồn — giá ở `productpricehistory`, tồn ở `inventory`.

### financeledger — Sổ cái (nguồn chính tài chính)
```
id, transaction_date, transaction_type (SalesRevenue|PurchaseCost|OperatingExpense|Refund),
reference_type, reference_id, amount (+ thu / - chi), description, fund_id (FK cash_funds),
created_by (FK users), created_at
```

### salesorders — Đơn hàng bán (dimension)
```
id, order_code, customer_id (FK customers), user_id (FK users),
total_amount, discount_amount, final_amount (generated=total-discount),
status, order_channel (Retail|Wholesale|Return),
payment_status (Paid|Unpaid|Partial), voucher_id,
created_at, cancelled_at, cancelled_by
```

### orderdetails — Dòng đơn hàng
```
id, order_id (FK salesorders), product_id (FK products), unit_id (FK productunits),
quantity, price_at_time, line_total (generated), dispatched_qty, created_at
```

### customers — Khách hàng
```
id, customer_code, name, phone, email, address, loyalty_points,
status (Active|Inactive), created_at, updated_at, deleted_at
```

### suppliers — Nhà cung cấp
```
id, supplier_code, name, contact_person, phone, email, tax_code,
status (Active|Inactive), created_at, updated_at
```

### categories — Danh mục sản phẩm
```
id, category_code, name, description, parent_id (tự tham chiếu), sort_order,
status (Active|Inactive), created_at, updated_at, deleted_at
```

### stockreceipts — Phiếu nhập kho
```
id, receipt_code, supplier_id (FK suppliers), staff_id (FK users),
receipt_date, status (Draft|Pending|Approved|Rejected),
total_amount, notes, approved_by (FK users), approved_at, created_at
```

### stockreceiptdetails — Dòng phiếu nhập
```
id, receipt_id (FK stockreceipts), product_id (FK products), unit_id (FK productunits),
quantity, cost_price, batch_number, expiry_date, line_total (generated), created_at
```

### stockdispatches — Phiếu xuất kho
```
id, dispatch_code, order_id (FK salesorders, nullable), user_id (FK users),
dispatch_date, status (Pending|Full|Partial), notes,
deleted_at, deleted_by_user_id, delete_reason, created_at
```

### stockdispatch_lines — Dòng phiếu xuất
```
id, dispatch_id (FK stockdispatches.id), inventory_id (FK inventory),
quantity, unit_price_snapshot
```

### inventorylogs — Nhật ký biến động tồn
```
id, product_id (FK products), action_type (INBOUND|OUTBOUND|TRANSFER|ADJUSTMENT),
quantity_change (+ nhập / - xuất), unit_id, user_id,
dispatch_id (FK stockdispatches), receipt_id (FK stockreceipts),
from_location_id, to_location_id, reference_note, created_at
```

### cashtransactions — Phiếu thu chi
```
id, transaction_code, direction (Income|Expense), amount,
category, description, payment_method, status (Pending|Completed|Cancelled),
transaction_date, fund_id (FK cash_funds), finance_ledger_id (FK financeledger),
created_by (FK users), created_at
```

### partnerdebts — Công nợ đối tác
```
id, debt_code, partner_type (Customer|Supplier),
customer_id (FK customers), supplier_id (FK suppliers),
total_amount, paid_amount (remaining = total_amount - paid_amount),
status (InDebt|Cleared), due_date, notes, created_at
```

### users — Tài khoản hệ thống
```
id, username, full_name, email, phone, role_id (FK roles),
status (Active|Locked), last_login, created_at
```

### productunits — Đơn vị quy đổi
```
id, product_id (FK products), unit_name (Thùng|Lốc|Lon|Gói…),
conversion_rate (hệ số về base unit), is_base_unit, created_at
```

### productpricehistory — Lịch sử giá
```
id, product_id (FK products), unit_id (FK productunits),
cost_price, sale_price, effective_date, created_at
```

### warehouselocations — Vị trí kho
```
id, warehouse_code, shelf_code, description, capacity,
status (Active|Maintenance|Inactive), created_at
```

### cash_funds — Quỹ tiền
```
id, code, name, is_default, is_active, created_at
```

### alertsettings — Cấu hình cảnh báo
```
id, owner_id (FK users), alert_type (LowStock|ExpiryDate|…),
threshold_value, channel (App|Email|SMS|Zalo),
frequency (Realtime|Daily|Weekly), is_enabled, created_at
```

### vouchers — Mã khuyến mãi
```
id, code, name, discount_type (Percent|FixedAmount), discount_value,
is_active, valid_from, valid_to, used_count, max_uses (NULL=vô hạn)
```

---

## Mẫu join thường dùng

```sql
-- Sản phẩm tồn nhiều nhất
SELECT p.name, SUM(i.quantity) AS tong_ton
FROM products p JOIN inventory i ON i.product_id = p.id
WHERE p.status = 'Active'
GROUP BY p.id, p.name
ORDER BY tong_ton DESC LIMIT 10;

-- Doanh thu theo tháng
SELECT DATE_TRUNC('month', fl.transaction_date) AS thang,
       SUM(fl.amount) AS doanh_thu
FROM financeledger fl
WHERE fl.transaction_type = 'SalesRevenue'
GROUP BY 1 ORDER BY 1 DESC LIMIT 12;

-- Doanh thu theo kênh bán
SELECT so.order_channel, SUM(fl.amount) AS doanh_thu
FROM financeledger fl
JOIN salesorders so ON fl.reference_type = 'SalesOrder'
                   AND fl.reference_id = so.id
WHERE fl.transaction_type = 'SalesRevenue'
GROUP BY so.order_channel;

-- Tồn sắp hết (dưới ngưỡng cảnh báo)
SELECT p.name, i.quantity, i.min_quantity
FROM inventory i JOIN products p ON i.product_id = p.id
WHERE i.quantity < i.min_quantity AND p.status = 'Active'
ORDER BY (i.quantity - i.min_quantity) ASC LIMIT 20;

-- Công nợ còn lại của khách hàng
SELECT c.name, pd.total_amount - pd.paid_amount AS con_lai
FROM partnerdebts pd JOIN customers c ON pd.customer_id = c.id
WHERE pd.partner_type = 'Customer' AND pd.status = 'InDebt'
ORDER BY con_lai DESC LIMIT 20;
```
