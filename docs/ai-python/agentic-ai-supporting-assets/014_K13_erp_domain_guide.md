# K13 - ERP Domain Guide

```yaml
asset_id: K13
version: "2026.06.07"
source_of_truth: manual
refresh_policy: manual_review
consumers: [intent, planner, answer_composer]
must_log_version_in_trace: true
```

## Purpose

Mô tả nghiệp vụ ngắn gọn của từng lĩnh vực ERP để intent hiểu ngữ cảnh câu hỏi, planner chọn tool đúng, và answer_composer dùng ngôn ngữ nghiệp vụ chuẩn.

---

## Domains

### products_catalog — Sản phẩm & Danh mục
```yaml
domain: products_catalog
summary_vi: "Quản lý danh mục hàng hóa: thêm/sửa/ẩn sản phẩm, phân nhóm danh mục, theo dõi giá."
key_tables: [products, categories, productunits, productpricehistory, productimages]
key_actions:
  - "Tra cứu thông tin sản phẩm (tên, SKU, giá bán, danh mục)"
  - "Thêm sản phẩm mới qua AI draft (HITL)"
  - "Kiểm tra sản phẩm nào đang active/inactive"
common_questions:
  - "Sản phẩm [tên] có mã SKU là gì?"
  - "Danh mục nào có nhiều sản phẩm nhất?"
  - "Giá bán hiện tại của [tên SP] là bao nhiêu?"
ai_capabilities: [data_query, catalog_draft]
related_domains: [inventory, orders]
notes:
  - "Giá sản phẩm lấy từ productpricehistory, không phải cột trong products"
  - "Giá vốn (cost_price) chỉ owner xem được"
  - "Sản phẩm Inactive vẫn còn trong DB nhưng không bán nữa"
```

### inventory — Tồn kho & Kho hàng
```yaml
domain: inventory
summary_vi: "Theo dõi số lượng hàng tồn tại từng vị trí kho, lô hàng, hạn sử dụng. Cảnh báo khi tồn thấp hoặc sắp hết hạn."
key_tables: [inventory, warehouselocations, inventorylogs, inventoryauditsessions, inventoryauditlines]
key_actions:
  - "Kiểm tra tồn kho tổng hoặc theo sản phẩm/danh mục/vị trí"
  - "Xem sản phẩm sắp hết hàng (quantity <= min_quantity)"
  - "Xem hàng sắp hết hạn sử dụng"
  - "Tra cứu lịch sử biến động kho (nhập/xuất/điều chuyển)"
  - "Nhập kho mới qua AI draft (HITL)"
common_questions:
  - "Tồn kho hiện tại của [SP] còn bao nhiêu?"
  - "Sản phẩm nào sắp hết hàng?"
  - "Hàng nào sắp hết hạn trong 30 ngày?"
  - "Kho WH01 kệ A1 còn những gì?"
ai_capabilities: [data_query, inventory_draft]
related_domains: [products_catalog, orders, receipts]
lifecycle:
  - "Nhập hàng: StockReceipt Approved → inventory.quantity tăng + InventoryLog INBOUND"
  - "Xuất hàng: StockDispatch Full → inventory.quantity giảm + InventoryLog OUTBOUND"
  - "Điều chỉnh: Audit session → InventoryLog ADJUSTMENT"
notes:
  - "Tổng tồn = SUM(quantity) per product_id khi SP ở nhiều vị trí/lô"
  - "quantity luôn theo đơn vị cơ sở (is_base_unit=TRUE)"
  - "min_quantity=0 nghĩa là chưa đặt ngưỡng cảnh báo"
```

### orders — Đơn hàng bán
```yaml
domain: orders
summary_vi: "Quản lý đơn bán lẻ/bán sỉ/trả hàng, theo dõi trạng thái từ Pending → Delivered hoặc Cancelled."
key_tables: [salesorders, orderdetails, customers, stockdispatches]
key_actions:
  - "Xem danh sách đơn theo trạng thái hoặc kênh bán"
  - "Theo dõi đơn cụ thể (mã đơn, khách, sản phẩm)"
  - "Thống kê số đơn, giá trị đơn theo kỳ"
  - "Top sản phẩm bán chạy"
common_questions:
  - "Hôm nay có bao nhiêu đơn hàng?"
  - "Đơn [mã] gồm những sản phẩm gì?"
  - "Đơn nào chưa thanh toán?"
  - "Top 10 sản phẩm bán chạy tháng này?"
ai_capabilities: [data_query, chart_report]
related_domains: [customers, inventory, finance]
lifecycle:
  - Pending → Processing → Partial/Shipped → Delivered (hoàn thành)
  - Pending → Cancelled (hủy)
  - Partial → con đơn (parent_order_id) nếu thiếu hàng backorder
notes:
  - "salesorders không phải nguồn doanh thu đã ghi sổ — dùng financeledger cho báo cáo tài chính"
  - "Đơn Return: order_channel='Return', ref_sales_order_id trỏ về đơn gốc"
  - "final_amount = total_amount - discount_amount (generated column)"
```

### customers — Khách hàng
```yaml
domain: customers
summary_vi: "Danh sách khách hàng, lịch sử mua hàng, điểm tích lũy, công nợ."
key_tables: [customers, salesorders, partnerdebts]
key_actions:
  - "Tra cứu thông tin khách hàng"
  - "Xem lịch sử mua hàng của khách"
  - "Top khách hàng mua nhiều nhất"
  - "Kiểm tra công nợ của khách"
common_questions:
  - "Khách [tên] mua hàng bao nhiêu lần rồi?"
  - "Khách hàng nào mua nhiều nhất tháng này?"
  - "Khách nào còn đang nợ tiền?"
ai_capabilities: [data_query]
related_domains: [orders, finance]
notes:
  - "PII: phone/email chỉ hiển thị khi owner yêu cầu rõ ràng"
  - "Khách xóa mềm: deleted_at IS NOT NULL, mặc định loại trừ"
  - "Tổng chi tiêu không có cột riêng, tính qua financeledger JOIN salesorders"
```

