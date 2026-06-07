# K14 - Vietnamese Units And Formatting

```yaml
asset_id: K14
version: "2026.06.07"
source_of_truth: manual
refresh_policy: manual_review
consumers: [answer_composer, chart_tool]
must_log_version_in_trace: false
```

## Purpose

Chuẩn hóa định dạng số, tiền tệ, ngày tháng, đơn vị, và nhãn để output tiếng Việt nhất quán trên mọi template.

---

## Locale

```yaml
locale: vi-VN
timezone: Asia/Ho_Chi_Minh   # UTC+7, IANA standard cho Việt Nam
calendar: Gregorian
```

---

## Currency — Tiền tệ VND

```yaml
currency:
  default: VND
  symbol: "đ"
  iso_code: VND

formatting:
  thousands_separator: "."
  decimal_separator: ","
  decimal_places: 0    # VND không dùng số lẻ trong hiển thị thông thường

compact_rules:
  - threshold: 1_000_000_000   display: "{value} tỷ đồng"      example: "1,5 tỷ đồng"
  - threshold: 1_000_000       display: "{value} triệu đồng"   example: "45,2 triệu đồng"
  - threshold: 1_000           display: "{value} nghìn đồng"   example: "850 nghìn đồng"
  - threshold: 0               display: "{value} đồng"          example: "750 đồng"

exact_display_rule: "Trong bảng chi tiết: 45.200.000 đ (dùng dấu chấm ngàn, ký hiệu đ cuối)"
headline_rule:      "Trong headline/summary: dùng compact (45,2 triệu đồng)"

negative_display:
  rule: "Khi số âm (chi phí): hiển thị dấu trừ trước — VD: -8,5 triệu đồng"
  do_not: "Không dùng ngoặc đơn (-8.500.000) cho user thông thường"
```

---

## Date & Time — Ngày tháng

```yaml
date_format:
  full_date:    "dd/MM/yyyy"     example: "07/06/2026"
  month_year:   "MM/yyyy"        example: "06/2026"
  year_only:    "yyyy"           example: "2026"
  time_only:    "HH:mm"          example: "14:30"
  datetime:     "dd/MM/yyyy HH:mm"  example: "07/06/2026 14:30"

relative_period_labels:
  today:        "hôm nay ({date})"
  this_month:   "tháng {MM}/{yyyy}"
  last_month:   "tháng trước ({MM}/{yyyy})"
  this_quarter: "Quý {Q}/{yyyy}"
  this_year:    "năm {yyyy}"

fiscal_period:
  rule: "Dùng năm dương lịch (Gregorian), không có tài khóa riêng"
  quarter_definition:
    Q1: "01/01 – 31/03"
    Q2: "01/04 – 30/06"
    Q3: "01/07 – 30/09"
    Q4: "01/10 – 31/12"

timezone_display:
  rule: "Tất cả thời gian hiển thị theo Asia/Ho_Chi_Minh (GMT+7)"
  sql_note: "transaction_date là DATE (không có timezone) — filter trực tiếp theo date_trunc"
  timestamp_note: "Khi cần hiển thị timestamp: AT TIME ZONE 'Asia/Ho_Chi_Minh'"
```

---

## Numbers — Số

```yaml
numbers:
  decimal_separator: ","
  thousands_separator: "."
  percent:
    display: "{value}%"
    decimal_places: 1
    example: "23,5%"
  large_numbers:
    million: "triệu"    # 1.000.000
    billion: "tỷ"       # 1.000.000.000

rounding:
  currency: "Làm tròn đến đồng (0 decimal)"
  percent:  "Làm tròn 1 decimal"
  quantity: "Làm tròn đến số nguyên"
```

---

## Units — Đơn vị đo

```yaml
units:
  quantity:
    default: "sản phẩm"
    context_rules:
      - entity: order        unit: "đơn hàng"
      - entity: receipt      unit: "phiếu"
      - entity: customer     unit: "khách"
      - entity: product      unit: "sản phẩm"  fallback: dùng unit_name từ productunits
      - entity: transaction  unit: "giao dịch"

  weight:
    default: "gram"
    convert_display:
      - "≥ 1000g → kg"

  money: "đồng"   # hoặc compact theo compact_rules

  days: "ngày"
  hours: "giờ"
  months: "tháng"

unit_display_position: "sau số"   # VD: "100 sản phẩm", "50 đơn hàng"
```

---

## Answer Formatting Rules

```yaml
answer_rules:
  headline:
    rule: "Số tiền compact, ngày tháng đầy đủ. Tối đa 2 câu."
    example: "Doanh thu tháng 06/2026 là **45,2 triệu đồng**."

  table_column:
    rule: "Số tiền exact với dấu chấm ngàn và ký hiệu đ"
    example: "45.200.000 đ"

  date_range:
    rule: "Luôn ghi rõ khoảng nếu user dùng relative period"
    example: "Tháng 06/2026 (từ 01/06/2026 đến 30/06/2026)"

  empty_zero:
    rule: "Phân biệt 0 đồng (có dữ liệu, giá trị bằng 0) và NULL (không có giao dịch)"
    zero_display: "0 đồng"
    null_display: "Không có dữ liệu"

  mixed_language:
    rule: "KHÔNG mix Anh-Việt trong 1 câu hướng user"
    bad: "Revenue của tháng này là 45 triệu"
    good: "Doanh thu tháng này là 45 triệu đồng"

  business_terms_only:
    rule: "Dùng nhãn nghiệp vụ từ K3, không dùng raw enum code"
    bad: "status = 'SalesRevenue'"
    good: "Doanh thu bán hàng"
```

---

## Chart Label Rules

```yaml
chart_labels:
  axis_labels: "Luôn có nhãn tiếng Việt trên cả 2 trục"
  currency_axis: "Đơn vị: triệu đồng (nếu compact) hoặc đồng"
  date_axis:
    monthly: "MM/yyyy"
    daily:   "dd/MM"
  percent_axis: "%"
  legend: "Dùng label_vi từ K1 hoặc K3, không dùng tên cột"
```
