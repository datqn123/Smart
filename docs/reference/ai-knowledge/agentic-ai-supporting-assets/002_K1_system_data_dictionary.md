# K1 - System Data Dictionary

```yaml
asset_id: K1
version: "2026.06.07"
source_of_truth: hybrid
refresh_policy: on_schema_change
owner: ai_python
consumers: [intent, planner, sql_subagent, data_validator, answer_composer]
must_log_version_in_trace: true
```

## Purpose

Map toàn bộ bảng/cột DB sang ngôn ngữ nghiệp vụ tiếng Việt để intent/planner/sql_subagent không cần đoán schema.

---

## Tables

### products (Sản phẩm)
```yaml
table: products
label_vi: "Sản phẩm"
business_purpose: "Danh mục hàng hóa đang quản lý/bán. Mỗi sản phẩm có SKU duy nhất."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [product_count, active_product_count]
columns:
  - name: id            type: int       label_vi: "Mã SP"         sensitivity: internal_id  unit: null
  - name: category_id   type: int       label_vi: "Mã danh mục"   sensitivity: internal_id  unit: null   nullable: true
  - name: sku_code      type: varchar   label_vi: "Mã SKU"        sensitivity: normal        unit: null
  - name: barcode       type: varchar   label_vi: "Mã vạch"       sensitivity: normal        unit: null   nullable: true
  - name: name          type: varchar   label_vi: "Tên sản phẩm"  sensitivity: normal        unit: null
  - name: description   type: text      label_vi: "Mô tả"         sensitivity: normal        unit: null   nullable: true
  - name: weight        type: decimal   label_vi: "Trọng lượng"   sensitivity: normal        unit: gram   nullable: true
  - name: status        type: varchar   label_vi: "Trạng thái"    sensitivity: normal        unit: null   enum_ref: product_status
  - name: created_at    type: timestamp label_vi: "Ngày tạo"      sensitivity: normal        unit: null   timezone: Asia/Ho_Chi_Minh
  - name: updated_at    type: timestamp label_vi: "Cập nhật"      sensitivity: normal        unit: null   timezone: Asia/Ho_Chi_Minh
foreign_keys:
  - column: category_id  references: categories.id  join_label_vi: "Sản phẩm thuộc danh mục"
common_joins:
  - target: categories     sql: "products.category_id = categories.id"               use_when_vi: ["theo danh mục", "nhóm sản phẩm"]
  - target: productunits   sql: "productunits.product_id = products.id"              use_when_vi: ["đơn vị tính", "giá theo đơn vị"]
  - target: inventory      sql: "inventory.product_id = products.id"                 use_when_vi: ["tồn kho", "số lượng còn lại"]
  - target: orderdetails   sql: "orderdetails.product_id = products.id"              use_when_vi: ["đã bán", "doanh số sản phẩm"]
domain_cautions:
  - "Không có cost_price/sale_price trong bảng products; giá lấy từ productpricehistory JOIN productunits."
  - "Ảnh sản phẩm nằm ở productimages, products.image_url là ảnh chính dự phòng."
```

### productpricehistory (Lịch sử giá)
```yaml
table: productpricehistory
label_vi: "Lịch sử giá sản phẩm"
business_purpose: "Lưu giá vốn và giá bán theo đơn vị tính và thời điểm. Giá hiện tại = ORDER BY effective_date DESC LIMIT 1."
tenant_scoped: true
read_roles: [owner]
write_roles: []
known_metrics: [current_cost_price, current_sale_price, gross_margin]
columns:
  - name: id             type: int      label_vi: "Mã"           sensitivity: internal_id   unit: null
  - name: product_id     type: int      label_vi: "Mã SP"        sensitivity: internal_id   unit: null
  - name: unit_id        type: int      label_vi: "Mã đơn vị"   sensitivity: internal_id   unit: null
  - name: cost_price     type: decimal  label_vi: "Giá vốn"      sensitivity: cost_sensitive unit: VND
  - name: sale_price     type: decimal  label_vi: "Giá bán"      sensitivity: normal         unit: VND
  - name: effective_date type: date     label_vi: "Hiệu lực từ"  sensitivity: normal         unit: null timezone: date_only
foreign_keys:
  - column: product_id  references: products.id
  - column: unit_id     references: productunits.id
domain_cautions:
  - "cost_price chỉ owner được xem; staff không được query cột này."
  - "Giá hiện tại: JOIN ON product_id AND unit_id, ORDER BY effective_date DESC LIMIT 1 per (product, unit)."
```

