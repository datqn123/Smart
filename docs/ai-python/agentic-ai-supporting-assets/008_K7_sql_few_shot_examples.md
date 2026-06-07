# K7 - SQL Few-Shot Examples

```yaml
asset_id: K7
version: "2026.06.07"
source_of_truth: manual
refresh_policy: manual_review
consumers: [sql_subagent, sql_review]
must_log_version_in_trace: true
```

## Purpose

Bộ ví dụ câu hỏi Việt → SQL đúng làm few-shot prompt cho sql_subagent. Tất cả SQL phải pass K5.

---

## Examples

### sql_ex_001 — Doanh thu tháng này
```yaml
id: sql_ex_001
intent_type: data_query
role_visibility: [owner]
question_vi: "Doanh thu tháng này là bao nhiêu?"
assumptions: ["Doanh thu = SUM(amount) từ financeledger WHERE transaction_type='SalesRevenue'"]
sql: |
  SELECT SUM(amount) AS doanh_thu
  FROM financeledger
  WHERE transaction_type = 'SalesRevenue'
    AND transaction_date >= date_trunc('month', CURRENT_DATE)
    AND transaction_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  LIMIT 1;
expected_shape: { columns: [doanh_thu], row_count: 1, unit: VND }
```

### sql_ex_002 — Doanh thu theo từng tháng trong năm
```yaml
id: sql_ex_002
intent_type: chart_report
role_visibility: [owner]
question_vi: "Doanh thu từng tháng trong năm nay?"
sql: |
  SELECT
    to_char(date_trunc('month', transaction_date), 'MM/YYYY') AS thang,
    SUM(amount) AS doanh_thu
  FROM financeledger
  WHERE transaction_type = 'SalesRevenue'
    AND transaction_date >= date_trunc('year', CURRENT_DATE)
    AND transaction_date < date_trunc('year', CURRENT_DATE) + INTERVAL '1 year'
  GROUP BY date_trunc('month', transaction_date)
  ORDER BY date_trunc('month', transaction_date)
  LIMIT 100;
expected_shape: { columns: [thang, doanh_thu], row_count: "1-12", chart_type: time_series_line }
```

### sql_ex_003 — Top 10 sản phẩm bán chạy theo số lượng
```yaml
id: sql_ex_003
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Top 10 sản phẩm bán chạy nhất tháng này?"
assumptions: ["Bán chạy tính theo số lượng đã bán trong orderdetails của đơn KHÔNG bị Cancelled"]
sql: |
  SELECT
    p.name AS ten_san_pham,
    p.sku_code,
    SUM(od.quantity) AS so_luong_ban
  FROM orderdetails od
  JOIN salesorders so ON od.order_id = so.id
  JOIN products p ON od.product_id = p.id
  WHERE so.status != 'Cancelled'
    AND so.created_at >= date_trunc('month', CURRENT_DATE)
    AND so.created_at < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  GROUP BY p.id, p.name, p.sku_code
  ORDER BY so_luong_ban DESC
  LIMIT 10;
expected_shape: { columns: [ten_san_pham, sku_code, so_luong_ban], row_count: "0-10" }
```

### sql_ex_004 — Tồn kho hiện tại tất cả sản phẩm
```yaml
id: sql_ex_004
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Tổng tồn kho hiện tại của từng sản phẩm?"
sql: |
  SELECT
    p.name AS ten_san_pham,
    p.sku_code,
    SUM(i.quantity) AS tong_ton_kho
  FROM inventory i
  JOIN products p ON i.product_id = p.id
  WHERE p.status = 'Active'
  GROUP BY p.id, p.name, p.sku_code
  ORDER BY tong_ton_kho DESC
  LIMIT 100;
expected_shape: { columns: [ten_san_pham, sku_code, tong_ton_kho] }
```

### sql_ex_005 — Danh sách sản phẩm sắp hết hàng
```yaml
id: sql_ex_005
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Sản phẩm nào sắp hết hàng?"
assumptions: ["Sắp hết = quantity <= min_quantity trong inventory"]
sql: |
  SELECT
    p.name AS ten_san_pham,
    p.sku_code,
    SUM(i.quantity) AS ton_hien_tai,
    MAX(i.min_quantity) AS muc_canh_bao
  FROM inventory i
  JOIN products p ON i.product_id = p.id
  WHERE p.status = 'Active'
  GROUP BY p.id, p.name, p.sku_code
  HAVING SUM(i.quantity) <= MAX(i.min_quantity)
  ORDER BY (SUM(i.quantity)::float / NULLIF(MAX(i.min_quantity), 0)) ASC
  LIMIT 50;
expected_shape: { columns: [ten_san_pham, sku_code, ton_hien_tai, muc_canh_bao] }
```

