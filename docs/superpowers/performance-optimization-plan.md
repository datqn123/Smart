# Kế hoạch tối ưu hiệu năng Backend Smart ERP

> **Mục tiêu:** Giảm số lượng query DB, chuyển N+1 patterns thành batch operations, xử lý async các tác vụ không cần đồng bộ.

**Phạm vi:** 13 modules, ~348 Java files, ~23,800 LOC
**Database:** PostgreSQL 15+, Flyway migrations
**Phương pháp:** 5 workstreams độc lập, xử lý song song

---

## Workstream 1: Inventory — Core Service Fixes

**Người thực hiện:** Agent 1
**File chạm:**
- `inventory/receipts/lifecycle/StockReceiptLifecycleService.java`
- `inventory/dispatch/ManualStockDispatchService.java`
- `inventory/audit/service/AuditSessionService.java`
- `inventory/service/InventoryPatchService.java`
- `inventory/receipts/lifecycle/StockReceiptNotifier.java`
- `inventory/dispatch/StockDispatchNotifier.java`
- `inventory/dispatch/OrderLinkedDispatchService.java`

### Tasks:

- [ ] **1.1 StockReceiptLifecycleService — validateDetails() N+1 fix**
  - **Vấn đề:** 2N queries (productActive + findUnit) trong for-loop
  - **Fix:** Batch validation: `SELECT id, status FROM products WHERE id IN (:ids)` và `SELECT ... FROM productunits WHERE (id, product_id) IN (:tuples)`

- [ ] **1.2 StockReceiptLifecycleService — insertAllDetails() batch INSERT**
  - **Vấn đề:** N individual INSERTs trong for-loop
  - **Fix:** `namedJdbc.batchUpdate()` với `MapSqlParameterSource[]` batch

- [ ] **1.3 StockReceiptLifecycleService — approve() 3-4N loop**
  - **Vấn đề:** SELECT FOR UPDATE + UPDATE/INSERT + findBaseUnitId + insertInventoryLog per line
  - **Fix:** Pre-fetch baseUnitIds `Map<Integer, Integer>` trước loop; batch UPDATE inventory; batch INSERT inventory_logs

- [ ] **1.4 ManualStockDispatchService — finalizeDelivered() 3N loop**
  - **Vấn đề:** 3N round-trips (lockInventoryRow + deductInventory + insertInventoryLog)
  - **Fix:** `SELECT ... FROM inventory WHERE id IN (:ids) FOR UPDATE`; `UPDATE inventory SET quantity = quantity - CASE ... END WHERE id IN (:ids)`; batch INSERT logs

- [ ] **1.5 ManualStockDispatchService — dispatchHasPendingLines() redundant**
  - **Vấn đề:** 3-4 lần gọi/request
  - **Fix:** Cache local variable `boolean hasPendingLines = repo.dispatchHasPendingLines(dispatchId)`

- [ ] **1.6 AuditSessionService — applyVariance() 5N loop**
  - **Vấn đề:** lockInventory + updateInventory + findBaseUnitId + insertLog + setVarianceApplied
  - **Fix:** Batch lock, batch update, pre-fetch baseUnitIds map, batch insert logs

- [ ] **1.7 AuditSessionService — exception-driven retry loop**
  - **Vấn đề:** try-catch DuplicateKeyException với 20 lần retry
  - **Fix:** Sử dụng sequence table hoặc `SELECT nextval(...)` thay vì exception flow control

- [ ] **1.8 InventoryPatchService — notifyOwners N+1**
  - **Vấn đề:** Individual INSERT notification trong for-loop
  - **Fix:** `INSERT INTO notifications (...) SELECT ... FROM users WHERE role = 'Owner' AND status = 'Active' AND id <> :actorId`

- [ ] **1.9 StockReceiptNotifier, StockDispatchNotifier, OrderLinkedDispatchService — async notifications**
  - **Vấn đề:** Notification INSERTs chạy synchronous trong @Transactional HTTP thread
  - **Fix:** Extract notification thành `@Async` method hoặc `ApplicationEventPublisher` + `@TransactionalEventListener(phase = AFTER_COMMIT)`