### suppliers — Nhà cung cấp
```yaml
domain: suppliers
summary_vi: "Danh sách nhà cung cấp, lịch sử nhập hàng, công nợ với NCC."
key_tables: [suppliers, stockreceipts, partnerdebts]
key_actions:
  - "Tra cứu thông tin nhà cung cấp"
  - "Xem lịch sử nhập hàng từ NCC"
  - "Kiểm tra còn nợ NCC bao nhiêu"
common_questions:
  - "Nhà cung cấp [tên] cung cấp những sản phẩm gì?"
  - "Phiếu nhập nào từ [NCC] đang chờ duyệt?"
  - "Cửa hàng đang nợ [NCC] bao nhiêu tiền?"
ai_capabilities: [data_query]
related_domains: [inventory, receipts, finance]
```

### receipts — Phiếu nhập kho
```yaml
domain: receipts
summary_vi: "Quản lý phiếu nhập hàng từ nhà cung cấp. Chỉ khi Approved mới cập nhật tồn kho và ghi sổ cái."
key_tables: [stockreceipts, stockreceiptdetails, suppliers]
key_actions:
  - "Xem phiếu nhập theo trạng thái (Draft/Pending/Approved/Rejected)"
  - "Tổng giá trị nhập trong kỳ"
  - "Tạo phiếu nhập mới qua AI draft (HITL)"
common_questions:
  - "Phiếu nhập nào đang chờ duyệt?"
  - "Tháng này đã nhập kho bao nhiêu tiền hàng?"
  - "Thêm phiếu nhập mới cho [NCC]"
ai_capabilities: [data_query, inventory_draft]
lifecycle:
  - Draft → Pending (gửi duyệt) → Approved (nhập kho + ghi sổ) / Rejected
  - Chỉ Approved mới ảnh hưởng inventory.quantity và financeledger
```

### finance — Tài chính (chỉ Owner)
```yaml
domain: finance
summary_vi: "Sổ cái tài chính, thu chi, doanh thu, lợi nhuận, dòng tiền, công nợ. Chỉ Owner xem được."
key_tables: [financeledger, cashtransactions, partnerdebts]
sensitive: true
visible_roles: [owner]
key_actions:
  - "Xem doanh thu theo kỳ (ngày/tháng/quý/năm)"
  - "Xem chi phí và lợi nhuận"
  - "Xem dòng tiền"
  - "Quản lý công nợ KH/NCC"
  - "Ghi phiếu thu chi thủ công"
common_questions:
  - "Doanh thu tháng này là bao nhiêu?"
  - "Lợi nhuận gộp quý 2 thế nào?"
  - "Công nợ tổng cộng hiện tại là bao nhiêu?"
  - "Dòng tiền tháng này âm hay dương?"
ai_capabilities: [data_query, chart_report]
related_domains: [orders, receipts, customers, suppliers]
key_principle: "financeledger là nguồn CHUẨN — không dùng salesorders.final_amount làm nguồn doanh thu tổng hợp"
```

### ai_draft_hitl — Nháp AI & Xác nhận
```yaml
domain: ai_draft_hitl
summary_vi: "Luồng tạo nháp dữ liệu qua AI, chờ user xem lại và xác nhận trước khi ghi vào hệ thống."
key_tables: [ai_catalog_draft, ai_inventory_draft]
draft_types:
  - catalog: [product, category, supplier, customer]
  - inventory: [stock_receipt]
flow:
  - "1. User yêu cầu tạo [loại thực thể]"
  - "2. AI thu thập thông tin, hỏi thêm nếu thiếu trường bắt buộc"
  - "3. AI tạo nháp, hiển thị để user xem lại (HITL)"
  - "4. User xác nhận → AI commit qua Backend API"
  - "5. Ghi lại kết quả vào commit_result"
notes:
  - "Nháp có hạn expires_at — nếu hết hạn phải tạo lại"
  - "Chỉ owner mới được tạo catalog_draft và inventory_draft"
  - "Không bao giờ ghi trực tiếp vào products/stockreceipts mà không qua API"
```

### approvals — Phê duyệt
```yaml
domain: approvals
summary_vi: "Luồng phê duyệt phiếu nhập kho. Owner duyệt → Approved; Từ chối → Rejected."
key_tables: [stockreceipts]
key_actions:
  - "Xem danh sách phiếu chờ duyệt"
  - "Kiểm tra phiếu đã được duyệt chưa"
common_questions:
  - "Hôm nay có bao nhiêu phiếu nhập chờ duyệt?"
  - "Phiếu [mã] đã được duyệt chưa?"
ai_capabilities: [data_query]
notes:
  - "AI không thể thực hiện approve/reject — chỉ đọc và báo cáo trạng thái"
```

---

## Cross-Domain Relationships

```
products ←→ inventory:      1 SP có thể có nhiều dòng tồn kho (nhiều vị trí/lô)
products ←→ orderdetails:   1 SP xuất hiện trong nhiều đơn hàng
salesorders → financeledger: 1 đơn → 1 bút toán SalesRevenue khi hoàn tất
stockreceipts → financeledger: 1 phiếu nhập Approved → 1 bút toán PurchaseCost
salesorders ←→ stockdispatches: 1 đơn có thể có nhiều phiếu xuất (partial)
customers ←→ partnerdebts:  công nợ KH theo từng hợp đồng/kỳ
suppliers ←→ partnerdebts:  công nợ NCC theo từng kỳ nhập hàng
```