### sql_ex_006 — Tổng công nợ khách hàng còn lại
```yaml
id: sql_ex_006
intent_type: data_query
role_visibility: [owner]
question_vi: "Tổng công nợ khách hàng hiện tại là bao nhiêu?"
sql: |
  SELECT
    SUM(total_amount - paid_amount) AS tong_no_con_lai,
    COUNT(*) AS so_khach_dang_no
  FROM partnerdebts
  WHERE partner_type = 'Customer'
    AND status = 'InDebt'
  LIMIT 1;
expected_shape: { columns: [tong_no_con_lai, so_khach_dang_no], row_count: 1, unit: VND }
```

### sql_ex_007 — Danh sách khách hàng nợ quá hạn
```yaml
id: sql_ex_007
intent_type: data_query
role_visibility: [owner]
question_vi: "Khách hàng nào nợ quá hạn rồi?"
sql: |
  SELECT
    c.name AS ten_khach,
    c.phone AS so_dien_thoai,
    pd.total_amount - pd.paid_amount AS so_no_con_lai,
    pd.due_date AS han_thanh_toan
  FROM partnerdebts pd
  JOIN customers c ON pd.customer_id = c.id
  WHERE pd.partner_type = 'Customer'
    AND pd.status = 'InDebt'
    AND pd.due_date < CURRENT_DATE
  ORDER BY pd.due_date ASC
  LIMIT 50;
expected_shape: { columns: [ten_khach, so_dien_thoai, so_no_con_lai, han_thanh_toan] }
```

### sql_ex_008 — Đơn hàng chờ xử lý hôm nay
```yaml
id: sql_ex_008
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Có bao nhiêu đơn hàng đang chờ xử lý?"
sql: |
  SELECT
    COUNT(*) AS so_don_cho_xu_ly,
    SUM(final_amount) AS gia_tri_don_cho
  FROM salesorders
  WHERE status = 'Pending'
  LIMIT 1;
expected_shape: { columns: [so_don_cho_xu_ly, gia_tri_don_cho], row_count: 1 }
```

### sql_ex_009 — Số đơn theo trạng thái
```yaml
id: sql_ex_009
intent_type: chart_report
role_visibility: [owner, staff]
question_vi: "Số đơn hàng theo trạng thái tháng này?"
sql: |
  SELECT
    status AS trang_thai,
    COUNT(*) AS so_don
  FROM salesorders
  WHERE created_at >= date_trunc('month', CURRENT_DATE)
    AND created_at < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  GROUP BY status
  ORDER BY so_don DESC
  LIMIT 20;
expected_shape: { columns: [trang_thai, so_don], chart_type: bar }
```

### sql_ex_010 — Chi phí nhập hàng tháng này
```yaml
id: sql_ex_010
intent_type: data_query
role_visibility: [owner]
question_vi: "Chi phí nhập hàng tháng này là bao nhiêu?"
sql: |
  SELECT SUM(amount) AS chi_phi_nhap_hang
  FROM financeledger
  WHERE transaction_type = 'PurchaseCost'
    AND transaction_date >= date_trunc('month', CURRENT_DATE)
    AND transaction_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  LIMIT 1;
expected_shape: { columns: [chi_phi_nhap_hang], row_count: 1, unit: VND }
```

### sql_ex_011 — Lợi nhuận gộp tháng này
```yaml
id: sql_ex_011
intent_type: data_query
role_visibility: [owner]
question_vi: "Lợi nhuận gộp tháng này là bao nhiêu?"
assumptions: ["Lợi nhuận gộp = SalesRevenue + PurchaseCost (PurchaseCost âm)"]
sql: |
  SELECT
    SUM(CASE WHEN transaction_type = 'SalesRevenue' THEN amount ELSE 0 END) AS doanh_thu,
    SUM(CASE WHEN transaction_type = 'PurchaseCost' THEN amount ELSE 0 END) AS gia_von,
    SUM(CASE WHEN transaction_type IN ('SalesRevenue','PurchaseCost') THEN amount ELSE 0 END) AS loi_nhuan_gop
  FROM financeledger
  WHERE transaction_type IN ('SalesRevenue', 'PurchaseCost')
    AND transaction_date >= date_trunc('month', CURRENT_DATE)
    AND transaction_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  LIMIT 1;
expected_shape: { columns: [doanh_thu, gia_von, loi_nhuan_gop], row_count: 1, unit: VND }
```

