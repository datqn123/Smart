# K3 - Enum And Status Dictionary

```yaml
asset_id: K3
version: "2026.06.07"
source_of_truth: hybrid
refresh_policy: on_schema_change
consumers: [sql_subagent, data_validator, answer_composer]
must_log_version_in_trace: true
```

## Purpose

Liệt kê toàn bộ giá trị enum thực trong DB kèm nhãn tiếng Việt và alias. SQL phải dùng mã thô (raw code); answer_composer render nhãn Việt.

---

## Enums

### order_status — salesorders.status
```json
{
  "enum": "order_status",
  "table": "salesorders", "column": "status",
  "values": {
    "Pending":    { "label_vi": "Chờ xử lý",     "aliases_vi": ["mới tạo", "chưa duyệt"],      "terminal": false },
    "Processing": { "label_vi": "Đang xử lý",    "aliases_vi": ["đang làm", "đang thực hiện"], "terminal": false },
    "Partial":    { "label_vi": "Xuất một phần", "aliases_vi": ["xuất chưa đủ", "thiếu hàng"],"terminal": false },
    "Shipped":    { "label_vi": "Đã giao vận",   "aliases_vi": ["đang giao", "đã ship"],        "terminal": false },
    "Delivered":  { "label_vi": "Đã giao thành công", "aliases_vi": ["hoàn thành", "đã nhận"], "terminal": true  },
    "Cancelled":  { "label_vi": "Đã hủy",        "aliases_vi": ["hủy đơn", "bị hủy"],          "terminal": true  }
  }
}
```

### payment_status — salesorders.payment_status
```json
{
  "enum": "payment_status",
  "table": "salesorders", "column": "payment_status",
  "values": {
    "Paid":    { "label_vi": "Đã thanh toán", "aliases_vi": ["đã trả", "thanh toán xong"],  "terminal": true  },
    "Unpaid":  { "label_vi": "Chưa thanh toán","aliases_vi": ["chưa trả", "còn nợ"],        "terminal": false },
    "Partial": { "label_vi": "Trả một phần",  "aliases_vi": ["thanh toán một phần", "trả thiếu"], "terminal": false }
  }
}
```

### order_channel — salesorders.order_channel
```json
{
  "enum": "order_channel",
  "table": "salesorders", "column": "order_channel",
  "values": {
    "Retail":    { "label_vi": "Bán lẻ",   "aliases_vi": ["lẻ", "POS", "tại quầy"] },
    "Wholesale": { "label_vi": "Bán sỉ",   "aliases_vi": ["sỉ", "đại lý"]           },
    "Return":    { "label_vi": "Trả hàng", "aliases_vi": ["hoàn hàng", "đổi trả"]   }
  }
}
```

### receipt_status — stockreceipts.status
```json
{
  "enum": "receipt_status",
  "table": "stockreceipts", "column": "status",
  "values": {
    "Draft":    { "label_vi": "Nháp",         "aliases_vi": ["chưa gửi"],        "terminal": false },
    "Pending":  { "label_vi": "Chờ duyệt",    "aliases_vi": ["đang xét duyệt"],  "terminal": false },
    "Approved": { "label_vi": "Đã duyệt",     "aliases_vi": ["duyệt xong", "đã nhập kho"], "terminal": true,
                  "note": "Chỉ Approved mới cộng tồn kho và ghi financeledger" },
    "Rejected": { "label_vi": "Bị từ chối",   "aliases_vi": ["bị từ chối", "không duyệt"], "terminal": true  }
  }
}
```

### dispatch_status — stockdispatches.status
```json
{
  "enum": "dispatch_status",
  "table": "stockdispatches", "column": "status",
  "values": {
    "Pending":   { "label_vi": "Chờ xuất",          "aliases_vi": ["chưa xuất"],      "terminal": false },
    "Full":      { "label_vi": "Xuất đủ",            "aliases_vi": ["đã xuất hết"],    "terminal": true  },
    "Partial":   { "label_vi": "Xuất một phần",      "aliases_vi": ["xuất chưa đủ"],   "terminal": false },
    "Cancelled": { "label_vi": "Đã hủy phiếu xuất", "aliases_vi": ["hủy xuất kho"],   "terminal": true  }
  }
}
```