### categories (Danh mục)
```yaml
table: categories
label_vi: "Danh mục sản phẩm"
business_purpose: "Phân loại sản phẩm theo cây phân cấp. parent_id=NULL là danh mục gốc."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [category_count, products_per_category]
columns:
  - name: id            type: int      label_vi: "Mã danh mục"  sensitivity: internal_id
  - name: category_code type: varchar  label_vi: "Mã code"       sensitivity: normal
  - name: name          type: varchar  label_vi: "Tên danh mục"  sensitivity: normal
  - name: description   type: text     label_vi: "Mô tả"         sensitivity: normal    nullable: true
  - name: parent_id     type: int      label_vi: "Danh mục cha"  sensitivity: internal_id nullable: true
  - name: sort_order    type: int      label_vi: "Thứ tự"        sensitivity: normal
  - name: status        type: varchar  label_vi: "Trạng thái"    sensitivity: normal    enum_ref: category_status
  - name: deleted_at    type: timestamp label_vi: "Xóa mềm"     sensitivity: normal    nullable: true
```

### inventory (Tồn kho)
```yaml
table: inventory
label_vi: "Tồn kho vật lý"
business_purpose: "Số lượng hàng tồn tại từng vị trí kho theo lô hàng. quantity luôn theo đơn vị cơ sở."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [total_quantity, low_stock_count, expiry_soon_count]
columns:
  - name: id           type: int      label_vi: "Mã tồn kho"     sensitivity: internal_id   unit: null
  - name: product_id   type: int      label_vi: "Mã SP"           sensitivity: internal_id   unit: null
  - name: location_id  type: int      label_vi: "Vị trí kho"      sensitivity: internal_id   unit: null
  - name: batch_number type: varchar  label_vi: "Số lô"           sensitivity: normal         unit: null  nullable: true
  - name: expiry_date  type: date     label_vi: "Hạn sử dụng"     sensitivity: normal         unit: null  nullable: true
  - name: quantity     type: int      label_vi: "Số lượng tồn"    sensitivity: normal         unit: base_unit  note: ">=0, đơn vị cơ sở"
  - name: min_quantity type: int      label_vi: "Mức cảnh báo tối thiểu" sensitivity: normal  unit: base_unit
  - name: updated_at   type: timestamp label_vi: "Cập nhật"       sensitivity: normal         unit: null  timezone: Asia/Ho_Chi_Minh
foreign_keys:
  - column: product_id   references: products.id
  - column: location_id  references: warehouselocations.id
common_joins:
  - target: products            sql: "inventory.product_id = products.id"                    use_when_vi: ["tên sản phẩm tồn kho", "tìm SP tồn nhiều/ít"]
  - target: warehouselocations  sql: "inventory.location_id = warehouselocations.id"         use_when_vi: ["vị trí kho", "kệ nào"]
domain_cautions:
  - "Tổng tồn = SUM(quantity) GROUP BY product_id khi sản phẩm ở nhiều vị trí/lô."
  - "LowStock: quantity <= min_quantity."
  - "Hết hạn sắp đến: expiry_date BETWEEN NOW() AND NOW() + INTERVAL '30 days'."
```

### warehouselocations (Vị trí kho)
```yaml
table: warehouselocations
label_vi: "Vị trí kho (kệ)"
business_purpose: "Kệ hàng trong kho. VD: WH01-A1."
tenant_scoped: false
read_roles: [owner, staff]
write_roles: []
columns:
  - name: id             type: int     label_vi: "Mã vị trí"    sensitivity: internal_id
  - name: warehouse_code type: varchar label_vi: "Mã kho"        sensitivity: normal
  - name: shelf_code     type: varchar label_vi: "Mã kệ"         sensitivity: normal
  - name: description    type: varchar label_vi: "Mô tả"         sensitivity: normal  nullable: true
  - name: capacity       type: decimal label_vi: "Sức chứa"      sensitivity: normal  unit: null    nullable: true
  - name: status         type: varchar label_vi: "Trạng thái"    sensitivity: normal  enum_ref: location_status
```

