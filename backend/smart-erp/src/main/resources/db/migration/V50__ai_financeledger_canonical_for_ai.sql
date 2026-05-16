-- Ledger-first AI registry: financeledger is the canonical fact table for revenue/expense/cashflow
-- after unified business postings. salesorders is a dimension table via reference_type/reference_id.

UPDATE ai_table_description AS t
SET description = v.description,
    updated_at  = CURRENT_TIMESTAMP
FROM (
    VALUES
        ('financeledger', $fl$Nguồn chuẩn (canonical) cho báo cáo thu/chi/doanh thu/chi phí/dòng tiền sau khi nghiệp vụ hoàn tất: mọi bút toán đều ghi vào sổ cái này. Chức năng: fact table kế toán với transaction_type (SalesRevenue, PurchaseCost, OperatingExpense, Refund), amount (dương=thu, âm=chi), transaction_date, fund_id, reference_type + reference_id (đa hình tới SalesOrder, StockReceipt, CashTransaction, …). Ảnh hưởng tới: tổng doanh thu, chi phí, lãi lỗ, số dư quỹ — dùng SUM(amount) và lọc transaction_type, KHÔNG dùng salesorders làm nguồn tổng hợp thu/chi. Bảng liên quan: cash_funds (fund_id), users (created_by), cashtransactions (finance_ledger_id). Đọc khi: doanh thu, thu tiền, chi phí, chi tiền, dòng tiền, lãi lỗ, sổ cái, báo cáo tài chính, theo tháng/quỹ; drill-down đơn hàng qua reference_type='SalesOrder'.$fl$),
        ('salesorders', $so$Bảng chiều (dimension) đơn bán: khách, kênh order_channel, thanh toán, trạng thái, mã đơn — KHÔNG phải nguồn chuẩn tổng doanh thu đã ghi sổ (dùng financeledger + SalesRevenue). Chức năng: join từ financeledger khi cần phân tích theo kênh/khách/trạng thái đơn: ON fl.reference_type = 'SalesOrder' AND fl.reference_id = salesorders.id. Ảnh hưởng tới: KPI bán theo kênh, công nợ KH, xuất kho. Bảng liên quan: customers, orderdetails, stockdispatches. Đọc khi: doanh thu theo kênh Retail/Wholesale; theo khách; trạng thái đơn; chi tiết đơn — luôn kết hợp financeledger làm fact.$so$)
) AS v(table_name, description)
WHERE t.table_name = v.table_name;

UPDATE ai_column_description AS t
SET description = v.description,
    updated_at  = CURRENT_TIMESTAMP
FROM (
    VALUES
        ('financeledger', 'amount', 'Số tiền bút toán (DECIMAL). Tổng doanh thu: SUM(amount) WHERE transaction_type=''SalesRevenue''. Chi phí: các type PurchaseCost/OperatingExpense. Dùng transaction_date cho báo cáo theo kỳ.'),
        ('financeledger', 'transaction_type', 'Bắt buộc lọc: SalesRevenue (doanh thu), PurchaseCost, OperatingExpense, Refund. Không SUM toàn bộ ledger cho doanh thu.'),
        ('financeledger', 'reference_type', 'Loại chứng từ nguồn. Join salesorders: reference_type=''SalesOrder'' AND reference_id = salesorders.id.'),
        ('financeledger', 'reference_id', 'ID chứng từ nguồn — chỉ join bảng đích khi reference_type khớp (không join mù).'),
        ('salesorders', 'final_amount', 'Tổng đơn (generated). Chỉ dùng khi phân tích pipeline đơn; báo cáo thu đã ghi sổ lấy từ financeledger.'),
        ('salesorders', 'order_channel', 'Retail | Wholesale — dimension khi join từ financeledger qua SalesOrder reference.')
) AS v(table_name, column_name, description)
WHERE t.table_name = v.table_name AND t.column_name = v.column_name;
