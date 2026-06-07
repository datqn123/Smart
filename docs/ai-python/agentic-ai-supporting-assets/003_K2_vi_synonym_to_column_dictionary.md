# K2 - Vietnamese Synonym To Column Dictionary

```yaml
asset_id: K2
version: "2026.06.07"
source_of_truth: manual
refresh_policy: monthly_review
consumers: [intent, sql_subagent, planner]
must_log_version_in_trace: true
```

## Purpose

Map từ khóa tiếng Việt → bảng/cột/metric thực trong DB để intent subagent phân giải đúng ý định user.

`confidence_boost`: cộng thêm vào base confidence khi term khớp chính xác (exact/fuzzy score ≥ 0.8). VD base=0.72 + boost=0.2 → 0.92 → chạy luôn.

---

## Terms

### Tài chính — Doanh thu
```yaml
- term: "doanh thu"
  aliases_vi: ["doanh số", "tiền bán", "thu bán hàng", "revenue"]
  maps_to:
    - kind: metric    id: sales_revenue
    - kind: table     table: financeledger
    - kind: filter    table: financeledger  column: transaction_type  value: SalesRevenue
  confidence_boost: 0.15
  requires_filters: [time_range]
  examples: ["Doanh thu tháng này", "Doanh thu quý 1", "Tổng tiền bán được hôm nay"]

- term: "doanh thu theo kênh"
  aliases_vi: ["doanh thu lẻ", "doanh thu sỉ", "bán lẻ", "bán sỉ"]
  maps_to:
    - kind: metric    id: sales_revenue_by_channel
    - kind: join      primary: financeledger  secondary: salesorders  via: "reference_type='SalesOrder'"
    - kind: group_by  table: salesorders  column: order_channel
  confidence_boost: 0.1
  examples: ["Doanh thu kênh bán lẻ tháng này", "So sánh bán lẻ và bán sỉ"]
```

### Tài chính — Chi phí & Lợi nhuận
```yaml
- term: "chi phí"
  aliases_vi: ["chi tiền", "khoản chi", "expense", "chi vận hành"]
  maps_to:
    - kind: metric  id: total_expense
    - kind: filter  table: financeledger  column: transaction_type  value: [OperatingExpense, PurchaseCost]
  sensitivity: finance_sensitive
  confidence_boost: 0.1
  examples: ["Chi phí tháng này là bao nhiêu"]

- term: "lợi nhuận"
  aliases_vi: ["lãi", "lãi gộp", "lời", "profit", "lợi nhuận gộp"]
  maps_to:
    - kind: metric  id: gross_profit
    - kind: formula hint: "SUM(amount) WHERE transaction_type IN ('SalesRevenue','PurchaseCost')"
  sensitivity: finance_sensitive
  ambiguity: ["lãi" có thể là gross_profit hoặc net_cashflow — hỏi lại nếu không rõ ngữ cảnh]
  confidence_boost: 0.05
  examples: ["Lợi nhuận tháng này", "Cửa hàng lời bao nhiêu"]

- term: "dòng tiền"
  aliases_vi: ["cashflow", "tiền mặt vào ra", "thu chi"]
  maps_to:
    - kind: metric  id: net_cashflow
    - kind: table   table: financeledger
  sensitivity: finance_sensitive
  confidence_boost: 0.1
```

