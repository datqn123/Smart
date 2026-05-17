## 5. Inventory Management

> Requires permission: `can_manage_inventory`

### 5.1. View & Search Stock

**UI (`StockPage.tsx`):**
- 4 KPI cards: Total SKUs, Total Inventory Value, Low Stock Count, Expiring Soon Count
- Stock table with infinite scroll
- Toolbar: search, filter by stock level, location, category

**Data Flow:**
```
GET /api/v1/inventory?search=&stockLevel=all&locationId=&categoryId=&page=1&limit=20&sort=id:asc
GET /api/v1/inventory/summary?search=&stockLevel=all  (KPI cards)
  ↓
Backend InventoryListService:
  1. loadSummary() — COUNT, SUM(quantity×costPrice), low/expiring counts
  2. countRows() — total rows for pagination
  3. loadPage() — JOIN products, locations, units
     - isLowStock = quantity > 0 AND quantity <= minQuantity
     - isExpiringSoon = expiryDate <= today+30days AND quantity > 0
     - totalValue = costPrice × quantity
  ↓
Frontend:
  - IntersectionObserver loads more on near-end scroll
  - Search debounce 400ms
```

**Display Status:**

| Status | Condition | Color |
|---|---|---|
| Draft | Draft | Gray |
| Out of Stock | quantity = 0 | Red |
| Low Stock | isLowStock | Red |
| Expiring Soon | isExpiringSoon | Amber |
| Normal | Default | Green |

**Batch Detail View:** Click eye icon → `StockBatchDetailsDialog` shows batch info + list of same-product lots still in stock.

### 5.2. Edit Stock Info

**UI:** Select rows → click "Edit" → `StockEditDialog`

**Editable fields:** `locationId`, `minQuantity`, `batchNumber`, `expiryDate`, `unitId`

**Read-only fields:** `costPrice`, `unitName`, `productName`, `skuCode`, `quantity`

**Data Flow:**
```
Single: PATCH /api/v1/inventory/{id} { changedFields }
Bulk:   PATCH /api/v1/inventory/bulk { items: [{id, ...fields}] }  (max 100 rows)
  ↓
Backend InventoryPatchService:
  1. SELECT ... FOR UPDATE (row lock)
  2. Check: product status != "Inactive", location status != "Maintenance"
  3. Check: new locationId exists and is Active
  4. Check: unitId belongs to product
  5. Check: no duplicate (productId + locationId + batchNumber)
  6. UPDATE only changed fields
  7. Write log to systemlogs (before/after JSON)
  8. Notify Owner (if actor is not Owner)
```

### 5.3. Stock Receipt (Inbound)

**UI (`InboundPage.tsx`):**
- Receipt list with filters: status, date, supplier, "mine"
- "Create Receipt" button → `ReceiptForm`

#### Create Receipt

```
Frontend: ReceiptForm (Zod validation)
  - supplierId (required), receiptDate (required)
  - details[]: productId, unitId, quantity, costPrice (required)
  - expiryDate >= receiptDate
  - Mode: "Save Draft" or "Submit for Approval"
POST /api/v1/stock-receipts { supplierId, receiptDate, invoiceNumber?, notes?, saveMode, details[] }
  ↓
Backend StockReceiptLifecycleService.create():
  1. Validate supplier exists and is Active
  2. Validate each line: product Active, unitId belongs to product, must be base unit
  3. Check no duplicate (productId + batchNumber) within same receipt
  4. Generate code: PN-{year}-{seq} (retry max 5 on duplicate)
  5. INSERT header + detail rows
  6. If saveMode=pending → notify approvers
  ↓
Response: 201 Created with full receipt data
```

#### Approve Receipt — **Inventory Increase Point**

```
POST /api/v1/stock-receipts/{id}/approve { inboundLocationId }
  ↓
Backend (requires can_approve + Admin/Owner):
  1. Check status = "Pending"
  2. Check location is Active
  3. For each detail line:
     - Find existing inventory (same productId + locationId + batchNumber) or create new
     - Add quantity (converted to base unit)
     - INSERT inventory_logs (INBOUND)
  4. UPDATE receipt status → "Approved", record approverId + approvedAt
  5. Post to finance ledger (purchase cost)
  6. Write system log
```

#### Reject Receipt

```
POST /api/v1/stock-receipts/{id}/reject { reason }  (min 15 chars)
  ↓
Backend: UPDATE status → "Rejected", record reviewerId + reviewedAt + rejectionReason
```

#### Edit / Delete

| Status | Edit | Delete |
|---|---|---|
| Draft | Creator can edit | Owner only |
| Pending | Cannot edit | Staff/Admin/Owner can delete |
| Approved/Rejected | Cannot edit | Cannot delete |

#### Receipt Status Diagram

