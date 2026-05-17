## 7. Order Management

> Requires permission: `can_manage_orders`

### 7.1. Retail POS

**UI (`RetailPage.tsx`):** Split-screen layout
- **Left (8 cols):** POS product grid — search, cards with stock badges
- **Right (4 cols):** Cart + checkout

#### Cart (Zustand store, persist sessionStorage)

- `addItem`: merge by `(productId, unitId)` pair, accumulate quantity
- `updateQuantity`: minimum = 1
- `getTotal()`: sum of `lineTotal`
- `getFinalTotal()`: `total - discount`

#### Checkout

```
Frontend: POSCartPanel
  - Select customer (default "Walk-in Customer")
  - Enter voucher code (optional) → preview discount
  - "Cash" button → paymentStatus: "Paid"
  - "Card/Transfer" button → paymentStatus: "Unpaid"
POST /api/v1/sales-orders/retail/checkout { customerId?, walkIn?, lines[], discountAmount?, voucherCode?, paymentStatus? }
  ↓
Backend SalesOrderService.retailCheckout():
  1. Resolve customer: walkIn=true → lookup "WALKIN" customer
  2. Validate each line: product exists, unitId belongs to product, qty > 0, price ≥ 0, price within ±10% of catalog price
  3. Compute subtotal = Σ(unitPrice × quantity)
  4. Validate discount: 0 ≤ discount ≤ subtotal
  5. Process voucher (if provided):
     - SELECT ... FROM vouchers WHERE code = ? FOR UPDATE (row lock)
     - Validate: isActive, within validity period, has remaining uses
     - Compute discount: Percent → subtotal × value/100; FixedAmount → min(value, subtotal)
  6. INSERT order header: status = "Delivered", orderChannel = "Retail", temp code TMP-UUID
  7. INSERT order lines
  8. Deduct stock (FEFO — First Expired First Out):
     - SELECT inventory ... FOR UPDATE (ordered by expiry date)
     - Check sufficient stock → 409 if insufficient
     - Create stockdispatches (code PX-{year}-{id})
     - Deduct inventory buckets, INSERT inventory_log outbound
     - Update dispatched_qty for order lines
  9. Voucher redemption: increment used_count + insert redemption record
  10. Post revenue to finance ledger
  ↓
Response: 201 Created with full order data
```

### 7.2. Wholesale

#### Create Order

```
POST /api/v1/sales-orders { orderChannel: "Wholesale", customerId, discountAmount?, shippingAddress?, notes?, paymentStatus?, status?, lines[] }
  ↓
Backend:
  1. Validate customer exists
  2. Validate lines (same as retail)
  3. Validate status: Pending|Processing|Partial|Shipped|Delivered (Cancelled blocked)
  4. Validate paymentStatus: Paid|Unpaid|Partial
  5. INSERT order header (temp code → SO-{year}-{id})
  6. INSERT order lines
  7. Post to finance ledger (if applicable)
  → Does NOT auto-deduct stock (managed via separate dispatch workflow)
```

#### Edit Order

```
PATCH /api/v1/sales-orders/{id} { status?, paymentStatus?, shippingAddress?, notes?, discountAmount? }
  ↓
Backend:
  1. SELECT ... FOR UPDATE
  2. Block updates on Cancelled orders (409)
  3. Trigger finance ledger posting when:
     - paymentStatus → "Paid"
     - status → "Delivered"
```

#### Order Status Diagram

```
Pending → Processing → Partial → Shipped → Delivered
   ↓          ↓          ↓         ↓          ↓
Cancelled ← (any state, via cancel endpoint)
```

| Status | Can Create | Can Patch | Can Cancel | Finance Impact |
|---|---|---|---|---|
| Pending | ✓ | ✓ | ✓ | None |
| Processing | ✓ | ✓ | ✓ | None |
| Partial | ✓ | ✓ | ✓ | None |
| Shipped | ✓ | ✓ | ✓ (409 if dispatched) | None |
| Delivered | ✓ | ✓ | ✓ (restores stock for retail) | Records revenue |
| Cancelled | ✗ | ✗ | Idempotent 200 | Records refund (retail) |

### 7.3. Returns / Refunds

```
POST /api/v1/sales-orders { orderChannel: "Return", customerId, refSalesOrderId?, lines[] }
  ↓
Backend:
  1. Validate refSalesOrderId customer must match return's customer
  2. Create order normally (same as Wholesale)
```

#### Cancel Order

```
POST /api/v1/sales-orders/{id}/cancel
  ↓
Backend SalesOrderService.cancel():
  1. SELECT ... FOR UPDATE
  2. Idempotent: already Cancelled → return immediately (200)
  3. Check stock dispatch:
     - Retail: Call RetailStockService.reverseDeductionForRetailCancel()
       → Restore inventory, INSERT inventory_log inbound, cancel dispatch records
     - Wholesale: 409 — "Cannot cancel — already dispatched from warehouse"
  4. Voucher reversal (Retail): restore voucher used_count
  5. Finance ledger: post refund entry
  6. UPDATE status = 'Cancelled', cancelled_at = now, cancelled_by = userId
```

### 7.4. Vouchers

#### Voucher Types

| Type | Formula |
|---|---|
| Percent | discount = subtotal × value / 100 |
| FixedAmount | discount = min(value, subtotal) |

#### Preview Voucher

```
POST /api/v1/sales-orders/retail/voucher-preview { voucherCode?, subtotal, manualDiscount? }
  ↓ (read-only, no locks, no state changes)
Backend:
  1. Validate voucher: active, within validity, has remaining uses
  2. Compute discount breakdown
  ↓
Response: { applicable: true/false, voucherDiscountAmount, totalDiscountAmount, payableAmount }
```

#### Redemption (during checkout)

1. `SELECT ... FOR UPDATE` — row lock prevents race conditions
2. Validate applicability
3. Compute discount
4. After successful order creation:
   - `UPDATE vouchers SET used_count = used_count + 1`
   - `INSERT INTO voucher_redemptions (voucher_id, order_id)`
5. On order cancel: `reverseRedemptionForOrder` — decrement used_count, delete redemption record

**Concurrency protection:** 409 Conflict if voucher runs out of uses between preview and checkout

---