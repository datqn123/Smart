-- Task: perf(catalog) N+1 fix in ProductService.bulkDelete() — hỗ trợ EXISTS trên product_id
-- Bổ sung index cho hai cột FK product_id mà chưa có index ở V1 baseline
-- nhằm tránh full-table scan khi EXISTS (SELECT 1 FROM stockreceiptdetails WHERE product_id = p.id)
-- hoặc EXISTS (SELECT 1 FROM orderdetails WHERE product_id = p.id) trong
-- ProductJdbcRepository.findBulkDeleteBlockReasons (1 query batch cho N ids).

CREATE INDEX IF NOT EXISTS idx_srd_product_id
    ON stockreceiptdetails (product_id);

CREATE INDEX IF NOT EXISTS idx_od_product_id
    ON orderdetails (product_id);
