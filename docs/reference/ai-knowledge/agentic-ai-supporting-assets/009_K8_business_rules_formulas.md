# K8 - Business Rules And Formulas

```yaml
asset_id: K8
version: "2026.06.07"
source_of_truth: manual
refresh_policy: manual_review
consumers: [data_validator, sql_subagent, answer_composer]
must_log_version_in_trace: true
```

## Purpose

Định nghĩa cách tính các chỉ số kinh doanh để sql_subagent sinh đúng SQL và data_validator biết cái gì là "hợp lý".

---

## Metrics

### sales_revenue — Doanh thu bán hàng
```yaml
id: sales_revenue
label_vi: "Doanh thu bán hàng"
definition_vi: "Tổng tiền ghi nhận từ giao dịch bán hàng đã hạch toán vào sổ cái."
source_table: financeledger
preferred_formula: "SUM(amount) WHERE transaction_type = 'SalesRevenue'"
required_filters: [time_range]
fallback: null
sensitivity: finance_sensitive
visible_roles: [owner]
validation:
  min_value: 0
  allow_zero: true
  allow_null: true    # null khi chưa có giao dịch trong kỳ
  suspicious_if: "giá trị âm"
caution: "KHÔNG dùng SUM(salesorders.final_amount) — salesorders không phải nguồn chuẩn doanh thu đã ghi sổ"
```

### purchase_cost — Giá vốn hàng mua
```yaml
id: purchase_cost
label_vi: "Giá vốn hàng mua / Chi phí nhập hàng"
definition_vi: "Tổng chi phí mua hàng đã nhập kho và ghi vào sổ cái."
source_table: financeledger
preferred_formula: "SUM(amount) WHERE transaction_type = 'PurchaseCost'"
required_filters: [time_range]
sensitivity: finance_sensitive
visible_roles: [owner]
validation:
  note: "amount thường âm (chi ra) → SUM trả số âm. Khi hiển thị dùng ABS()"
  suspicious_if: "giá trị dương lớn (ngược chiều thông thường)"
```

### operating_expense — Chi phí vận hành
```yaml
id: operating_expense
label_vi: "Chi phí vận hành"
definition_vi: "Các khoản chi vận hành không phải giá vốn hàng hóa."
source_table: financeledger
preferred_formula: "SUM(ABS(amount)) WHERE transaction_type = 'OperatingExpense'"
required_filters: [time_range]
sensitivity: finance_sensitive
visible_roles: [owner]
```

### total_expense — Tổng chi phí
```yaml
id: total_expense
label_vi: "Tổng chi phí"
definition_vi: "Tổng mọi khoản chi = PurchaseCost + OperatingExpense + Refund."
source_table: financeledger
preferred_formula: "SUM(ABS(amount)) WHERE transaction_type IN ('PurchaseCost','OperatingExpense','Refund') AND amount < 0"
required_filters: [time_range]
sensitivity: finance_sensitive
visible_roles: [owner]
```

### gross_profit — Lợi nhuận gộp
```yaml
id: gross_profit
label_vi: "Lợi nhuận gộp"
definition_vi: "Doanh thu bán hàng trừ giá vốn hàng mua trong kỳ."
source_table: financeledger
preferred_formula: |
  SUM(CASE WHEN transaction_type = 'SalesRevenue' THEN amount ELSE 0 END)
  + SUM(CASE WHEN transaction_type = 'PurchaseCost' THEN amount ELSE 0 END)
  (vì PurchaseCost thường âm nên dùng dấu cộng)
required_filters: [time_range]
sensitivity: finance_sensitive
visible_roles: [owner]
validation:
  allow_negative: true   # Lỗ là hợp lệ
  suspicious_if: "lớn hơn doanh thu (không thể)"
```

### net_cashflow — Dòng tiền thuần
```yaml
id: net_cashflow
label_vi: "Dòng tiền thuần"
definition_vi: "Tổng thu trừ tổng chi trong kỳ (SUM toàn bộ amount trong financeledger)."
source_table: financeledger
preferred_formula: "SUM(amount) — tổng tất cả transaction_type"
required_filters: [time_range]
sensitivity: finance_sensitive
visible_roles: [owner]
validation:
  allow_negative: true
```

### inventory_on_hand — Tồn kho hiện tại
```yaml
id: inventory_on_hand
label_vi: "Tồn kho hiện tại"
definition_vi: "Tổng số lượng hàng đang có trong kho theo đơn vị cơ sở."
source_table: inventory
preferred_formula: "SUM(quantity) GROUP BY product_id"
aggregation_note: "JOIN với products và GROUP BY product_id khi cần tổng theo SP"
validation:
  allow_negative: false
  suspicious_if: "quantity < 0 (vi phạm CHECK constraint — không nên xảy ra)"
caution: "quantity luôn theo đơn vị cơ sở (is_base_unit=TRUE)"
```

### low_stock — Tồn kho dưới mức cảnh báo
```yaml
id: low_stock
label_vi: "Hàng sắp hết / tồn thấp"
definition_vi: "Sản phẩm có SUM(quantity) <= MAX(min_quantity) theo vị trí."
source_table: inventory
preferred_formula: |
  SELECT ... FROM inventory GROUP BY product_id
  HAVING SUM(quantity) <= MAX(min_quantity)
validation:
  note: "min_quantity = 0 nghĩa là chưa cấu hình cảnh báo, bỏ qua sản phẩm này"
```