### Tài chính — Công nợ
```yaml
- term: "công nợ"
  aliases_vi: ["nợ", "còn nợ", "debt", "tiền nợ"]
  maps_to:
    - kind: metric  id: partner_debt_balance
    - kind: table   table: partnerdebts
  sensitivity: finance_sensitive
  ambiguity: ["công nợ" không rõ khách hay NCC — nếu thiếu context, hỏi HITL"]
  confidence_boost: 0.1
  examples: ["Khách nào đang nợ tiền", "Tổng công nợ hiện tại"]

- term: "nợ khách hàng"
  aliases_vi: ["khách nợ", "công nợ khách", "KH nợ", "receivable"]
  maps_to:
    - kind: filter  table: partnerdebts  column: partner_type  value: Customer
  confidence_boost: 0.15
  examples: ["Khách hàng nào còn nợ tiền", "Tổng nợ khách hàng"]

- term: "nợ nhà cung cấp"
  aliases_vi: ["nợ NCC", "công nợ nhà cung cấp", "payable"]
  maps_to:
    - kind: filter  table: partnerdebts  column: partner_type  value: Supplier
  confidence_boost: 0.15

- term: "quá hạn"
  aliases_vi: ["nợ quá hạn", "đến hạn chưa trả"]
  maps_to:
    - kind: filter  table: partnerdebts  column: due_date   condition: "< CURRENT_DATE"
    - kind: filter  table: partnerdebts  column: status     value: InDebt
  confidence_boost: 0.1
  examples: ["Công nợ quá hạn", "Ai nợ quá hạn rồi"]
```

### Tồn kho
```yaml
- term: "tồn kho"
  aliases_vi: ["hàng còn", "số lượng tồn", "stock", "hàng trong kho", "tồn"]
  maps_to:
    - kind: metric  id: inventory_on_hand
    - kind: table   table: inventory
    - kind: column  table: inventory  column: quantity
  confidence_boost: 0.2
  examples: ["Tồn kho hiện tại là bao nhiêu", "Sản phẩm nào còn trong kho"]

- term: "sắp hết hàng"
  aliases_vi: ["cần nhập thêm", "hàng sắp cạn", "low stock", "tồn thấp"]
  maps_to:
    - kind: metric   id: low_stock
    - kind: filter   table: inventory  condition: "quantity <= min_quantity"
  confidence_boost: 0.2
  examples: ["Sản phẩm nào sắp hết hàng", "Danh sách hàng cần nhập thêm"]

- term: "sắp hết hạn"
  aliases_vi: ["gần hết hạn sử dụng", "hàng sắp hỏng"]
  maps_to:
    - kind: filter  table: inventory  condition: "expiry_date BETWEEN NOW() AND NOW() + INTERVAL '30 days'"
  confidence_boost: 0.15
  examples: ["Hàng nào sắp hết hạn trong 30 ngày"]
```

### Sản phẩm & Danh mục
```yaml
- term: "sản phẩm bán chạy"
  aliases_vi: ["hàng bán chạy", "top sản phẩm", "sản phẩm hot", "best seller"]
  maps_to:
    - kind: metric    id: top_products_by_quantity
    - kind: join      primary: orderdetails  secondary: products  via: "product_id"
    - kind: order_by  table: orderdetails  column: "SUM(quantity)"  direction: DESC
  confidence_boost: 0.1
  ambiguity: ["bán chạy" theo số lượng hay doanh thu? — mặc định số lượng, nêu giả định"]
  examples: ["Top 10 sản phẩm bán chạy nhất tháng này"]

- term: "giá sản phẩm"
  aliases_vi: ["giá bán", "bán giá bao nhiêu", "giá hiện tại"]
  maps_to:
    - kind: table   table: productpricehistory
    - kind: column  table: productpricehistory  column: sale_price
    - kind: order   condition: "ORDER BY effective_date DESC LIMIT 1 per (product, unit)"
  confidence_boost: 0.1

- term: "giá vốn"
  aliases_vi: ["giá nhập", "giá mua vào", "cost price"]
  maps_to:
    - kind: column  table: productpricehistory  column: cost_price
  sensitivity: cost_sensitive
  visibility: [owner]
  confidence_boost: 0.1
```