### sql_ex_012 — Tồn kho theo danh mục
```yaml
id: sql_ex_012
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Tổng tồn kho theo từng danh mục?"
sql: |
  SELECT
    cat.name AS danh_muc,
    COUNT(DISTINCT p.id) AS so_san_pham,
    SUM(i.quantity) AS tong_ton_kho
  FROM inventory i
  JOIN products p ON i.product_id = p.id
  JOIN categories cat ON p.category_id = cat.id
  WHERE p.status = 'Active'
    AND cat.status = 'Active'
  GROUP BY cat.id, cat.name
  ORDER BY tong_ton_kho DESC
  LIMIT 50;
expected_shape: { columns: [danh_muc, so_san_pham, tong_ton_kho] }
```

### sql_ex_013 — Sản phẩm sắp hết hạn trong 30 ngày
```yaml
id: sql_ex_013
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Sản phẩm nào sắp hết hạn sử dụng trong 30 ngày tới?"
sql: |
  SELECT
    p.name AS ten_san_pham,
    p.sku_code,
    i.batch_number AS so_lo,
    i.expiry_date AS han_su_dung,
    i.quantity AS so_luong_ton,
    wl.warehouse_code || '-' || wl.shelf_code AS vi_tri
  FROM inventory i
  JOIN products p ON i.product_id = p.id
  JOIN warehouselocations wl ON i.location_id = wl.id
  WHERE i.expiry_date IS NOT NULL
    AND i.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
    AND i.quantity > 0
  ORDER BY i.expiry_date ASC
  LIMIT 100;
expected_shape: { columns: [ten_san_pham, sku_code, so_lo, han_su_dung, so_luong_ton, vi_tri] }
```

### sql_ex_014 — Top khách hàng mua nhiều nhất
```yaml
id: sql_ex_014
intent_type: data_query
role_visibility: [owner]
question_vi: "Top 10 khách hàng mua nhiều nhất tháng này?"
sql: |
  SELECT
    c.name AS ten_khach,
    COUNT(DISTINCT so.id) AS so_don_hang,
    SUM(fl.amount) AS tong_doanh_thu
  FROM salesorders so
  JOIN customers c ON so.customer_id = c.id
  JOIN financeledger fl ON fl.reference_type = 'SalesOrder' AND fl.reference_id = so.id
  WHERE fl.transaction_type = 'SalesRevenue'
    AND fl.transaction_date >= date_trunc('month', CURRENT_DATE)
    AND fl.transaction_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  GROUP BY c.id, c.name
  ORDER BY tong_doanh_thu DESC
  LIMIT 10;
expected_shape: { columns: [ten_khach, so_don_hang, tong_doanh_thu] }
```

### sql_ex_015 — Phiếu nhập kho chờ duyệt
```yaml
id: sql_ex_015
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Có bao nhiêu phiếu nhập kho đang chờ duyệt?"
sql: |
  SELECT
    sr.receipt_code AS so_phieu,
    s.name AS nha_cung_cap,
    sr.receipt_date AS ngay_nhap,
    sr.total_amount AS gia_tri_nhap
  FROM stockreceipts sr
  JOIN suppliers s ON sr.supplier_id = s.id
  WHERE sr.status = 'Pending'
  ORDER BY sr.receipt_date DESC
  LIMIT 50;
expected_shape: { columns: [so_phieu, nha_cung_cap, ngay_nhap, gia_tri_nhap] }
```

### sql_ex_016 — Doanh thu theo kênh bán
```yaml
id: sql_ex_016
intent_type: chart_report
role_visibility: [owner]
question_vi: "So sánh doanh thu kênh bán lẻ và bán sỉ tháng này?"
sql: |
  SELECT
    so.order_channel AS kenh_ban,
    SUM(fl.amount) AS doanh_thu
  FROM financeledger fl
  JOIN salesorders so ON fl.reference_type = 'SalesOrder' AND fl.reference_id = so.id
  WHERE fl.transaction_type = 'SalesRevenue'
    AND fl.transaction_date >= date_trunc('month', CURRENT_DATE)
    AND fl.transaction_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  GROUP BY so.order_channel
  ORDER BY doanh_thu DESC
  LIMIT 10;
expected_shape: { columns: [kenh_ban, doanh_thu], chart_type: bar }
```