### salesorders (Đơn hàng bán)
```yaml
table: salesorders
label_vi: "Đơn hàng bán"
business_purpose: "Bảng chiều đơn bán; KHÔNG phải nguồn doanh thu đã ghi sổ (dùng financeledger). Chứa kênh bán, trạng thái, khách hàng."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [order_count_by_status, order_count_by_channel, avg_order_value]
columns:
  - name: id               type: int      label_vi: "Mã đơn"            sensitivity: internal_id
  - name: order_code       type: varchar  label_vi: "Số đơn hàng"        sensitivity: normal       note: "VD: SO-2026-0001"
  - name: customer_id      type: int      label_vi: "Khách hàng"         sensitivity: internal_id
  - name: user_id          type: int      label_vi: "Nhân viên xử lý"    sensitivity: internal_id
  - name: total_amount     type: decimal  label_vi: "Tổng tiền hàng"     sensitivity: normal        unit: VND
  - name: discount_amount  type: decimal  label_vi: "Chiết khấu"         sensitivity: normal        unit: VND
  - name: final_amount     type: decimal  label_vi: "Thành tiền"         sensitivity: normal        unit: VND  note: "Generated = total_amount - discount_amount"
  - name: status           type: varchar  label_vi: "Trạng thái đơn"     sensitivity: normal        enum_ref: order_status
  - name: order_channel    type: varchar  label_vi: "Kênh bán"           sensitivity: normal        enum_ref: order_channel
  - name: payment_status   type: varchar  label_vi: "Thanh toán"         sensitivity: normal        enum_ref: payment_status
  - name: created_at       type: timestamp label_vi: "Ngày tạo đơn"     sensitivity: normal        timezone: Asia/Ho_Chi_Minh
  - name: cancelled_at     type: timestamp label_vi: "Ngày hủy"         sensitivity: normal        nullable: true
foreign_keys:
  - column: customer_id  references: customers.id
  - column: user_id      references: users.id
common_joins:
  - target: financeledger  sql: "financeledger.reference_type='SalesOrder' AND financeledger.reference_id=salesorders.id"  use_when_vi: ["doanh thu theo kênh", "doanh thu theo khách"]
  - target: orderdetails   sql: "orderdetails.order_id = salesorders.id"   use_when_vi: ["chi tiết sản phẩm trong đơn"]
  - target: customers      sql: "salesorders.customer_id = customers.id"   use_when_vi: ["tên khách hàng"]
domain_cautions:
  - "Doanh thu tổng hợp lấy từ financeledger (SalesRevenue), không SUM(final_amount) trực tiếp."
  - "Dùng salesorders JOIN financeledger khi cần doanh thu theo kênh/khách."
```

### financeledger (Sổ cái tài chính)
```yaml
table: financeledger
label_vi: "Sổ cái tài chính"
business_purpose: "Nguồn CHUẨN (canonical) cho báo cáo tài chính. Mọi thu/chi ghi vào đây sau khi nghiệp vụ hoàn tất. amount dương=thu, âm=chi."
tenant_scoped: true
read_roles: [owner]
write_roles: []
known_metrics: [total_revenue, total_expense, net_cashflow, revenue_by_month]
columns:
  - name: id               type: int      label_vi: "Mã bút toán"      sensitivity: internal_id
  - name: transaction_date type: date     label_vi: "Ngày giao dịch"   sensitivity: normal        unit: null  timezone: date_only
  - name: transaction_type type: varchar  label_vi: "Loại giao dịch"   sensitivity: normal        enum_ref: finance_transaction_type
  - name: reference_type   type: varchar  label_vi: "Chứng từ nguồn"   sensitivity: normal        note: "SalesOrder | StockReceipt | CashTransaction"
  - name: reference_id     type: int      label_vi: "ID chứng từ"       sensitivity: internal_id  note: "Polymorphic FK; chỉ join khi reference_type khớp"
  - name: amount           type: decimal  label_vi: "Số tiền"           sensitivity: finance_sensitive unit: VND  note: "Dương=thu, Âm=chi"
  - name: description      type: text     label_vi: "Ghi chú"          sensitivity: normal        nullable: true
  - name: created_by       type: int      label_vi: "Người tạo"        sensitivity: internal_id
  - name: created_at       type: timestamp label_vi: "Thời điểm tạo"   sensitivity: normal        timezone: Asia/Ho_Chi_Minh
domain_cautions:
  - "Doanh thu: SUM(amount) WHERE transaction_type='SalesRevenue'. KHÔNG SUM toàn bộ ledger."
  - "Chi phí: SUM(amount) WHERE transaction_type IN ('PurchaseCost','OperatingExpense')."
  - "Lợi nhuận gộp = SalesRevenue + PurchaseCost (PurchaseCost thường âm)."
  - "Drill-down đơn hàng: JOIN salesorders ON reference_type='SalesOrder' AND reference_id=salesorders.id."
  - "Chỉ owner có quyền đọc; staff bị chặn ở guardrail."
```

