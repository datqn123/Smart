# TECH PLAN - Xu ly bottleneck Java Backend

> Agent: TECH_LEAD
> Ngay cap nhat: 10/06/2026
> Scope: backend/smart-erp (Java Spring Boot)

## 1. Tong quan van de

| # | Vi tri | Loai | muc do | Mo ta |
|---|--------|------|--------|-------|
| 1 | `ProductService.bulkDelete()` | N+1 Query | **Nghiem trong** | 4N+1 queries cho N san pham |
| 2 | `CategoryService.patch()` | Memory O(E) | Trung binh | Load toan bo parent edges de check cycle |
| 3 | `InventoryListService.list()` | Redundant queries | Thap | 3 queries rieng biet cho cung filter |

---

## 2. Task 1 — Fix N+1 trong `ProductService.bulkDelete()`

### 2.1. Hien trang

File: `ProductService.java:461-490`

```
Vong 1: for (pid : ids) → existsProductId(pid)         → N queries
Vong 2: for (pid : ids) → deleteBlockReason(pid)       → 3N queries
          + existsStockReceiptDetail(pid)
          + existsOrderDetail(pid)
          + sumInventoryQuantity(pid)
Vong 3: lockProductsForUpdate(ids)                     → 1 query
Vong 4: deleteProducts(ids)                            → 1 query
```

**Tong: 4N + 2 queries** cho N san pham. Voi 100 san pham = 402 queries.

### 2.2. Giai phap

Them cac batch methods vao `ProductJdbcRepository`:

**Method 1: `findExistingProductIds(List<Integer> ids)`**
- SQL: `SELECT id FROM products WHERE id IN (:ids)`
- Tra ve: `Set<Integer>` cac id ton tai
- So sanh size de phat hien id khong ton tai

**Method 2: `findBulkDeleteBlockReasons(List<Integer> ids)`**
- SQL: 1 query duy nhat dung `LEFT JOIN` + `GROUP BY` de tra ve map `id → reason`
- Logic:
  ```sql
  SELECT p.id,
    CASE
      WHEN EXISTS (SELECT 1 FROM stockreceiptdetails srd WHERE srd.product_id = p.id) THEN 'HAS_STOCK_RECEIPT'
      WHEN EXISTS (SELECT 1 FROM orderdetails od WHERE od.product_id = p.id) THEN 'HAS_ORDER_LINES'
      WHEN COALESCE(inv.qty, 0) > 0 THEN 'HAS_STOCK'
      ELSE NULL
    END AS block_reason
  FROM unnest(:ids::int[]) AS p(id)
  LEFT JOIN LATERAL (SELECT SUM(quantity) AS qty FROM inventory WHERE product_id = p.id) inv ON true
  ```
- Tra ve: `Map<Integer, String>` — chi chua cac id bi block

### 2.3. Ket qua sau fix

| Truoc | Sau |
|-------|-----|
| 4N + 2 queries | **4 queries** (batch exists + batch reasons + lock + delete) |
| O(N) DB round-trips | O(1) DB round-trips |

### 2.4. Thay doi can thiet

| File | Thay doi |
|------|----------|
| `ProductJdbcRepository.java` | Them `findExistingProductIds()`, `findBulkDeleteBlockReasons()` |
| `ProductService.java` | Viet lai `bulkDelete()` dung batch methods |

---

## 3. Task 2 — Toi uu `CategoryService.patch()` cycle check

### 3.1. Hien trang

File: `CategoryService.java:213`

```java
List<CategoryParentEdgeRow> edges = categoryJdbcRepository.loadAllActiveParentEdges();
```

Load **toan bo** edges (id, parentId) cua categories dang hieu luc de check co tao cycle hay khong.

- Memory: O(E) voi E = so categories active
- Dung BFS de tim duong di tu `categoryId` → `newParentId`

### 3.2. Danh gia

- **Neu so categories < 1000**: Van de khong nghiem trong, memory khong dang ke.
- **Neu so categories > 1000**: Can toi uu.

### 3.3. Giai phap (neu can toi uu)

Dung PostgreSQL recursive CTE de chi query path tu node hien tai:

```sql
WITH RECURSIVE ancestors AS (
  SELECT id, parent_id FROM categories
  WHERE id = :categoryId AND deleted_at IS NULL
  UNION ALL
  SELECT c.id, c.parent_id FROM categories c
  INNER JOIN ancestors a ON a.parent_id = c.id
  WHERE c.deleted_at IS NULL
)
SELECT id FROM ancestors WHERE id = :newParentId
```

- Chi load ancestors cua current node, khong load toan bo tree
- Memory: O(depth) thay vi O(E)

### 3.4. Thay doi can thiet

| File | Thay doi |
|------|----------|
| `CategoryJdbcRepository.java` | Them `wouldCreateCycle(long categoryId, long newParentId)` |
| `CategoryService.java` | Thay the `loadAllActiveParentEdges()` + BFS bang method moi |

---

## 4. Task 3 — Gop queries trong `InventoryListService.list()`

### 4.1. Hien trang

File: `InventoryListService.java:47-53`

```java
InventorySummaryData summary = listRepo.loadSummary(q);  // Query 1 (aggregate)
long total = listRepo.countRows(q);                      // Query 2 (COUNT)
List<InventoryListRow> rows = listRepo.loadPage(q);      // Query 3 (data)
```

### 4.2. Danh gia

- **Query 1 va 2** cung dung `BASE_FROM` + filter, chi khac SELECT columns
- Co the gop thanh 1 query duy nhat

### 4.3. Giai phap

Gop `loadSummary()` va `countRows()` thanh 1 method:

```sql
SELECT
  COUNT(*)::bigint AS total_rows,
  COUNT(*)::bigint AS total_skus,
  COALESCE(SUM(...), 0) AS total_value,
  COALESCE(SUM(CASE WHEN low_stock THEN 1 ELSE 0 END), 0) AS low_stock_count,
  COALESCE(SUM(CASE WHEN expiring THEN 1 ELSE 0 END), 0) AS expiring_soon_count
FROM ...
WHERE ...
```

### 4.4. Ket qua

| Truoc | Sau |
|-------|-----|
| 3 queries | **2 queries** (summary+count gop, data rieng) |

### 4.5. Thay doi can thiet

| File | Thay doi |
|------|----------|
| `InventoryListJdbcRepository.java` | Them `loadSummaryWithCount(q)` tra ve ca summary + total |
| `InventoryListService.java` | Cap nhat `list()` dung method moi |

---

## 5. Thu tu thuc hien

| Buoc | Task | Do phuc tap | Rui ro |
|------|------|-------------|--------|
| 1 | Task 1 — Fix N+1 `bulkDelete()` | Trung binh | Thap — chi them batch queries |
| 2 | Task 3 — Gop queries `InventoryList` | Thap | Thap — chi gop SQL |
| 3 | Task 2 — Toi uu cycle check | Trung binh | Trung binh — can test recursive CTE |

---

## 6. Test plan

| Task | Test can viet |
|------|---------------|
| Task 1 | Test `bulkDelete` voi 0, 1, 10, 100 ids; test mixed (1 so bi block, 1 so khong) |
| Task 2 | Test cycle detection: direct cycle, indirect cycle, no cycle, self-reference |
| Task 3 | Test summary + count gop cho ra cung ket qua nhu tach rieng |

---

## 7. Rollout

1. Merge tung task rieng, moi task 1 PR
2. Task 1 uu tien cao nhat (anh huong hieu nang ro nhat)
3. Theo doi slow query log sau moi merge