### sql_ex_017 — Nhật ký biến động kho sản phẩm cụ thể
```yaml
id: sql_ex_017
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Lịch sử nhập xuất của sản phẩm [tên SP] trong 7 ngày qua?"
assumptions: ["Tên sản phẩm đã được resolve qua K4 entity matching"]
sql: |
  SELECT
    il.created_at AS thoi_gian,
    il.action_type AS loai_hanh_dong,
    il.quantity_change AS thay_doi_so_luong,
    il.reference_note AS ghi_chu
  FROM inventorylogs il
  JOIN products p ON il.product_id = p.id
  WHERE p.name ILIKE '%:product_name%'
    AND il.created_at >= CURRENT_DATE - INTERVAL '7 days'
  ORDER BY il.created_at DESC
  LIMIT 100;
expected_shape: { columns: [thoi_gian, loai_hanh_dong, thay_doi_so_luong, ghi_chu] }
note: ":product_name là param được điền từ K4 entity resolution"
```

### sql_ex_018 — Tổng thu chi trong tháng
```yaml
id: sql_ex_018
intent_type: data_query
role_visibility: [owner]
question_vi: "Tổng thu và tổng chi tháng này là bao nhiêu?"
sql: |
  SELECT
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS tong_thu,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS tong_chi,
    SUM(amount) AS don_tien_thuan
  FROM financeledger
  WHERE transaction_date >= date_trunc('month', CURRENT_DATE)
    AND transaction_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'
  LIMIT 1;
expected_shape: { columns: [tong_thu, tong_chi, don_tien_thuan], row_count: 1, unit: VND }
```

### sql_ex_019 — Kết quả rỗng (empty result handling)
```yaml
id: sql_ex_019
intent_type: data_query
role_visibility: [owner]
question_vi: "Doanh thu tháng 2/2020?"
expected_behavior: "Trả về 0 row hoặc NULL — answer_composer phải nói không có dữ liệu, không phải báo lỗi"
sql: |
  SELECT SUM(amount) AS doanh_thu
  FROM financeledger
  WHERE transaction_type = 'SalesRevenue'
    AND transaction_date >= '2020-02-01'
    AND transaction_date < '2020-03-01'
  LIMIT 1;
expected_shape: { columns: [doanh_thu], row_count: 1, value_may_be_null: true }
note: "NULL result → answer 'Không có dữ liệu doanh thu trong khoảng thời gian này'"
```

### sql_ex_020 — Staff không được xem doanh thu (permission denied)
```yaml
id: sql_ex_020
intent_type: data_query
role_visibility: []
question_vi: "Doanh thu tháng này?" (hỏi bởi staff)
expected_behavior: "Guardrail chặn TRƯỚC khi sinh SQL — không có SQL example vì không được phép"
sql: null
policy_response: "HARNESS_POLICY_BLOCK — denied_table: financeledger for role staff"
user_message: "Bạn không có quyền xem thông tin tài chính. Vui lòng liên hệ Owner."
```

### sql_ex_021 — Tồn kho theo vị trí kho
```yaml
id: sql_ex_021
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Kho WH01 kệ A1 còn bao nhiêu hàng?"
sql: |
  SELECT
    p.name AS ten_san_pham,
    i.quantity AS so_luong,
    i.batch_number AS so_lo
  FROM inventory i
  JOIN products p ON i.product_id = p.id
  JOIN warehouselocations wl ON i.location_id = wl.id
  WHERE wl.warehouse_code = 'WH01' AND wl.shelf_code = 'A1'
    AND i.quantity > 0
  ORDER BY p.name
  LIMIT 100;
expected_shape: { columns: [ten_san_pham, so_luong, so_lo] }
```

### sql_ex_022 — Tìm sản phẩm theo tên (fuzzy intent resolved)
```yaml
id: sql_ex_022
intent_type: data_query
role_visibility: [owner, staff]
question_vi: "Tồn kho của Coca Cola hiện tại?"
assumptions: ["'Coca Cola' đã được K4 resolve thành product_id=123 tên='Coca-Cola lon 330ml'"]
sql: |
  SELECT
    p.name AS ten_san_pham,
    SUM(i.quantity) AS tong_ton,
    MAX(i.min_quantity) AS muc_toi_thieu
  FROM inventory i
  JOIN products p ON i.product_id = p.id
  WHERE p.id = :resolved_product_id
  GROUP BY p.id, p.name
  LIMIT 1;
expected_shape: { columns: [ten_san_pham, tong_ton, muc_toi_thieu], row_count: 1 }
note: ":resolved_product_id được điền từ K4 entity resolution"
```

---

## Quality Rules

- Mọi SQL phải SELECT-only, không có DML/DDL.
- Phải pass K5 policy trước khi thêm vào bộ này.
- Tên bảng/cột phải khớp K1 (lowercase PostgreSQL).
- Filter enum phải dùng giá trị thô từ K3.
- Có `LIMIT` trong mọi query.
- Có `expected_shape` cho mỗi ví dụ.