### cashtransactions (Thu chi thủ công)
```yaml
table: cashtransactions
label_vi: "Thu chi tiền mặt thủ công"
business_purpose: "Phiếu thu/chi thủ công; khi Completed thì liên kết financeledger."
tenant_scoped: true
read_roles: [owner]
write_roles: []
columns:
  - name: id               type: int      label_vi: "Mã phiếu"         sensitivity: internal_id
  - name: transaction_code type: varchar  label_vi: "Số phiếu"          sensitivity: normal
  - name: direction        type: varchar  label_vi: "Thu/Chi"           sensitivity: finance_sensitive  enum_ref: cash_direction
  - name: amount           type: decimal  label_vi: "Số tiền"           sensitivity: finance_sensitive  unit: VND
  - name: category         type: varchar  label_vi: "Hạng mục"          sensitivity: normal
  - name: status           type: varchar  label_vi: "Trạng thái"        sensitivity: normal             enum_ref: cash_tx_status
  - name: transaction_date type: date     label_vi: "Ngày giao dịch"    sensitivity: normal             timezone: date_only
  - name: finance_ledger_id type: int     label_vi: "Liên kết sổ cái"   sensitivity: internal_id        nullable: true
```

### partnerDebts (Công nợ)
```yaml
table: partnerdebts
label_vi: "Sổ công nợ đối tác"
business_purpose: "Theo dõi công nợ khách hàng và nhà cung cấp. Số dư thực = total_amount - paid_amount."
tenant_scoped: true
read_roles: [owner]
write_roles: []
known_metrics: [customer_debt_total, supplier_debt_total, overdue_debt_count]
columns:
  - name: id           type: int      label_vi: "Mã công nợ"        sensitivity: internal_id
  - name: debt_code    type: varchar  label_vi: "Số công nợ"         sensitivity: normal
  - name: partner_type type: varchar  label_vi: "Loại đối tác"       sensitivity: normal           enum_ref: partner_type
  - name: customer_id  type: int      label_vi: "Khách hàng"         sensitivity: internal_id      nullable: true
  - name: supplier_id  type: int      label_vi: "Nhà cung cấp"       sensitivity: internal_id      nullable: true
  - name: total_amount type: decimal  label_vi: "Tổng nợ"            sensitivity: finance_sensitive unit: VND
  - name: paid_amount  type: decimal  label_vi: "Đã thanh toán"      sensitivity: finance_sensitive unit: VND
  - name: due_date     type: date     label_vi: "Hạn thanh toán"     sensitivity: normal            nullable: true   timezone: date_only
  - name: status       type: varchar  label_vi: "Trạng thái nợ"      sensitivity: normal            enum_ref: debt_status
foreign_keys:
  - column: customer_id  references: customers.id
  - column: supplier_id  references: suppliers.id
domain_cautions:
  - "Số dư còn lại = total_amount - paid_amount (không có cột riêng, tính tại query)."
  - "Quá hạn: due_date < CURRENT_DATE AND status='InDebt'."
  - "Chỉ owner xem công nợ; staff không có quyền."
```

