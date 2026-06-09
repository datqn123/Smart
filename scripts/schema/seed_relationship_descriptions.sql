-- Semantic descriptions for FK relationships.
-- Each description tells LLM what the relationship means in business terms.
-- Uses UPSERT (ON CONFLICT DO UPDATE) for idempotency.

INSERT INTO ai_relationship_description (from_table, from_column, to_table, to_column, description)
VALUES
    ('products', 'category_id', 'categories', 'id',
     'Mỗi sản phẩm thuộc về một danh mục. Khi user hỏi "gạo", "điện tử", "thực phẩm" — '
     'đó là categories.name. JOIN categories và filter c.name, KHÔNG filter products.name.'),

    ('inventory', 'product_id', 'products', 'id',
     'Mỗi dòng tồn kho tương ứng với một sản phẩm. JOIN products để lấy tên, mã SKU, min_quantity.'),

    ('inventory', 'location_id', 'warehouselocations', 'id',
     'Mỗi dòng tồn kho thuộc một vị trí kho. JOIN warehouselocations để lấy tên kho/giá.'),

    ('stockreceiptdetails', 'receipt_id', 'stockreceipts', 'id',
     'Chi tiết của phiếu nhập — mỗi dòng là một sản phẩm trong phiếu nhập. '
     'stockreceipts.status phải là Approved mới tính.'),

    ('stockreceiptdetails', 'product_id', 'products', 'id',
     'Sản phẩm trong phiếu nhập. JOIN products để lấy tên/mã.'),

    ('stockdispatch_lines', 'dispatch_id', 'stockdispatches', 'id',
     'Chi tiết của phiếu xuất — mỗi dòng là một sản phẩm trong phiếu xuất.'),

    ('stockdispatch_lines', 'product_id', 'products', 'id',
     'Sản phẩm trong phiếu xuất.'),

    ('orderdetails', 'order_id', 'salesorders', 'id',
     'Chi tiết đơn hàng — mỗi dòng là một sản phẩm trong đơn. salesorders.status != Cancelled.'),

    ('orderdetails', 'product_id', 'products', 'id',
     'Sản phẩm trong đơn hàng. Dùng để tính số lượng bán.'),

    ('financeledger', 'reference_type', NULL, NULL,
     'Phân loại tham chiếu: SalesOrder, PurchaseInvoice, ... '
     'JOIN với bảng tương ứng theo reference_id khi cần thông tin chi tiết.'),

    ('productpricehistory', 'product_id', 'products', 'id',
     'Lịch sử giá sản phẩm. Mỗi sản phẩm có nhiều dòng giá theo thời gian. '
     'JOIN bằng LATERAL hoặc DISTINCT ON để lấy giá mới nhất.'),

    ('productpricehistory', 'unit_id', 'productunits', 'id',
     'Đơn vị tính của giá. Giá theo đơn vị cơ sở khi is_base_unit = TRUE.')
ON CONFLICT (from_table, from_column, to_table, to_column) DO UPDATE
    SET description = EXCLUDED.description,
        updated_at = CURRENT_TIMESTAMP;
