## 6. Product Management

> Requires permission: `can_manage_products` (products), `can_manage_customers` (customers)

### 6.1. Products

#### Create Product

```
Frontend: ProductForm → if images exist → multipart/form-data
POST /api/v1/products  (JSON or multipart)
  ↓
Backend ProductService:
  1. Check SKU uniqueness
  2. Validate category (if provided) — must exist and be Active
  3. INSERT into products
  4. INSERT base unit into productunits (conversion_rate=1, is_base_unit=TRUE)
  5. INSERT initial price into productpricehistory
  6. If images: parallel upload to Cloudinary (max 10 images, JPEG/PNG/WebP, ≤5MB each)
  7. If upload fails → rollback (delete product)
  ↓
Response: 201 Created { id, skuCode, barcode, name, categoryId, imageUrl, status, currentStock, currentPrice }
```

#### Product List

```
GET /api/v1/products?search=&categoryId=&status=&page=&limit=&sort=
  ↓
Backend: JOIN products → productunits (base) → categories → inventory (COALESCE qty)
         + LATERAL subquery on productpricehistory for latest price
Frontend: Infinite scroll (IntersectionObserver), search debounce 400ms
```

#### Edit Product (Differential PATCH)

```
PATCH /api/v1/products/{id} { changedFields }
  ↓
Backend:
  1. SELECT ... FOR UPDATE (pessimistic lock)
  2. Validate each field (skuCode ≤50, name ≤255, barcode ≤100, weight ≥0)
  3. Price pair rule: if changing price → MUST send both salePrice AND costPrice
  4. Compare with latest productpricehistory → only INSERT history row if actually changed
  5. priceEffectiveDate defaults to today
```

#### Delete Product — **Owner Only**

**Delete Guards:**

| Check | Related Table |
|---|---|
| Has stock receipts | `stockreceiptdetails` |
| Has order lines | `orderdetails` |
| Has stock | `inventory.quantity > 0` |

#### Product Image Management

- **JSON mode:** `POST /api/v1/products/{id}/images` with `{url, sortOrder, isPrimary}` — add from external URL
- **Multipart mode:** `POST /api/v1/products/{id}/images` with `file` part — upload to Cloudinary
- **Primary image:** When setting `isPrimary=true` → clear all existing primaries → update `products.image_url`

### 6.2. Categories — Hierarchical Tree

#### Tree List

```
GET /api/v1/categories?format=tree&search=&status=
  ↓
Backend CategoryService:
  1. Load all active categories (deleted_at IS NULL) with product counts
  2. Apply search filter — INCLUDES ancestors of matching nodes (preserves tree context)
  3. Build tree in memory: buildChildrenIndex() → recursive buildSubTree() with BFS cycle guard
  4. Sort by sortOrder, then name
```

#### Create Category

```
POST /api/v1/categories { categoryCode, name, description?, parentId?, sortOrder?, status? }
  ↓
Backend:
  1. Validate: code not blank, unique, name ≤255
  2. Parent must exist and be Active
  3. INSERT into categories
```

#### Edit — Cycle Prevention

```
PATCH /api/v1/categories/{id} { parentId?, ... }
  ↓
Backend:
  1. wouldPutParentInDescendantSubtree() — BFS from current node's descendants
     - If newParentId found among descendants → reject "hierarchy cycle"
  2. v1 limitation: Cannot move back to root (parentId=null) via PATCH
```

#### Delete Category — **Owner Only, Soft Delete**

**Delete Guards:**
- Has active child categories
- Has products assigned to this category

```
DELETE /api/v1/categories/{id}
→ UPDATE categories SET deleted_at = CURRENT_TIMESTAMP
```

### 6.3. Suppliers

#### Basic CRUD

```
POST /api/v1/suppliers { supplierCode, name, contactPerson, phone, email?, address?, taxCode?, status? }
PATCH /api/v1/suppliers/{id} { changedFields }  (differential)
GET /api/v1/suppliers?search=&status=&page=&limit=&sort=  (infinite scroll)
```

#### Delete — **Owner Only, Hard Delete**

**Delete Guards:**

| Check | Related Table |
|---|---|
| Has receipts | `stockreceipts` |
| Has partner debts | `partnerdebts` |

### 6.4. Customers

#### Basic CRUD

```
POST /api/v1/customers { customerCode, name, phone, email?, address?, status? }
  → loyaltyPoints initialized to 0
PATCH /api/v1/customers/{id} { changedFields }
  → Staff CANNOT edit loyaltyPoints (403)
  → Frontend hides loyaltyPoints field for Staff
GET /api/v1/customers?search=&status=&page=&limit=&sort=
  → Aggregates total_spent, order_cnt from salesorders (excluding Cancelled)
```

#### Delete — Split Authority

| Action | Permission | Type | Delete Guards |
|---|---|---|---|
| Single delete | **Admin** | Soft Delete | Open orders, Partner debts |
| Bulk delete (≤50) | **Owner** | Hard Delete | ANY orders, Partner debts |

---