### finance_transaction_type — financeledger.transaction_type
```json
{
  "enum": "finance_transaction_type",
  "table": "financeledger", "column": "transaction_type",
  "values": {
    "SalesRevenue":     { "label_vi": "Doanh thu bán hàng", "aliases_vi": ["thu bán", "doanh thu"],      "amount_sign": "positive" },
    "PurchaseCost":     { "label_vi": "Giá vốn hàng mua",  "aliases_vi": ["chi nhập hàng", "giá nhập"], "amount_sign": "negative" },
    "OperatingExpense": { "label_vi": "Chi phí vận hành",  "aliases_vi": ["chi phí", "vận hành"],        "amount_sign": "negative" },
    "Refund":           { "label_vi": "Hoàn tiền",         "aliases_vi": ["trả lại tiền", "refund"],     "amount_sign": "negative" }
  },
  "usage_note": "Doanh thu thuần = SUM(amount) WHERE transaction_type='SalesRevenue'. Lợi nhuận gộp = SalesRevenue + PurchaseCost (PurchaseCost thường âm)."
}
```

### cash_direction — cashtransactions.direction
```json
{
  "enum": "cash_direction",
  "table": "cashtransactions", "column": "direction",
  "values": {
    "Income":  { "label_vi": "Thu tiền", "aliases_vi": ["thu", "nhận tiền"] },
    "Expense": { "label_vi": "Chi tiền", "aliases_vi": ["chi", "xuất tiền"] }
  }
}
```

### cash_tx_status — cashtransactions.status
```json
{
  "enum": "cash_tx_status",
  "table": "cashtransactions", "column": "status",
  "values": {
    "Pending":   { "label_vi": "Chờ xử lý",    "terminal": false },
    "Completed": { "label_vi": "Đã hoàn tất",   "terminal": true,
                   "note": "Chỉ Completed mới liên kết financeledger" },
    "Cancelled": { "label_vi": "Đã hủy",        "terminal": true  }
  }
}
```

### debt_status — partnerdebts.status
```json
{
  "enum": "debt_status",
  "table": "partnerdebts", "column": "status",
  "values": {
    "InDebt":  { "label_vi": "Còn nợ",    "aliases_vi": ["đang nợ", "chưa thanh toán"], "terminal": false },
    "Cleared": { "label_vi": "Đã tất toán","aliases_vi": ["hết nợ", "đã trả xong"],     "terminal": true  }
  }
}
```

### partner_type — partnerdebts.partner_type
```json
{
  "enum": "partner_type",
  "table": "partnerdebts", "column": "partner_type",
  "values": {
    "Customer": { "label_vi": "Khách hàng",     "aliases_vi": ["công nợ khách", "KH nợ"] },
    "Supplier": { "label_vi": "Nhà cung cấp",   "aliases_vi": ["công nợ NCC", "nợ nhà cung cấp"] }
  }
}
```

### product_status — products.status
```json
{
  "enum": "product_status",
  "table": "products", "column": "status",
  "values": {
    "Active":   { "label_vi": "Đang kinh doanh", "aliases_vi": ["đang bán", "hoạt động"] },
    "Inactive": { "label_vi": "Ngừng kinh doanh","aliases_vi": ["dừng bán", "không còn bán"] }
  }
}
```

### category_status — categories.status
```json
{
  "enum": "category_status",
  "table": "categories", "column": "status",
  "values": {
    "Active":   { "label_vi": "Hoạt động" },
    "Inactive": { "label_vi": "Tạm dừng" }
  }
}
```

### customer_status — customers.status
```json
{
  "enum": "customer_status",
  "table": "customers", "column": "status",
  "values": {
    "Active":   { "label_vi": "Hoạt động" },
    "Inactive": { "label_vi": "Tạm dừng" }
  }
}
```