### stockreceipts (Phiếu nhập kho)
```yaml
table: stockreceipts
label_vi: "Phiếu nhập kho"
business_purpose: "Chứng từ nhập hàng từ nhà cung cấp. Chỉ khi Approved mới cộng tồn và ghi financeledger."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [receipt_count_by_status, total_purchase_cost]
columns:
  - name: id            type: int      label_vi: "Mã phiếu"           sensitivity: internal_id
  - name: receipt_code  type: varchar  label_vi: "Số phiếu nhập"       sensitivity: normal        note: "VD: PN-2026-0001"
  - name: supplier_id   type: int      label_vi: "Nhà cung cấp"        sensitivity: internal_id
  - name: staff_id      type: int      label_vi: "Nhân viên nhập"       sensitivity: internal_id
  - name: receipt_date  type: date     label_vi: "Ngày nhập"           sensitivity: normal        timezone: date_only
  - name: status        type: varchar  label_vi: "Trạng thái"          sensitivity: normal        enum_ref: receipt_status
  - name: total_amount  type: decimal  label_vi: "Tổng tiền nhập"      sensitivity: cost_sensitive unit: VND
  - name: approved_by   type: int      label_vi: "Người duyệt"         sensitivity: internal_id   nullable: true
  - name: approved_at   type: timestamp label_vi: "Ngày duyệt"         sensitivity: normal        nullable: true
common_joins:
  - target: suppliers           sql: "stockreceipts.supplier_id = suppliers.id"          use_when_vi: ["nhà cung cấp nhập"]
  - target: stockreceiptdetails sql: "stockreceiptdetails.receipt_id = stockreceipts.id" use_when_vi: ["chi tiết sản phẩm nhập"]
```

### stockreceiptdetails (Chi tiết nhập)
```yaml
table: stockreceiptdetails
label_vi: "Chi tiết phiếu nhập"
business_purpose: "Từng dòng sản phẩm trong phiếu nhập. line_total = quantity × cost_price."
tenant_scoped: true
read_roles: [owner]
write_roles: []
columns:
  - name: receipt_id   type: int      label_vi: "Phiếu nhập"     sensitivity: internal_id
  - name: product_id   type: int      label_vi: "Sản phẩm"       sensitivity: internal_id
  - name: unit_id      type: int      label_vi: "Đơn vị"         sensitivity: internal_id
  - name: quantity     type: int      label_vi: "Số lượng"       sensitivity: normal         unit: unit
  - name: cost_price   type: decimal  label_vi: "Giá vốn nhập"   sensitivity: cost_sensitive unit: VND
  - name: line_total   type: decimal  label_vi: "Thành tiền dòng" sensitivity: cost_sensitive unit: VND  note: "Generated = quantity*cost_price"
  - name: batch_number type: varchar  label_vi: "Số lô"          sensitivity: normal         nullable: true
  - name: expiry_date  type: date     label_vi: "Hạn sử dụng"    sensitivity: normal         nullable: true
```

### orderdetails (Chi tiết đơn hàng)
```yaml
table: orderdetails
label_vi: "Chi tiết đơn hàng"
business_purpose: "Từng dòng sản phẩm trong đơn bán. price_at_time không thay đổi khi giá thị trường đổi."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [top_products_by_quantity, top_products_by_revenue, product_sales_volume]
columns:
  - name: order_id       type: int      label_vi: "Mã đơn"              sensitivity: internal_id
  - name: product_id     type: int      label_vi: "Sản phẩm"            sensitivity: internal_id
  - name: unit_id        type: int      label_vi: "Đơn vị"              sensitivity: internal_id
  - name: quantity       type: int      label_vi: "Số lượng bán"        sensitivity: normal        unit: unit
  - name: price_at_time  type: decimal  label_vi: "Giá tại thời điểm"   sensitivity: normal        unit: VND
  - name: line_total     type: decimal  label_vi: "Thành tiền dòng"     sensitivity: normal        unit: VND  note: "Generated"
  - name: dispatched_qty type: int      label_vi: "Đã xuất kho"         sensitivity: normal        unit: unit
common_joins:
  - target: products   sql: "orderdetails.product_id = products.id"  use_when_vi: ["top sản phẩm bán chạy", "doanh số từng SP"]
  - target: salesorders sql: "orderdetails.order_id = salesorders.id" use_when_vi: ["đơn hàng tương ứng"]
```

