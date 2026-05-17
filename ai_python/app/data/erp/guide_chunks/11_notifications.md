## 11. Notifications

### UI (Header notification bell)

- **Polling:** `GET /api/v1/notifications?page=1&limit=50` every **12 seconds**
- **Red badge:** shows unread count (capped at "99+")
- **Dropdown:** max 50 notifications, newest first, unread has blue left bar

### Click Notification

| referenceType | Action |
|---|---|
| `StockReceipt` | Fetch receipt detail → open ReceiptDetailDialog → mark read |
| `StockDispatch` | Fetch dispatch detail → open DispatchDetailDialog → mark read |
| Other | Just mark read |

### API

```
GET /api/v1/notifications?page=1&limit=50&unreadOnly=true
PATCH /api/v1/notifications/:id  (mark single read)
POST /api/v1/notifications/mark-all-read
```

### Backend

- **Table:** `notifications` — user_id, notification_type, title, message, is_read, reference_type, reference_id
- **Source:** Other services INSERT notifications (password reset requests, receipts/dispatches, etc.)
- **Time format:** Vietnamese relative — "Just now", "X minutes ago", "X days ago", or full date (>14 days)

---