**Kiểm tra:** Compile thành công, logic nghiệp vụ không đổi.

---

## Workstream 2: Inventory — Repository Query Rewrites

**Người thực hiện:** Agent 2
**File chạm:**
- `inventory/repository/InventoryListJdbcRepository.java`
- `inventory/repository/InventoryPatchJdbcRepository.java`
- `inventory/audit/repository/AuditSessionJdbcRepository.java`
- `inventory/dispatch/StockDispatchJdbcRepository.java`
- `inventory/receipts/lifecycle/StockReceiptLifecycleJdbcRepository.java`
- `inventory/receipts/repository/StockReceiptListJdbcRepository.java`
- `inventory/approvals/ApprovalsJdbcRepository.java`

### Tasks:

- [ ] **2.1 StockDispatchJdbcRepository — 5 subqueries → 1 LATERAL**
  - **Vấn đề:** `CASE WHEN EXISTS (SELECT ...) THEN (SELECT COUNT(*)) ELSE (SELECT COUNT(*) FROM inventorylogs ...) END` + 2 EXISTS — 5 subquery executions/row
  - **Fix:**
    ```sql
    LEFT JOIN LATERAL (
      SELECT COUNT(*)::int AS line_count,
             bool_or(sdl3.quantity > i3.quantity) AS has_shortage
      FROM stockdispatch_lines sdl3
      LEFT JOIN inventory i3 ON i3.id = sdl3.inventory_id
      WHERE sdl3.dispatch_id = sd.id
    ) line_agg ON true
    ```

- [ ] **2.2 AuditSessionJdbcRepository — 3 subqueries → 1 LATERAL**
  - **Vấn đề:** 3 correlated subqueries (total_lines, counted_lines, variance_lines)
  - **Fix:**
    ```sql
    LEFT JOIN LATERAL (
      SELECT COUNT(*)::int AS total_lines,
             COUNT(*) FILTER (WHERE is_counted)::int AS counted_lines,
             COUNT(*) FILTER (WHERE is_counted AND actual_quantity IS NOT NULL
                             AND actual_quantity <> system_quantity)::int AS variance_lines
      FROM inventoryauditlines l2 WHERE l2.session_id = s.id
    ) line_agg ON true
    ```

- [ ] **2.3 StockReceiptListJdbcRepository — line_count subquery → LATERAL**
  - **Vấn đề:** Correlated subquery COUNT(*) per row
  - **Fix:** LEFT JOIN LATERAL (SELECT COUNT(*) ...) ON true

- [ ] **2.4 ApprovalsJdbcRepository — reviewed_at::date CAST fix**
  - **Vấn đề:** `sr.reviewed_at::date >= :_from` — CAST trên indexed column
  - **Fix:** `sr.reviewed_at >= :_from::timestamptz` và `sr.reviewed_at < (:_to::timestamptz + interval '1 day')`

- [ ] **2.5 ApprovalsJdbcRepository — ORDER BY sr.created_at ASC không index**
  - **Vấn đề:** Sort trên non-indexed column
  - **Fix:** Thêm index `CREATE INDEX idx_sr_status_created ON stockreceipts(status, created_at DESC, id DESC)` hoặc cân nhắc nếu database chưa lớn.

- [ ] **2.6 InventoryListJdbcRepository — LIMIT/OFFSET string concat → named params**
  - **Vấn đề:** `" LIMIT " + q.limit() + " OFFSET " + offset` — không dùng parameter, không cache query plan
  - **Fix:** `LIMIT :_lim OFFSET :_off` với `src.addValue("_lim", q.limit())`

- [ ] **2.7 InventoryPatchJdbcRepository — COALESCE batch_number fix**
  - **Vấn đề:** `COALESCE(batch_number, '') = COALESCE(:_batch_key, '')` — function trên indexed column
  - **Fix:** `batch_number IS NOT DISTINCT FROM :_batch_key` — index-compatible