### supplier_status — suppliers.status
```json
{
  "enum": "supplier_status",
  "table": "suppliers", "column": "status",
  "values": {
    "Active":   { "label_vi": "Đang hợp tác" },
    "Inactive": { "label_vi": "Tạm dừng hợp tác" }
  }
}
```

### location_status — warehouselocations.status
```json
{
  "enum": "location_status",
  "table": "warehouselocations", "column": "status",
  "values": {
    "Active":      { "label_vi": "Đang dùng" },
    "Maintenance": { "label_vi": "Đang bảo trì" },
    "Inactive":    { "label_vi": "Ngừng sử dụng" }
  }
}
```

### alert_type — alertsettings.alert_type
```json
{
  "enum": "alert_type",
  "table": "alertsettings", "column": "alert_type",
  "values": {
    "LowStock":              { "label_vi": "Cảnh báo tồn kho thấp" },
    "ExpiryDate":            { "label_vi": "Cảnh báo hết hạn sử dụng" },
    "HighValueTransaction":  { "label_vi": "Giao dịch giá trị lớn" },
    "PendingApproval":       { "label_vi": "Chờ phê duyệt" },
    "PartnerDebtDueSoon":    { "label_vi": "Công nợ sắp đến hạn" }
  }
}
```

### inventory_action_type — inventorylogs.action_type
```json
{
  "enum": "inventory_action_type",
  "table": "inventorylogs", "column": "action_type",
  "values": {
    "INBOUND":    { "label_vi": "Nhập kho",        "quantity_sign": "positive" },
    "OUTBOUND":   { "label_vi": "Xuất kho",        "quantity_sign": "negative" },
    "TRANSFER":   { "label_vi": "Điều chuyển kho", "quantity_sign": "depends_on_direction" },
    "ADJUSTMENT": { "label_vi": "Điều chỉnh",      "quantity_sign": "positive_or_negative" }
  }
}
```

### audit_status — inventoryauditsessions.status
```json
{
  "enum": "audit_status",
  "table": "inventoryauditsessions", "column": "status",
  "values": {
    "Pending":     { "label_vi": "Chờ bắt đầu" },
    "In Progress": { "label_vi": "Đang kiểm kê" },
    "Completed":   { "label_vi": "Đã hoàn thành", "terminal": true },
    "Cancelled":   { "label_vi": "Đã hủy",         "terminal": true }
  }
}
```

### draft_status — ai_catalog_draft.status / ai_inventory_draft.status
```json
{
  "enum": "draft_status",
  "tables": ["ai_catalog_draft", "ai_inventory_draft"], "column": "status",
  "values": {
    "draft":     { "label_vi": "Nháp chờ xác nhận" },
    "committed": { "label_vi": "Đã xác nhận và ghi",  "terminal": true },
    "expired":   { "label_vi": "Hết hạn",              "terminal": true }
  }
}
```

### catalog_draft_entity_type — ai_catalog_draft.entity_type
```json
{
  "enum": "catalog_draft_entity_type",
  "table": "ai_catalog_draft", "column": "entity_type",
  "values": {
    "product":  { "label_vi": "Sản phẩm mới" },
    "category": { "label_vi": "Danh mục mới" },
    "supplier": { "label_vi": "Nhà cung cấp mới" },
    "customer": { "label_vi": "Khách hàng mới" }
  }
}
```

### inventory_draft_entity_type — ai_inventory_draft.entity_type
```json
{
  "enum": "inventory_draft_entity_type",
  "table": "ai_inventory_draft", "column": "entity_type",
  "values": {
    "stock_receipt": { "label_vi": "Phiếu nhập kho mới" }
  }
}
```

---

## Validation Rules

- SQL WHERE phải dùng **mã thô** (VD: `status = 'Approved'`), không dùng nhãn Việt.
- Answer_composer render **nhãn Việt**, không hiển thị raw code cho user.
- Nếu user dùng alias Việt ambiguous (VD: "chờ" → Pending hoặc nhiều loại) → HITL.
- Enum bị deprecated: giữ trong file với `deprecated: true`, sql_subagent không tạo WHERE điều kiện cho nó.
