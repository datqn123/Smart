## 15. Database Reference

### Core Tables

| Table | Description |
|---|---|
| `users` | User accounts |
| `roles` | Roles + JSONB permissions |
| `refresh_tokens` | Login refresh tokens |
| `staffpasswordresetrequests` | Password reset requests |
| `storeprofiles` | Store profile information |
| `alertsettings` | Alert configurations |
| `systemlogs` | System audit logs |
| `notifications` | User notifications |

### Catalog & Partners

| Table | Description |
|---|---|
| `categories` | Product categories (hierarchical tree) |
| `products` | Products |
| `productimages` | Product image gallery |
| `productunits` | Product units of measure |
| `productpricehistory` | Product price history |
| `suppliers` | Suppliers |
| `customers` | Customers |

### Inventory

| Table | Description |
|---|---|
| `inventory` | Current stock levels |
| `inventorylogs` | Stock movement logs |
| `stockreceipts` | Inbound stock receipts |
| `stockreceiptdetails` | Receipt line items |
| `stockdispatches` | Outbound stock dispatches |
| `stockdispatch_lines` | Dispatch line items |
| `inventoryauditsessions` | Audit sessions |
| `inventoryauditlines` | Audit session lines |
| `inventory_audit_session_events` | Audit session events |
| `warehouselocations` | Warehouse locations |

### Orders

| Table | Description |
|---|---|
| `salesorders` | Sales orders |
| `orderdetails` | Order line items |
| `vouchers` | Discount vouchers |
| `voucher_redemptions` | Voucher redemption history |

### Finance

| Table | Description |
|---|---|
| `cashtransactions` | Cash transactions |
| `cash_funds` | Cash funds |
| `financeledger` | Finance ledger (double-entry) |
| `partnerdebts` | Partner debts (receivables/payables) |

### AI

| Table | Description |
|---|---|
| `ai_table_description` | Table descriptions for AI |
| `ai_column_description` | Column descriptions for AI |
| `aichathistory` | AI chat history |
| `aiinsights` | AI insights |

---