- [ ] **2.8 StockReceiptLifecycleService — loadOrThrow redundant re-read**
  - **Vấn đề:** Mỗi mutation method gọi `loadOrThrow(id)` ở cuối — 2 queries (header + details) đọc lại data vừa ghi
  - **Fix:** Construct response từ in-memory state hoặc return row vừa mutated

**Kiểm tra:** Compile thành công, mọi test query pass.

---

## Workstream 3: Catalog Fixes

**Người thực hiện:** Agent 3
**File chạm:**
- `catalog/service/CustomerService.java`
- `catalog/service/SupplierService.java`
- `catalog/repository/CustomerJdbcRepository.java`
- `catalog/repository/SupplierJdbcRepository.java`
- `catalog/service/CategoryService.java`
- `catalog/repository/CategoryJdbcRepository.java`
- `catalog/service/ProductService.java`
- `catalog/repository/ProductJdbcRepository.java`
- `catalog/service/ProductImageService.java`

### Tasks:

- [ ] **3.1 CustomerService.bulkDelete() — 3N → 3 queries**
  - **Vấn đề:** 3 for-loops, mỗi loop N queries xác thực (existsCustomerId, existsSalesOrder, existsPartnerDebt)
  - **Fix:** 3 batch queries: `SELECT id FROM customers WHERE id IN (:ids)`, `SELECT DISTINCT customer_id FROM salesorders WHERE customer_id IN (:ids)`, `SELECT DISTINCT customer_id FROM partnerdebts WHERE customer_id IN (:ids)`

- [ ] **3.2 SupplierService.bulkDelete() — 3N → 3 queries**
  - **Vấn đề:** Same pattern as 3.1
  - **Fix:** Tương tự 3.1 — batch SELECT queries

- [ ] **3.3 CustomerJdbcRepository.lockCustomersForUpdate() — N → 1 query**
  - **Vấn đề:** Individual SELECT FOR UPDATE trong for-loop
  - **Fix:** `SELECT ... FROM customers WHERE id IN (:ids) AND deleted_at IS NULL ORDER BY id FOR UPDATE`

- [ ] **3.4 SupplierJdbcRepository.lockSuppliersForUpdate() — N → 1 query**
  - **Vấn đề:** Same as 3.3
  - **Fix:** Same batch SELECT FOR UPDATE

- [ ] **3.5 CategoryService.list() — missing pagination**
  - **Vấn đề:** loadAllActive() load ALL categories vào memory, xây tree trong Java
  - **Fix:** Thêm page/limit params, filter bằng WHERE clause thay vì in-memory. Với tree format, dùng recursive CTE.

- [ ] **3.6 CategoryJdbcRepository.loadDetail() — N+1 breadcrumb**
  - **Vấn đề:** While loop gọi findActiveById() từng cấp (guard 256)
  - **Fix:** Recursive CTE: 
    ```sql
    WITH RECURSIVE ancestors AS (
      SELECT id, parent_id, name, 1 AS depth FROM categories WHERE id = :id AND deleted_at IS NULL
      UNION ALL
      SELECT c.id, c.parent_id, c.name, a.depth + 1
      FROM categories c INNER JOIN ancestors a ON c.id = a.parent_id
      WHERE c.deleted_at IS NULL AND a.depth < 100
    )
    SELECT id, name FROM ancestors ORDER BY depth DESC
    ```

- [ ] **3.7 CategoryJdbcRepository.loadAllActive() — redundant product aggregation**
  - **Vấn đề:** `LEFT JOIN (SELECT category_id, COUNT(*) FROM products GROUP BY category_id)` scan ALL products mỗi lần load category
  - **Fix:** Chỉ tính product_count khi cần (tree format). Dùng LATERAL join hoặc computed column.

