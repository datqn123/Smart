-- Semantic descriptions for critical columns.
-- Each description tells LLM what kind of data lives in the column.
-- Uses UPSERT (ON CONFLICT DO UPDATE) to replace basic V45 descriptions.
-- Format: (table_name, column_name, description)

INSERT INTO ai_column_description (table_name, column_name, description)
VALUES
    -- Categories
    ('categories', 'name',
     'Tên danh mục sản phẩm (vd: Gạo, Điện tử, Thực phẩm, Nước giải khát, Hóa mỹ phẩm). '
     'Khi user hỏi theo danh mục (gạo, điện tử...), FILTER bằng cột này, KHÔNG filter products.name.'),

    -- Products
    ('products', 'name',
     'Tên sản phẩm cụ thể (vd: Gạo ST25 5kg, Nước mắm Nam Ngư 500ml, Bột giặt OMO 1kg). '
     'Không chứa tên danh mục chung chung. Để lọc theo danh mục, dùng categories.name qua JOIN categories.'),

    ('products', 'status',
     'Trạng thái master data: Active (đang kinh doanh) hoặc Inactive (ngưng). '
     'Không dùng status để xác định hàng tồn / hết hàng.'),

    -- Inventory
    ('inventory', 'quantity',
     'Số lượng tồn kho thực tế hiện tại (snapshot). Đây là fact, không tính toán từ chứng từ. '
     'out-of-stock = quantity = 0; low_stock = quantity > 0 AND quantity <= min_quantity.'),

    -- Finance Ledger
    ('financeledger', 'amount',
     'Số tiền giao dịch tài chính. Dương với doanh thu/thu, âm với chi phí/trả hàng. '
     'transaction_type xác định bản chất: SalesRevenue = doanh thu, PurchaseCost = giá vốn, OperatingExpense = chi phí.'),

    ('financeledger', 'transaction_type',
     'Loại giao dịch tài chính: SalesRevenue (doanh thu), PurchaseCost (giá vốn), '
     'OperatingExpense (chi phí), Refund (trả hàng/hoàn tiền).'),

    ('financeledger', 'transaction_date',
     'Ngày ghi nhận giao dịch tài chính (ngày chứng từ, không phải ngày tạo). '
     'Dùng cho lọc thời gian: tháng/năm/quý.'),

    -- Sales Orders
    ('salesorders', 'order_channel',
     'Kênh bán hàng: Retail (bán lẻ tại quầy/POS), Wholesale (bán sỉ), Return (đơn trả). '
     'Chỉ filter Retail khi user hỏi cụ thể "bán lẻ" hoặc "tại quầy".'),

    ('salesorders', 'status',
     'Trạng thái đơn hàng: Pending, Processing, Partial, Shipped, Delivered, Cancelled. '
     'Đơn đã huỷ (Cancelled) không tính vào doanh số.'),

    -- Stock Receipts
    ('stockreceipts', 'status',
     'Trạng thái phiếu nhập: Draft, Pending, Approved, Rejected. '
     'Chỉ Approved mới là nhập kho chính thức.'),

    -- Stock Dispatches
    ('stockdispatches', 'status',
     'Trạng thái phiếu xuất: Pending, Full, Partial, Cancelled, WaitingDispatch, Delivering, Delivered. '
     'Đơn đã huỷ (Cancelled) không tính. active rows: deleted_at IS NULL.')
ON CONFLICT (table_name, column_name) DO UPDATE
    SET description = EXCLUDED.description,
        updated_at = CURRENT_TIMESTAMP;
