## 16. Appendix: Key Business Rules

### Inventory Rules

1. **Increase inventory:** Only occurs when **approving a stock receipt** (Stock Receipt Approve)
2. **Decrease inventory:** Only occurs when **dispatch reaches Delivered status** or **applying audit variance**
3. **Retail POS:** Auto-deducts stock on checkout (FEFO — First Expired First Out)
4. **Row locking (FOR UPDATE):** Prevents race conditions on inventory patches, receipt approvals, checkout
5. **No duplicates:** Cannot have 2 inventory rows with same (productId + locationId + batchNumber)

### Product Pricing Rules

1. **Price pair:** When changing price, MUST send both `salePrice` AND `costPrice`
2. **Price history:** Only INSERT new record into `productpricehistory` if price actually changed
3. **Effective date:** `priceEffectiveDate` defaults to current date

### Delete Permission Rules

| Entity | Single Delete | Bulk Delete |
|---|---|---|
| Product | Owner only (hard) | Owner only (hard) |
| Category | Owner only (soft) | Owner only (soft, sequential) |
| Supplier | Owner only (hard) | Owner only (hard) |
| Customer | Admin only (soft) | Owner only (hard) |
| User | can_manage_staff (soft → Locked) | N/A |

### Finance Rules

1. **Idempotent posting:** All automatic postings check `existsPosting()` before INSERT
2. **Signed amounts:** Income = positive, Expense = negative
3. **Running balance:** Computed via window function `SUM() OVER (ORDER BY ...)`
4. **Default fund:** Automatic postings use fund with `is_default = TRUE`

### AI Chat Rules

1. **SQL read-only:** Only SELECT allowed, completely blocks DDL/DML
2. **Table allowlist:** SQL can only query registered tables
3. **Ledger metric policy:** Revenue/expense queries MUST use `financeledger` table
4. **Auto-LIMIT:** Automatically adds LIMIT if missing (default 1000)
5. **Conversation memory:** Sqlite checkpointer or in-memory, per thread_id