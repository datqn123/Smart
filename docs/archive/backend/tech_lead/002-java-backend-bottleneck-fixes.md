---
name: fixing-java-backend-bottlenecks
description: Use when Java Spring Boot backend has N+1 query problems, redundant database calls, or memory-heavy operations that cause performance degradation
---

# Fixing Java Backend Bottlenecks

## Overview

Kỹ thuật tối ưu hóa Java backend bằng cách phát hiện và xử lý các bottleneck phổ biến: N+1 queries, redundant queries, và memory-heavy operations.

## When to Use

- API response chậm (>500ms) với dữ liệu lớn
- Thấy vòng lặp `for` gọi database bên trong
- Nhiều queries riêng biệt cho cùng filter
- Load toàn bộ data khi chỉ cần subset

## Core Pattern

### Before (N+1 Problem)
```java
for (int pid : ids) {
    if (!repo.existsById(pid)) { ... }           // N queries
    if (!repo.isDeletable(pid)) { ... }          // N queries
}
repo.deleteBatch(ids);                           // 1 query
// Total: 2N + 1 queries
```

### After (Batch Pattern)
```java
Set<Integer> existing = repo.findExistingBatch(ids);  // 1 query
Map<Integer, String> blocked = repo.findBlockedBatch(ids);  // 1 query
repo.deleteBatch(ids);                                  // 1 query
// Total: 3 queries (O(1))
```

## Quick Reference

| Bottleneck | Dấu hiệu | Giải pháp | Queries giảm |
|------------|----------|-----------|--------------|
| **N+1 Query** | `for` loop + DB call bên trong | Batch query với `WHERE IN` | 4N+2 → 4 |
| **Redundant Queries** | Cùng filter, nhiều SELECT | Gop thành 1 query với multiple aggregates | 3 → 2 |
| **Memory O(E)** | Load toàn bộ table | Recursive CTE hoặc pagination | O(E) → O(depth) |

## Implementation

### Task 1: Fix N+1 trong `ProductService.bulkDelete()`

**Vị trí:** `ProductService.java:461-490`

**Vấn đề:** 4N+2 queries cho N sản phẩm

**Giải pháp:**
1. Thêm `ProductJdbcRepository.findExistingProductIds(List<Integer> ids)`
2. Thêm `ProductJdbcRepository.findBulkDeleteBlockReasons(List<Integer> ids)`
3. Viết lại `bulkDelete()` dùng batch methods

**SQL mẫu cho batch reasons:**
```sql
SELECT p.id,
  CASE
    WHEN EXISTS (SELECT 1 FROM stockreceiptdetails WHERE product_id = p.id) 
      THEN 'HAS_STOCK_RECEIPT'
    WHEN EXISTS (SELECT 1 FROM orderdetails WHERE product_id = p.id) 
      THEN 'HAS_ORDER_LINES'
    WHEN COALESCE(inv.qty, 0) > 0 
      THEN 'HAS_STOCK'
    ELSE NULL
  END AS block_reason
FROM unnest(:ids::int[]) AS p(id)
LEFT JOIN LATERAL (
  SELECT SUM(quantity) AS qty FROM inventory WHERE product_id = p.id
) inv ON true
```

### Task 2: Gộp queries trong `InventoryListService.list()`

**Vị trí:** `InventoryListService.java:47-53`

**Vấn đề:** 3 queries riêng biệt (summary, count, data)

**Giải pháp:**
1. Thêm `InventoryListJdbcRepository.loadSummaryWithCount(q)`
2. Trả về cả summary + total trong 1 query
3. Cap nhat `list()` dùng method mới

### Task 3: Tối ưu cycle check trong `CategoryService.patch()`

**Vị trí:** `CategoryService.java:213`

**Vấn đề:** Load toàn bộ parent edges O(E) memory

**Giải pháp:** Dùng PostgreSQL recursive CTE để chỉ load **descendants** của `categoryId` (thay vì load toàn bộ edges), kiểm tra `newParentId` có nằm trong subtree đó không — nếu có thì set `categoryId.parent = newParentId` sẽ tạo cycle.

```sql
WITH RECURSIVE descendants AS (
  SELECT id, parent_id, 1 AS depth
  FROM categories
  WHERE parent_id = :categoryId AND deleted_at IS NULL
  UNION ALL
  SELECT c.id, c.parent_id, d.depth + 1
  FROM categories c
  INNER JOIN descendants d ON c.parent_id = d.id
  WHERE c.deleted_at IS NULL AND d.depth < 1000
)
SELECT EXISTS(
  SELECT 1 FROM descendants WHERE id = :newParentId
) AS would_create_cycle
```

> **Ghi chú:** Plan ban đầu viết example walk *ancestors* (từ `categoryId` đi lên). Code thực tế walk *descendants* (từ `categoryId` đi xuống) — cả hai cách đều đúng về mặt toán học (tương đương với BFS trong code cũ tại `CategoryService.java:263-284`). Descendants được chọn vì filter `parent_id = :categoryId` ở anchor case tận dụng index trên `parent_id` tốt hơn.

## Common Mistakes

| Sai lầm | Hậu quả | Cách tránh |
|---------|---------|------------|
| Dùng `@Query` với `IN clause` cho List lớn | PostgreSQL giới hạn 65535 params | Chunk thành batches 1000 items |
| Quên transaction cho batch operations | Partial failure, data inconsistent | Wrap trong `@Transactional` |
| Batch query không dùng index | Full table scan, chậm hơn loop | Thêm index cho columns trong WHERE IN |
| Recursive CTE không có LIMIT | Infinite loop với cyclic data | Thêm `LIMIT 1000` hoặc depth check |

## Test Plan

| Task | Test cases |
|------|------------|
| Task 1 | 0 ids, 1 id, 10 ids, 100 ids; mixed (some blocked, some not) |
| Task 2 | Verify summary + count same as separate queries |
| Task 3 | Direct cycle, indirect cycle, no cycle, self-reference |

## Priority Order

1. **Task 1** — Impact cao nhất (4N+2 → 4 queries)
2. **Task 2** — Impact trung bình (3 → 2 queries)
3. **Task 3** — Impact thấp (chỉ khi >1000 categories)