### expiry_soon — Sắp hết hạn
```yaml
id: expiry_soon
label_vi: "Hàng sắp hết hạn"
definition_vi: "Hàng có expiry_date trong vòng N ngày tới (mặc định N=30)."
source_table: inventory
preferred_formula: "WHERE expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL ':N days' AND quantity > 0"
default_window_days: 30
```

### customer_debt_balance — Công nợ khách hàng
```yaml
id: customer_debt_balance
label_vi: "Công nợ khách hàng còn lại"
definition_vi: "Tổng số tiền khách hàng còn nợ chưa thanh toán."
source_table: partnerdebts
preferred_formula: "SUM(total_amount - paid_amount) WHERE partner_type='Customer' AND status='InDebt'"
sensitivity: finance_sensitive
visible_roles: [owner]
validation:
  min_value: 0
  note: "remaining_debt = total_amount - paid_amount (không có cột sẵn)"
```

### supplier_debt_balance — Công nợ nhà cung cấp
```yaml
id: supplier_debt_balance
label_vi: "Công nợ nhà cung cấp còn lại"
definition_vi: "Tổng số tiền cửa hàng còn nợ nhà cung cấp."
source_table: partnerdebts
preferred_formula: "SUM(total_amount - paid_amount) WHERE partner_type='Supplier' AND status='InDebt'"
sensitivity: finance_sensitive
visible_roles: [owner]
```

### top_products_by_quantity — Sản phẩm bán chạy theo số lượng
```yaml
id: top_products_by_quantity
label_vi: "Top sản phẩm bán chạy (số lượng)"
definition_vi: "Xếp hạng sản phẩm theo tổng số lượng bán trong orderdetails của đơn không bị hủy."
source_table: orderdetails
preferred_formula: |
  SELECT product_id, SUM(quantity) AS total_qty
  FROM orderdetails
  JOIN salesorders ON order_id = salesorders.id
  WHERE salesorders.status != 'Cancelled'
    AND [time_filter on salesorders.created_at]
  GROUP BY product_id ORDER BY total_qty DESC
  LIMIT :n
required_filters: [time_range]
```

### top_products_by_revenue — Sản phẩm bán chạy theo doanh thu
```yaml
id: top_products_by_revenue
label_vi: "Top sản phẩm theo doanh thu"
definition_vi: "Xếp hạng sản phẩm theo doanh thu dòng (line_total) trong orderdetails."
source_table: orderdetails
preferred_formula: |
  SELECT product_id, SUM(line_total) AS total_revenue
  FROM orderdetails
  JOIN salesorders ON order_id = salesorders.id
  WHERE salesorders.status != 'Cancelled'
    AND [time_filter]
  GROUP BY product_id ORDER BY total_revenue DESC
  LIMIT :n
sensitivity: finance_sensitive
visible_roles: [owner]
caution: "Doanh thu dòng (line_total) khác doanh thu đã ghi sổ (financeledger). Dùng cho phân tích sản phẩm."
```

### draft_validity — Hợp lệ nháp
```yaml
id: draft_validity_catalog
label_vi: "Hợp lệ nháp catalog"
rules:
  - "sku_code bắt buộc, không trùng với products đang active"
  - "product_name bắt buộc, không rỗng"
  - "sale_price nếu có: >= 0"
  - "cost_price nếu có: >= 0 và < sale_price (cảnh báo nếu ngược)"
  - "category_id nếu có: phải tồn tại trong categories đang active"

id: draft_validity_inventory
label_vi: "Hợp lệ nháp phiếu nhập"
rules:
  - "product_id bắt buộc, phải tồn tại trong products"
  - "quantity bắt buộc, > 0"
  - "warehouse_id bắt buộc, phải tồn tại trong warehouselocations"
  - "unit_cost nếu có: >= 0"
```

---

## Data Validator Rules

| Rule | Điều kiện | Hành động |
|---|---|---|
| Tồn kho âm | quantity < 0 | Báo lỗi — không hợp lệ về nghiệp vụ |
| Doanh thu âm | SUM(SalesRevenue) < 0 | Cảnh báo — hỏi lại hoặc report như lỗi |
| Lợi nhuận > Doanh thu | gross_profit > sales_revenue | Cảnh báo — logic không thể |
| Công nợ âm | paid_amount > total_amount | Lỗi — vi phạm constraint DB |
| Kết quả rỗng | 0 rows và query hợp lệ | Không phải lỗi — answer "không có dữ liệu" |
| NULL metric | SUM trả NULL | Tương đương 0 — dùng COALESCE(SUM(...),0) |
| Thời gian tương lai | transaction_date > CURRENT_DATE | Cảnh báo trong answer |

## Normalized Intent Keys (dùng cho K15)

```yaml
intent_keys:
  - revenue_by_period
  - revenue_by_channel
  - expense_by_period
  - gross_profit_by_period
  - net_cashflow_by_period
  - inventory_on_hand_all
  - inventory_on_hand_by_product
  - inventory_on_hand_by_category
  - low_stock_list
  - expiry_soon_list
  - top_products_by_quantity
  - top_products_by_revenue
  - customer_debt_balance
  - supplier_debt_balance
  - overdue_debt_list
  - order_count_by_status
  - order_count_by_channel
  - receipt_pending_list
  - stock_movement_by_product
  - catalog_draft_create
  - inventory_draft_create
  - chat_greeting
  - out_of_scope
```