- [ ] **3.8 ProductService.deleteBlockReason() — 3 queries → 1 query**
  - **Vấn đề:** 3 sequential guard queries per product delete
  - **Fix:** 
    ```sql
    SELECT CASE
      WHEN EXISTS (SELECT 1 FROM stockreceiptdetails WHERE product_id = :pid) THEN 'HAS_STOCK_RECEIPT'
      WHEN EXISTS (SELECT 1 FROM orderdetails WHERE product_id = :pid) THEN 'HAS_ORDER_LINES'
      WHEN COALESCE((SELECT SUM(quantity) FROM inventory WHERE product_id = :pid), 0) > 0 THEN 'HAS_STOCK'
    END AS block_reason
    ```

- [ ] **3.9 ProductImageService.persistGalleryAfterUploads() — clearPrimary trong loop**
  - **Vấn đề:** clearPrimaryForProduct gọi trong mỗi vòng lặp image upload
  - **Fix:** Đưa clearPrimaryForProduct và updateProductMainImageUrl ra ngoài loop, chỉ gọi 1 lần

**Kiểm tra:** Build thành công, CRUD operations hoạt động đúng.

---

## Workstream 4: Sales + Finance Fixes

**Người thực hiện:** Agent 4
**File chạm:**
- `sales/service/SalesOrderService.java`
- `sales/stock/RetailStockService.java`
- `sales/stock/RetailStockJdbcRepository.java`
- `sales/repository/SalesOrderJdbcRepository.java`
- `sales/repository/VoucherJdbcRepository.java`
- `finance/ledger/FinanceLedgerJdbcRepository.java`
- `finance/ledger/dispatch/DispatchLedgerPostingService.java`
- `finance/cashflow/CashflowMovementJdbcRepository.java`
- `finance/cashtx/CashTransactionJdbcRepository.java`
- `finance/ledger/FinanceLedgerPostingJdbcRepository.java`
- `finance/debts/PartnerDebtJdbcRepository.java`
- `dashboard/repository/DashboardJdbcRepository.java`

### Tasks:

- [ ] **4.1 SalesOrderService.validateLines() — N+1 → batch**
  - **Vấn đề:** 30+ queries cho 10 dòng (existsProductUnit, existsProductId, validateUnitPrice)
  - **Fix:** Batch: `SELECT id FROM products WHERE id IN (:ids)`, `SELECT product_id, unit_id FROM productunits WHERE (product_id, unit_id) IN (...)`, pre-fetch unit prices

- [ ] **4.2 SalesOrderService — batch INSERT order lines**
  - **Vấn đề:** Individual INSERT trong for-loop
  - **Fix:** `namedJdbc.batchUpdate()` với batch size

- [ ] **4.3 RetailStockService.FEFO — N+1 batch**
  - **Vấn đề:** 36+ queries cho 5 products (lockInventoryBuckets, findBaseUnitId, deductInventory, insertLog)
  - **Fix:** Pre-fetch baseUnitIds: `SELECT product_id, id FROM productunits WHERE product_id IN (:ids) AND is_base_unit = TRUE`. Batch lock: `SELECT ... WHERE product_id IN (:ids) FOR UPDATE`. Batch INSERT logs.

- [ ] **4.4 DispatchLedgerPostingService.computePrimaryCogs() — 2N batch**
  - **Vấn đề:** findBaseUnitId + findCurrentCostPrice per product trong loop
  - **Fix:** Batch lookup: `SELECT product_id, id FROM productunits WHERE product_id IN (:ids) AND is_base_unit = TRUE`, `SELECT DISTINCT ON (product_id) ... FROM productpricehistory WHERE product_id IN (:ids)`

- [ ] **4.5 FinanceLedgerJdbcRepository — window function + LIMIT**
  - **Vấn đề:** `SUM(amount) OVER (ORDER BY ...)` tính running balance qua ALL filtered rows dù chỉ return 1 page
  - **Fix:** Tính balance trong application code: lấy starting balance trước page, tính relative balance cho page rows

- [ ] **4.6 CashflowMovementJdbcRepository — CTE NOT MATERIALIZED**
  - **Vấn đề:** CTE mặc định materialized, không push-down LIMIT được
  - **Fix:** `movements AS NOT MATERIALIZED (...)`

