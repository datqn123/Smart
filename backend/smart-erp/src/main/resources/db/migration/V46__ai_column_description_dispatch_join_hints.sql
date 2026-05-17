-- Bổ sung mô tả cột để tránh join sai: stockdispatch_lines.dispatch_id là FK tới phiếu xuất (stockdispatches.id), không phải salesorders.id.

UPDATE ai_column_description
SET description = 'FK tới stockdispatches.id (phiếu xuất). Không dùng salesorders.id ở đây — nối đơn: stockdispatches.order_id = salesorders.id rồi stockdispatch_lines.dispatch_id = stockdispatches.id.',
    updated_at = CURRENT_TIMESTAMP
WHERE table_name = 'stockdispatch_lines'
  AND column_name = 'dispatch_id';

UPDATE ai_column_description
SET description = 'FK salesorders.id (đơn nguồn của phiếu xuất, có thể NULL). Chuỗi đúng tới dòng xuất: salesorders → stockdispatches (order_id) → stockdispatch_lines (dispatch_id).',
    updated_at = CURRENT_TIMESTAMP
WHERE table_name = 'stockdispatches'
  AND column_name = 'order_id';