### customers (Khách hàng)
```yaml
table: customers
label_vi: "Khách hàng"
business_purpose: "Danh sách khách hàng. Tổng chi tiêu tính qua SUM(salesorders.final_amount) không phải cột riêng."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
known_metrics: [customer_count, top_customers_by_spending]
columns:
  - name: id             type: int      label_vi: "Mã KH"           sensitivity: internal_id
  - name: customer_code  type: varchar  label_vi: "Mã code KH"       sensitivity: normal
  - name: name           type: varchar  label_vi: "Tên khách hàng"   sensitivity: pii_name
  - name: phone          type: varchar  label_vi: "Điện thoại"       sensitivity: pii_phone
  - name: email          type: varchar  label_vi: "Email"            sensitivity: pii_email  nullable: true
  - name: loyalty_points type: int      label_vi: "Điểm tích lũy"    sensitivity: normal
  - name: status         type: varchar  label_vi: "Trạng thái"       sensitivity: normal      enum_ref: customer_status
  - name: deleted_at     type: timestamp label_vi: "Xóa mềm"        sensitivity: normal      nullable: true
domain_cautions:
  - "PII: không đưa phone/email vào LLM prompt trừ khi user hỏi rõ và role là owner."
  - "Khách đã xóa mềm: deleted_at IS NOT NULL, loại bỏ khỏi mặc định."
```

### suppliers (Nhà cung cấp)
```yaml
table: suppliers
label_vi: "Nhà cung cấp"
business_purpose: "Danh sách nhà cung cấp hàng hóa."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: id            type: int      label_vi: "Mã NCC"          sensitivity: internal_id
  - name: supplier_code type: varchar  label_vi: "Mã code NCC"      sensitivity: normal
  - name: name          type: varchar  label_vi: "Tên nhà cung cấp" sensitivity: normal
  - name: contact_person type: varchar label_vi: "Người liên hệ"    sensitivity: pii_name    nullable: true
  - name: phone         type: varchar  label_vi: "Điện thoại"       sensitivity: pii_phone   nullable: true
  - name: tax_code      type: varchar  label_vi: "Mã số thuế"       sensitivity: normal      nullable: true
  - name: status        type: varchar  label_vi: "Trạng thái"       sensitivity: normal      enum_ref: supplier_status
```

### stockdispatches (Phiếu xuất kho)
```yaml
table: stockdispatches
label_vi: "Phiếu xuất kho"
business_purpose: "Phiếu xuất hàng gắn với đơn bán. Xuất hoàn tất khi status=Full."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: dispatch_code  type: varchar   label_vi: "Số phiếu xuất"   sensitivity: normal   note: "VD: PX-2026-0001"
  - name: order_id       type: int       label_vi: "Đơn hàng"        sensitivity: internal_id
  - name: dispatch_date  type: date      label_vi: "Ngày xuất"       sensitivity: normal   timezone: date_only
  - name: status         type: varchar   label_vi: "Trạng thái"      sensitivity: normal   enum_ref: dispatch_status
common_joins:
  - target: salesorders  sql: "stockdispatches.order_id = salesorders.id"  use_when_vi: ["xuất kho theo đơn"]
```

### inventorylogs (Nhật ký biến động kho)
```yaml
table: inventorylogs
label_vi: "Nhật ký biến động kho"
business_purpose: "Lịch sử từng thay đổi tồn kho: nhập/xuất/điều chuyển/điều chỉnh. quantity_change dương=nhập, âm=xuất."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: product_id      type: int       label_vi: "Sản phẩm"          sensitivity: internal_id
  - name: action_type     type: varchar   label_vi: "Loại hành động"     sensitivity: normal        enum_ref: inventory_action_type
  - name: quantity_change type: int       label_vi: "Thay đổi số lượng"  sensitivity: normal        unit: base_unit  note: "Dương=nhập, Âm=xuất"
  - name: created_at      type: timestamp label_vi: "Thời điểm"         sensitivity: normal        timezone: Asia/Ho_Chi_Minh
```