### Đơn hàng & Khách hàng
```yaml
- term: "đơn hàng"
  aliases_vi: ["order", "đơn bán", "hóa đơn bán"]
  maps_to:
    - kind: table  table: salesorders
  confidence_boost: 0.1
  examples: ["Đơn hàng hôm nay", "Đơn hàng chờ xử lý"]

- term: "đơn chưa xử lý"
  aliases_vi: ["đơn đang chờ", "đơn pending", "chưa duyệt đơn"]
  maps_to:
    - kind: filter  table: salesorders  column: status  value: Pending
  confidence_boost: 0.15

- term: "khách hàng"
  aliases_vi: ["khách", "người mua", "KH", "customer"]
  maps_to:
    - kind: table  table: customers
  confidence_boost: 0.1

- term: "khách VIP"
  aliases_vi: ["khách mua nhiều nhất", "khách hàng thân thiết", "top khách"]
  maps_to:
    - kind: metric  id: top_customers_by_spending
    - kind: join    primary: salesorders  secondary: customers  via: "customer_id"
    - kind: order   condition: "ORDER BY SUM(financeledger.amount) DESC"
  confidence_boost: 0.05
```

### Nhập kho & Nhà cung cấp
```yaml
- term: "phiếu nhập"
  aliases_vi: ["nhập kho", "nhập hàng", "stock receipt", "phiếu nhập kho"]
  maps_to:
    - kind: table  table: stockreceipts
  confidence_boost: 0.15
  examples: ["Phiếu nhập chờ duyệt", "Nhập kho hôm nay"]

- term: "nhà cung cấp"
  aliases_vi: ["NCC", "supplier", "đối tác cung cấp"]
  maps_to:
    - kind: table  table: suppliers
  confidence_boost: 0.1
```

### Thời gian
```yaml
- term: "hôm nay"
  maps_to:
    - kind: filter  condition: "DATE(column) = CURRENT_DATE"
  is_time_anchor: true

- term: "tháng này"
  maps_to:
    - kind: filter  condition: "column >= date_trunc('month', CURRENT_DATE) AND column < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
  is_time_anchor: true

- term: "tháng trước"
  maps_to:
    - kind: filter  condition: "column >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 month' AND column < date_trunc('month', CURRENT_DATE)"
  is_time_anchor: true

- term: "quý này"
  maps_to:
    - kind: filter  condition: "column >= date_trunc('quarter', CURRENT_DATE) AND column < date_trunc('quarter', CURRENT_DATE) + INTERVAL '3 months'"
  is_time_anchor: true

- term: "năm nay"
  maps_to:
    - kind: filter  condition: "column >= date_trunc('year', CURRENT_DATE) AND column < date_trunc('year', CURRENT_DATE) + INTERVAL '1 year'"
  is_time_anchor: true
```

---

## Ambiguity Table

| User term | Mơ hồ | Hành động |
|---|---|---|
| "lãi" | Gross profit hay net cashflow? | HITL nếu không rõ ngữ cảnh |
| "bán chạy" | Theo số lượng hay doanh thu? | Mặc định số lượng, nêu giả định |
| "công nợ" | KH hay NCC? | HITL để hỏi |
| "hàng tồn" | Tất cả hay chỉ đang active? | Mặc định active (status='Active') |
| "doanh thu" thiếu kỳ | Không có khoảng thời gian | HITL bắt buộc hỏi kỳ |
| "sắp hết hàng" ngưỡng bao nhiêu | Không rõ ngưỡng | Dùng min_quantity từ inventory, nêu giả định |
| "top" không rõ số | Bao nhiêu? | Mặc định top 10, nêu giả định |

## Matching Rules

1. Exact normalized match (lowercase, bỏ dấu) → dùng ngay.
2. Fuzzy string match với aliases_vi.
3. Embedding similarity với term description.
4. Nếu score < 0.6 → HITL bắt buộc.
5. Nếu 0.6 ≤ score < 0.75 → HITL nếu ambiguity.
6. Nếu score ≥ 0.75 và không có ambiguity blocking → tự suy, nêu giả định.
7. Nếu term maps_to có `sensitivity` → kiểm tra K6 trước khi resolve.