- [ ] **4.7 CashTransactionJdbcRepository.countList — redundant LEFT JOINs**
  - **Vấn đề:** COUNT(*) query có LEFT JOIN users (không cần thiết)
  - **Fix:** `SELECT COUNT(*) FROM cashtransactions ct` không JOIN

- [ ] **4.8 SalesOrderService — redundant order code re-query**
  - **Vấn đề:** `findOrderCode(id)` query sau khi vừa insert
  - **Fix:** Make `updateOrderCode()` return the generated code

- [ ] **4.9 VoucherJdbcRepository — UPPER(TRIM(code)) fix**
  - **Vấn đề:** Function trên indexed column
  - **Fix:** Bỏ UPPER(TRIM()) nếu code đã được normalize khi insert, hoặc dùng expression index.

- [ ] **4.10 DashboardJdbcRepository — created_at::date CAST fix (3 queries)**
  - **Vấn đề:** `WHERE created_at::date IN (:today, :yesterday)` — không dùng được idx_so_created_at
  - **Fix:** `WHERE created_at >= :startOfDay AND created_at < :endOfDay` với tham số timestamptz

- [ ] **4.11 DashboardJdbcRepository — countOrdersByStatus(null) full scan**
  - **Vấn đề:** `SELECT COUNT(*) FROM salesorders` — scan ALL rows
  - **Fix:** Merge `countOrdersByStatus("Pending")` + `countOrdersByStatus(null)` thành 1 query với `COUNT(*) FILTER (WHERE status = 'Pending')`

**Kiểm tra:** Build thành công, dashboard và sales operations hoạt động đúng.

---

## Workstream 5: Cross-Cutting Fixes (Auth + AI + Dashboard + Users + Settings + Notifications + CustomInterface)

**Người thực hiện:** Agent 5
**File chạm:**
- `ai/controller/AiChatRelayController.java`
- `auth/service/AuthService.java`
- `auth/session/LoginBruteForceProtection.java`
- `auth/support/RolePermissionReader.java`
- `dashboard/service/DashboardService.java`
- `dashboard/repository/DashboardJdbcRepository.java`
- `settings/systemlogs/SystemLogsJdbcRepository.java`
- `settings/tablecolumns/service/TableColumnSettingsService.java`
- `settings/alerts/repository/AlertSettingsJdbcRepository.java`
- `users/service/UsersManagementService.java`
- `users/service/UserCreationService.java`
- `users/repository/UsersListJdbcRepository.java`
- `notifications/service/NotificationsService.java`
- `notifications/repository/NotificationJdbcRepository.java`
- `custominterface/service/CustomInterfaceService.java`
- `custominterface/repository/CustomInterfaceJdbcRepository.java`

### Tasks:

- [ ] **5.1 AiChatRelayController — unbounded thread pool fix**
  - **Vấn đề:** `Executors.newCachedThreadPool()` — unlimited threads, risk OOM
  - **Fix:** `Executors.newFixedThreadPool(Math.max(4, Runtime.getRuntime().availableProcessors() * 2))` hoặc `ThreadPoolExecutor` với bounded queue + rejection policy

- [ ] **5.2 AuthService.login() — 3 queries → 1 query**
  - **Vấn đề:** findActiveByEmailIgnoreCase + countActiveByEmailIgnoreCase + findByEmailIgnoreCase — redundant
  - **Fix:** Chỉ gọi `findActiveByEmailIgnoreCase()` 1 lần, check `user.getStatus()` từ kết quả

- [ ] **5.3 LoginBruteForceProtection — ConcurrentHashMap memory leak**
  - **Vấn đề:** Map entries không bao giờ expire nếu user fail 1-4 lần rồi thôi
  - **Fix:** `Caffeine.newBuilder().expireAfterWrite(30, TimeUnit.MINUTES).build()` hoặc Guava Cache

- [ ] **5.4 DashboardService — merge count queries**
  - **Vấn đề:** `countOrdersByStatus("Pending")` + `countOrdersByStatus(null)` = 2 separate COUNT(*) queries
  - **Fix:** 1 query: `SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE status = 'Pending') AS pending FROM salesorders`