### productunits (Đơn vị tính)
```yaml
table: productunits
label_vi: "Đơn vị tính sản phẩm"
business_purpose: "Đơn vị tính và hệ số quy đổi. is_base_unit=TRUE là đơn vị gốc. VD 1 Thùng = 24 Lon."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: unit_name       type: varchar  label_vi: "Tên đơn vị"       sensitivity: normal
  - name: conversion_rate type: decimal  label_vi: "Hệ số quy đổi"    sensitivity: normal   note: "Số đơn vị cơ sở trong 1 đơn vị này"
  - name: is_base_unit    type: boolean  label_vi: "Đơn vị gốc"       sensitivity: normal
```

### inventoryauditsessions (Phiên kiểm kê)
```yaml
table: inventoryauditsessions
label_vi: "Phiên kiểm kê kho"
business_purpose: "Quản lý đợt kiểm kê tồn kho thực tế so với hệ thống."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: audit_code   type: varchar   label_vi: "Mã phiên kiểm"   sensitivity: normal
  - name: title        type: varchar   label_vi: "Tiêu đề"          sensitivity: normal
  - name: audit_date   type: date      label_vi: "Ngày kiểm"        sensitivity: normal   timezone: date_only
  - name: status       type: varchar   label_vi: "Trạng thái"       sensitivity: normal   enum_ref: audit_status
  - name: completed_at type: timestamp label_vi: "Hoàn thành lúc"   sensitivity: normal   nullable: true
```

### ai_catalog_draft (Nháp catalog AI)
```yaml
table: ai_catalog_draft
label_vi: "Nháp nhập liệu catalog (AI HITL)"
business_purpose: "Nháp AI sinh ra chờ user xác nhận trước khi commit vào catalog. Không dùng cho báo cáo dữ liệu thực."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: id              type: uuid     label_vi: "Mã nháp"         sensitivity: internal_id
  - name: entity_type     type: varchar  label_vi: "Loại thực thể"   sensitivity: normal       enum_ref: catalog_draft_entity_type
  - name: status          type: varchar  label_vi: "Trạng thái nháp" sensitivity: normal       enum_ref: draft_status
  - name: payload         type: jsonb    label_vi: "Dữ liệu nháp"    sensitivity: normal
  - name: expires_at      type: timestamp label_vi: "Hết hạn lúc"   sensitivity: normal
domain_cautions:
  - "Chỉ dùng khi AI tạo nháp catalog; không join vào báo cáo kinh doanh."
```

### ai_inventory_draft (Nháp chứng từ kho AI)
```yaml
table: ai_inventory_draft
label_vi: "Nháp chứng từ kho (AI HITL)"
business_purpose: "Nháp phiếu nhập/xuất kho do AI sinh, chờ xác nhận HITL. Chỉ entity_type='stock_receipt' hiện tại."
tenant_scoped: true
read_roles: [owner, staff]
write_roles: []
columns:
  - name: entity_type  type: varchar   label_vi: "Loại chứng từ"   sensitivity: normal  enum_ref: inventory_draft_entity_type
  - name: status       type: varchar   label_vi: "Trạng thái nháp" sensitivity: normal  enum_ref: draft_status
  - name: payload      type: jsonb     label_vi: "Dữ liệu nháp"    sensitivity: normal
  - name: expires_at   type: timestamp label_vi: "Hết hạn lúc"    sensitivity: normal
```

---

## Sensitivity Classification

| Level | Ý nghĩa | Xem được |
|---|---|---|
| `normal` | Dữ liệu bình thường | owner + staff |
| `internal_id` | Khóa nội bộ, không hiển thị với user | Không show trong answer |
| `cost_sensitive` | Giá vốn, chi phí | Chỉ owner |
| `finance_sensitive` | Tài chính: doanh thu, lợi nhuận, dòng tiền, công nợ | Chỉ owner |
| `pii_name / pii_phone / pii_email` | Thông tin cá nhân | Chỉ hiển thị khi user hỏi rõ |
