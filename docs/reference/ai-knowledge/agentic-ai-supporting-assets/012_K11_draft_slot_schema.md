# K11 - Draft Slot Schema

```yaml
asset_id: K11
version: "2026.06.07"
source_of_truth: manual
refresh_policy: on_schema_change
consumers: [catalog_draft, inventory_draft, hitl_renderer, data_validator]
must_log_version_in_trace: true
```

## Purpose

Định nghĩa trường bắt buộc/tùy chọn cho từng loại nháp HITL để AI thu thập đúng thông tin trước khi tạo nháp và renderer biết hiển thị gì.

---

## Catalog Drafts

### catalog_draft — entity_type: product (Sản phẩm mới)

```yaml
draft_type: catalog_product
tool: catalog_draft
entity_type: product
table_target: products (qua Backend API)
requires_hitl: true
idempotency_key: "tenant_id + sku_code"

required_slots:
  - name: sku_code
    label_vi: "Mã SKU"
    type: string
    validation:
      pattern: "^[A-Za-z0-9\\-_]{3,50}$"
      unique_in: products.sku_code
    hitl_prompt: "Mã SKU của sản phẩm này là gì? (VD: SP-001, NUOC-500ML)"

  - name: product_name
    label_vi: "Tên sản phẩm"
    type: string
    validation:
      min_length: 2
      max_length: 255
    hitl_prompt: "Tên đầy đủ của sản phẩm?"

optional_slots:
  - name: category_id
    label_vi: "Danh mục"
    type: int (FK → categories.id)
    resolve_via: K4_categories
    hitl_prompt: "Sản phẩm thuộc danh mục nào? (có thể bỏ qua)"

  - name: sale_price
    label_vi: "Giá bán"
    type: decimal
    unit: VND
    validation:
      min: 0
    hitl_prompt: "Giá bán dự kiến?"

  - name: cost_price
    label_vi: "Giá vốn"
    type: decimal
    unit: VND
    sensitivity: cost_sensitive
    visible_roles: [owner]
    validation:
      min: 0
      warn_if: "cost_price >= sale_price (bán dưới giá vốn)"
    hitl_prompt: "Giá nhập vào (giá vốn)? Chỉ owner xem được."

  - name: barcode
    label_vi: "Mã vạch"
    type: string
    hitl_prompt: "Mã vạch sản phẩm? (tùy chọn)"

  - name: supplier_id
    label_vi: "Nhà cung cấp"
    type: int (FK → suppliers.id)
    resolve_via: K4_suppliers
    hitl_prompt: "Nhà cung cấp sản phẩm này?"

  - name: description
    label_vi: "Mô tả"
    type: text
    hitl_prompt: "Mô tả ngắn về sản phẩm?"

  - name: unit_name
    label_vi: "Đơn vị tính cơ sở"
    type: string
    default: "Cái"
    hitl_prompt: "Đơn vị tính? (VD: Cái, Lon, Chai, Thùng)"
```

### catalog_draft — entity_type: category (Danh mục mới)

```yaml
draft_type: catalog_category
tool: catalog_draft
entity_type: category
requires_hitl: true
idempotency_key: "tenant_id + category_code"

required_slots:
  - name: category_code
    label_vi: "Mã danh mục"
    type: string
    validation:
      pattern: "^[A-Z0-9\\-_]{3,20}$"
      unique_in: categories.category_code
    hitl_prompt: "Mã danh mục? (VD: CAT005, THUCPHAM)"

  - name: name
    label_vi: "Tên danh mục"
    type: string
    validation:
      min_length: 2
      max_length: 255

optional_slots:
  - name: parent_id
    label_vi: "Danh mục cha"
    type: int (FK → categories.id)
    resolve_via: K4_categories
    hitl_prompt: "Danh mục này nằm trong danh mục cha nào? (tùy chọn)"

  - name: description
    label_vi: "Mô tả"
    type: text
```

### catalog_draft — entity_type: supplier (Nhà cung cấp mới)

```yaml
draft_type: catalog_supplier
tool: catalog_draft
entity_type: supplier
requires_hitl: true
idempotency_key: "tenant_id + supplier_code"

required_slots:
  - name: supplier_code
    label_vi: "Mã nhà cung cấp"
    type: string
    validation:
      pattern: "^[A-Z0-9\\-_]{3,20}$"
      unique_in: suppliers.supplier_code

  - name: name
    label_vi: "Tên nhà cung cấp"
    type: string

optional_slots:
  - name: contact_person  label_vi: "Người liên hệ"   type: string   sensitivity: pii_name
  - name: phone           label_vi: "Điện thoại"       type: string   sensitivity: pii_phone
  - name: email           label_vi: "Email"            type: string   sensitivity: pii_email
  - name: address         label_vi: "Địa chỉ"          type: text
  - name: tax_code        label_vi: "Mã số thuế"       type: string
```

