-- PRD finance-ledger-unified-business-postings — Task 2: hỗ trợ lọc COGS theo phiếu xuất
CREATE INDEX IF NOT EXISTS idx_financeledger_ref_dispatch
    ON financeledger (reference_type, reference_id)
    WHERE reference_type = 'StockDispatch';
