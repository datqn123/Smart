## 12. Approvals

> Requires: Owner or Admin

> **Note:** Routes `/approvals/pending` and `/approvals/history` in `App.tsx` currently redirect to `/dashboard` — approval pages exist in code but are not accessible via navigation.

### Pending Approvals

```
GET /api/v1/approvals/pending?search=&type=&fromDate=&toDate=&page=&limit=
  ↓
Backend ApprovalsService:
  1. Query stockreceipts WHERE status = 'Pending'
  2. Search: receipt_code ILIKE or full_name ILIKE
  3. Date filter on receipt_date
  4. Returns summary with totalPending and byType breakdown
  → Only Inbound has real data; Outbound/Return/Debt hardcoded = 0
```

### Approval History

```
GET /api/v1/approvals/history?resolution=&search=&type=&fromDate=&toDate=&page=&limit=
  ↓
Backend:
  1. Query stockreceipts WHERE status IN ('Approved', 'Rejected') AND reviewed_at IS NOT NULL
  2. Search includes reviewer name
  3. Date filter on reviewed_at::date
```

### Approve / Reject

> **Note:** Approve/reject mutations go through `stockReceiptsApi` (`approveStockReceipt`, `rejectStockReceipt`), NOT through dedicated approvals endpoints. Approvals endpoints are read-only.

- **Approve:** Click ✓ → dialog select inbound location → `POST /api/v1/stock-receipts/{id}/approve`
- **Reject:** Click ✗ → dialog enter reason → `POST /api/v1/stock-receipts/{id}/reject`

---