### catalog_draft — entity_type: customer (Khách hàng mới)

```yaml
draft_type: catalog_customer
tool: catalog_draft
entity_type: customer
requires_hitl: true
idempotency_key: "tenant_id + phone"

required_slots:
  - name: name
    label_vi: "Tên khách hàng"
    type: string

  - name: phone
    label_vi: "Số điện thoại"
    type: string
    sensitivity: pii_phone
    validation:
      pattern: "^0[0-9]{9}$"
      unique_in: customers.phone

optional_slots:
  - name: email    label_vi: "Email"    type: string  sensitivity: pii_email
  - name: address  label_vi: "Địa chỉ" type: text
```

---

## Inventory Drafts

### inventory_draft — entity_type: stock_receipt (Phiếu nhập kho mới)

```yaml
draft_type: inventory_stock_receipt
tool: inventory_draft
entity_type: stock_receipt
table_target: stockreceipts + stockreceiptdetails (qua Backend API)
requires_hitl: true
idempotency_key: "tenant_id + receipt_code (nếu có) hoặc conversation_id + timestamp"

required_slots:
  - name: supplier_id
    label_vi: "Nhà cung cấp"
    type: int (FK → suppliers.id)
    resolve_via: K4_suppliers
    hitl_prompt: "Nhập hàng từ nhà cung cấp nào?"

  - name: receipt_date
    label_vi: "Ngày nhập kho"
    type: date
    default: CURRENT_DATE
    hitl_prompt: "Ngày nhập kho? (mặc định hôm nay)"

  - name: lines
    label_vi: "Chi tiết sản phẩm nhập"
    type: array
    min_items: 1
    item_schema:
      required:
        - product_id    (resolve_via: K4_products)
        - quantity      (type: int, min: 1)
        - unit_id       (resolve_via: productunits JOIN product_id)
      optional:
        - cost_price    (type: decimal, unit: VND, sensitivity: cost_sensitive)
        - batch_number  (type: string)
        - expiry_date   (type: date)
    hitl_prompt: "Danh sách sản phẩm và số lượng nhập?"

optional_slots:
  - name: invoice_number
    label_vi: "Số hóa đơn NCC"
    type: string
    hitl_prompt: "Số hóa đơn của nhà cung cấp? (tùy chọn)"

  - name: notes
    label_vi: "Ghi chú"
    type: text
```

---

## HITL Flow Requirements

```yaml
hitl_flow:
  step1_collect:
    description: "AI hỏi từng required_slot còn thiếu, tối đa 2-3 câu/lần"
    rule: "Không hỏi optional_slot trừ khi user đề cập hoặc cần cho validation"

  step2_preview:
    description: "Hiển thị bảng tóm tắt nháp đã điền"
    template: K10.T3 (draft_preview_hitl)
    must_show:
      - Tất cả required_slots đã điền
      - Optional slots nếu đã cung cấp
      - Cảnh báo nếu có validation warn (VD: cost >= sale_price)
    must_not_show:
      - cost_price nếu user là staff

  step3_confirm:
    description: "User xác nhận → AI gọi Backend API commit"
    options: [confirm, edit, cancel]
    resume_token: "Lưu trong TurnContext.pending_hitl_payload"
    idempotency: "Dùng idempotency_key để tránh tạo trùng khi retry"

  step4_result:
    description: "Hiển thị kết quả commit"
    success_template: K10.T4 (draft_confirmed)
    failure: "Báo lỗi từ Backend API bằng ngôn ngữ thân thiện"

  expiry:
    ttl_hours: 24
    on_expire: "Báo user nháp đã hết hạn, đề nghị tạo lại"
    template: "Phiên xác nhận đã hết hạn. Vui lòng bắt đầu lại."
```

---

## Acceptance Checklist

- [ ] Mọi required_slot thiếu → HITL hỏi lại (không tạo nháp chưa đủ)
- [ ] cost_price ẩn với staff
- [ ] Confirm path idempotent với idempotency_key
- [ ] Commit dùng Backend API, không write DB trực tiếp
- [ ] Preview hiển thị đúng K14 (đơn tiền VND, ngày dd/MM/yyyy)
- [ ] Khi hết hạn → thông báo rõ ràng
- [ ] Entity resolution (product/supplier/category) dùng K4