- [ ] **5.5 SystemLogsJdbcRepository — context_data::text ILIKE fix**
  - **Vấn đề:** `COALESCE(s.context_data::text, '') ILIKE :_search` — CAST JSONB → text → ILIKE = full scan + per-row cast overhead
  - **Fix:** Remove context_data từ ILIKE search, hoặc dùng JSONB containment operator `@>` nếu cần search trong JSON

- [ ] **5.6 AlertSettingsJdbcRepository — non-sargable COALESCE pattern**
  - **Vấn đề:** `WHERE owner_id = COALESCE(:ownerId, owner_id)` — PostgreSQL không optimize được
  - **Fix:** Dynamic SQL WHERE clauses chỉ thêm khi param non-null, giống pattern SystemLogsJdbcRepository.buildFilter()

- [ ] **5.7 UsersListJdbcRepository — ILIKE users search**
  - **Vấn đề:** `ILIKE '%search%'` trên username, staff_code, full_name, email — không index
  - **Fix:** Query giữ nguyên. Khi database lớn, cân nhắc thêm pg_trgm extension + GIN indexes.

- [ ] **5.8 UsersManagementService.getById() — redundant double load**
  - **Vấn đề:** Load actor user + load target user (khi isSelf = true, cùng 1 user load 2 lần)
  - **Fix:** `User u = isSelf ? actor : userRepository.findWithRoleById(userId).orElseThrow(...)`

- [ ] **5.9 UserCreationService — redundant post-save re-query**
  - **Vấn đề:** `save(u)` → `findWithRoleById(saved.getId())` — role đã có trong memory
  - **Fix:** Construct response từ saved entity + targetRole đã có sẵn

- [ ] **5.10 NotificationsService — broadcast sequential INSERTs**
  - **Vấn đề:** For-loop INSERT cho mỗi recipient
  - **Fix:** `namedJdbc.batchUpdate()` với batch parameters

- [ ] **5.11 CustomInterfaceService — menuTree() load toàn bộ tree sau mỗi mutation**
  - **Vấn đề:** Mỗi CUD operation gọi menuTree() rebuild full tree
  - **Fix:** Return response đơn giản hơn từ mutation, không load lại toàn bộ tree. Hoặc compute etag incrementally.

- [ ] **5.12 CustomInterfaceJdbcRepository — SELECT * → explicit column list**
  - **Vấn đề:** Mọi query SELECT * từ custom_menu_folders và custom_menu_pages
  - **Fix:** Chỉ SELECT các column cần thiết cho từng query

- [ ] **5.13 GlobalTableColumnSettingsService — loadAll → filter in memory**
  - **Vấn đề:** `repo.findAll()` load ALL rows, filter in-memory theo scope
  - **Fix:** Add `WHERE table_key IN (:keys)` parameter

- [ ] **5.14 FinanceLedgerJdbcRepository — LIMIT/OFFSET string concat → named params**
  - **Vấn đề:** `" LIMIT " + limit + " OFFSET " + offset`
  - **Fix:** `LIMIT :_lim OFFSET :_off` với named parameters

**Kiểm tra:** Build thành công, auth/dashboard/notifications hoạt động đúng.

---

## Rủi ro và mitigation

| Rủi ro | Mitigation |
|--------|------------|
| Agent 1 và Agent 2 cùng sửa inventory service/repo — conflict | Agent 1 sửa service layer, Agent 2 sửa repository layer — khác file hoàn toàn |
| Transaction behavior thay đổi khi extract async | @TransactionalEventListener phase = AFTER_COMMIT đảm bảo chỉ chạy sau khi transaction chính commit |
| Batch INSERT thay đổi order | Thêm ORDER BY trong SELECT nếu cần guarantee order |
| Thread pool sizing sai | Dùng `availableProcessors() * 2` cho I/O bound, có thể config sau |

## Integration Check

Sau khi tất cả agent hoàn thành:
1. `mvn compile` — kiểm tra compile
2. Verify logic không đổi: endpoint nào trả về data khác trước
3. Rollback từng agent nếu có issue