```
Draft → (submit) → Pending → (approve) → Approved [INCREASES INVENTORY]
Draft → (submit) → Pending → (reject)  → Rejected
Draft → (delete) → [deleted]
Pending → (delete) → [deleted]
```

### 5.4. Stock Dispatch (Outbound)

**UI (`DispatchPage.tsx`):**
- Dispatch list with filters
- Create manually from Stock page or Dispatch page
- Create from order (order-linked)

#### Create Manual Dispatch

```
POST /api/v1/stock-dispatches { dispatchDate, referenceLabel?, notes?, lines: [{ inventoryId, quantity, unitPriceSnapshot? }] }
  ↓
Backend ManualStockDispatchService.createManual():
  1. Validate quantity > 0 for each line
  2. INSERT header with temp code, status = "Pending"
  3. For each line: lock inventory, check sufficient or shortage
  4. INSERT dispatch lines
  5. Generate code: PX-{year}-{id} (6-digit padded)
  6. If shortage → status = "Partial", notify shortage
  7. If sufficient → notify creation success
```

#### Approve Dispatch (Admin)

```
POST /api/v1/stock-dispatches/{id}/approve
  ↓
Backend (Admin only):
  1. Check status = Pending/Partial, no shortage
  2. UPDATE status → "WaitingDispatch"
```

#### Delivery Complete — **Inventory Decrease Point**

```
PATCH /api/v1/stock-dispatches/{id} { status: "Delivered" }
  ↓
Backend finalizeDelivered():
  1. For each line: deduct inventory quantity
  2. INSERT inventory_logs (OUTBOUND)
  3. Post COGS to finance ledger
  4. UPDATE status → "Delivered"
```

#### Dispatch Status Diagram

```
Pending → (admin approve, no shortage) → WaitingDispatch → Delivering → Delivered [DECREASES INVENTORY]
Pending → (has shortage) → Partial → (fix lines) → Pending
Any (not Delivered) → (soft-delete) → [soft deleted]
```

### 5.5. Audit Session

**UI (`AuditPage.tsx`):**
- Audit session list with filters
- "Create Audit Session" → select scope

#### Create Audit Session

```
POST /api/v1/inventory/audit-sessions { title, auditDate, notes?, scope: { mode, ... } }
  ↓
Backend AuditSessionService.create():
  1. Validate scope:
     - by_location_ids: find all inventory at these locations
     - by_category_id: find inventory for products in this category
     - by_inventory_ids: direct selection by ID
  2. Generate code: KK-{year}-{seq}
  3. INSERT session header, status = "Pending"
  4. For each inventory in scope:
     - INSERT audit line with systemQuantity (snapshot), actualQuantity = NULL
```

#### Enter Actual Quantities

```
PATCH /api/v1/inventory/audit-sessions/{id}/lines { lines: [{ lineId, actualQuantity, notes? }] }
  ↓
Backend (only when status = "In Progress" or "Re-check"):
  1. UPDATE actualQuantity, isCounted = true
  2. Recalculate variance = actual - system
```

#### Complete Audit

```
POST /api/v1/inventory/audit-sessions/{id}/complete { requireAllCounted? }  (default true)
  ↓
Backend:
  1. Check status = "In Progress"
  2. If requireAllCounted → all lines must be counted
  3. UPDATE status → "Pending Owner Approval"
  → Does NOT apply variance to inventory yet
```

#### Owner Approve / Reject

```
POST /api/v1/inventory/audit-sessions/{id}/approve   → Completed
POST /api/v1/inventory/audit-sessions/{id}/reject    → In Progress
  ↓ (Owner only)
```

#### Apply Variance — **Inventory Adjustment Point**

```
POST /api/v1/inventory/audit-sessions/{id}/apply-variance { mode?, reason? }
  ↓
Backend (only when status = "Completed"):
  1. For each line with variance: lock inventory
  2. Mode "set_actual": quantity = actualQuantity (rounded)
  3. Mode "add_delta" (default): quantity += (actual - system) (rounded)
  4. Check quantity >= 0
  5. UPDATE inventory
  6. INSERT inventory_log
  7. Mark varianceAppliedAt
```

#### Audit Status Diagram

```
Pending → In Progress → (complete) → Pending Owner Approval
Pending Owner Approval → (owner approve) → Completed → (apply-variance) → [inventory adjusted]
Pending Owner Approval → (owner reject) → In Progress
Pending/In Progress/Pending Owner Approval → (cancel) → Cancelled
Completed → (owner Re-check) → Re-check → (complete) → Pending Owner Approval
```

### 5.6. Warehouse Locations

**UI (`WarehouseLocationsPage.tsx`):**
- Currently uses mock data (4 hardcoded locations)
- Table: location code, area, shelf, capacity, current stock, status
- Statuses: "Active", "Full", "Inactive" (Maintenance)

**Backend:** Locations are referenced by `locationId` in inventory rows, validated during inventory patch and receipt approval.

---