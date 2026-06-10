# K9 - Chart Spec Catalog

```yaml
asset_id: K9
version: "2026.06.07"
source_of_truth: manual
refresh_policy: manual_review
consumers: [chart_tool, planner, answer_composer]
must_log_version_in_trace: true
```

## Purpose

Định nghĩa loại biểu đồ hợp lệ, shape dữ liệu yêu cầu, và quy tắc chọn biểu đồ phù hợp để frontend luôn nhận được payload có thể render được.

---

## Chart Types

### time_series_line — Đường theo thời gian
```yaml
chart_type: time_series_line
label_vi: "Biểu đồ đường theo thời gian"
recommended_for:
  - revenue_by_day
  - revenue_by_month
  - cashflow_by_period
  - inventory_trend
required_shape:
  x:
    type: [date, datetime, string_period]
    label: "Trục thời gian"
    example: "2026-06-01" hoặc "06/2026"
  y:
    type: number
    label: "Giá trị"
  series:
    type: string
    optional: true
    note: "Khi có nhiều dòng (VD: lẻ vs sỉ)"
min_data_points: 2
max_series: 5
```

### bar — Cột so sánh
```yaml
chart_type: bar
label_vi: "Biểu đồ cột"
recommended_for:
  - top_products_by_quantity
  - top_products_by_revenue
  - sales_by_category
  - order_count_by_status
  - order_count_by_channel
  - revenue_by_channel
required_shape:
  x:
    type: category
    label: "Nhãn danh mục"
  y:
    type: number
    label: "Giá trị"
  stacked:
    type: boolean
    optional: true
    default: false
min_data_points: 1
max_categories: 20
```

### pie — Tròn tỉ lệ
```yaml
chart_type: pie
label_vi: "Biểu đồ tròn"
recommended_for:
  - market_share_by_channel
  - stock_distribution_by_category
required_shape:
  label:
    type: category
  value:
    type: number
    must_be_positive: true
max_slices: 8
note: "Khi > 8 slice → gộp phần còn lại thành 'Khác'. Không dùng cho time-series."
```

### table_grid — Bảng dữ liệu
```yaml
chart_type: table_grid
label_vi: "Bảng dữ liệu"
recommended_for:
  - top_products_detail
  - low_stock_list
  - debt_list
  - receipt_list
  - any_query_with_multiple_columns
required_shape:
  columns:
    type: array
    each:
      name: string
      label_vi: string
      type: [string, number, date, currency]
  rows:
    type: array
use_when: "Khi dữ liệu có nhiều cột chi tiết hoặc data_points < 3 cho biểu đồ đường"
```

### summary_card — Thẻ tóm tắt số liệu
```yaml
chart_type: summary_card
label_vi: "Thẻ số liệu nổi bật"
recommended_for:
  - single_metric (VD: tổng doanh thu tháng)
  - kpi_snapshot
required_shape:
  value:
    type: number
  label_vi:
    type: string
  unit:
    type: string
  change_percent:
    type: number
    optional: true
    note: "So với kỳ trước"
use_when: "Khi query trả về 1 dòng 1 cột số"
```

---

## Chart Selection Rules

```yaml
selection_rules:
  - condition: "query trả về 1 row, 1 cột số"
    choose: summary_card

  - condition: "x_column là date/month/year và y là số → ít nhất 2 điểm"
    choose: time_series_line

  - condition: "x là category (≤ 8 giá trị) và hỏi về tỉ lệ/phân bổ"
    choose: pie

  - condition: "x là category và hỏi so sánh/xếp hạng"
    choose: bar

  - condition: "nhiều cột chi tiết hoặc < 2 data points cho line chart"
    choose: table_grid

  - condition: "dữ liệu rỗng hoặc chỉ có 1 row"
    choose: table_grid
    note: "Không render biểu đồ trống"
```

---

## Payload Contract

```json
{
  "chart_type": "time_series_line",
  "title_vi": "Doanh thu theo tháng năm 2026",
  "x_key": "thang",
  "y_keys": ["doanh_thu"],
  "y_labels_vi": { "doanh_thu": "Doanh thu" },
  "data": [
    { "thang": "04/2026", "doanh_thu": 15000000 },
    { "thang": "05/2026", "doanh_thu": 22000000 },
    { "thang": "06/2026", "doanh_thu": 18500000 }
  ],
  "unit": "VND",
  "currency": "VND",
  "x_format": "MM/YYYY",
  "y_format": "currency_compact",
  "assumptions": ["Doanh thu từ sổ cái tài chính, transaction_type=SalesRevenue"],
  "source_query_id": "sql_ex_002",
  "data_sensitivity": "finance_sensitive",
  "generated_at": "2026-06-07T10:00:00+07:00"
}
```

---

## Degrade Rules

```yaml
degrade_rules:
  sparse_time_series:
    condition: "time_series_line với < 2 data points"
    action: "Chuyển sang summary_card + table_grid"
    note_vi: "Không đủ dữ liệu để vẽ đường, hiển thị dạng bảng"

  too_many_slices:
    condition: "pie với > 8 slices"
    action: "Gộp phần nhỏ thành 'Khác' để giữ ≤ 8"

  empty_data:
    condition: "data = [] sau sql_subagent"
    action: "Không emit chart event — trả empty_result template K10.T6"

  mixed_units:
    condition: "y_keys có mixed currency và count"
    action: "Tách thành 2 chart riêng hoặc dùng dual-axis bar"
```

---

## Sensitive Data in Charts

```yaml
sensitive_rules:
  - chart_type: [time_series_line, bar, summary_card]
    data_sensitivity: finance_sensitive
    visible_roles: [owner]
    action_if_staff: "Không emit chart event, trả permission_denied"

  - data_sensitivity: cost_sensitive
    visible_roles: [owner]
    action_if_staff: "Strip cost_price column khỏi payload trước khi emit"
```

---

## Acceptance Checklist

- [ ] Frontend render được tất cả 5 chart types
- [ ] Payload luôn có `unit`, `currency`, `assumptions`
- [ ] Biểu đồ không emit khi data rỗng
- [ ] finance_sensitive chart bị chặn với staff
- [ ] Axes label dùng label_vi từ K1/K3
- [ ] Ngày tháng theo format K14 (dd/MM/yyyy, MM/yyyy)
