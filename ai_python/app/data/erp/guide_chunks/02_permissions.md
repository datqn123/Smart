## 2. Permissions & Roles

### Roles

| Role | Description |
|------|-------------|
| **Owner** | Store owner — highest privileges, cannot be deleted or assigned to new users |
| **Admin** | Administrator — manages staff, inventory, orders, finance |
| **Manager** | Manager — operational privileges |
| **Staff** | Staff — limited privileges, can request password reset |
| **Warehouse** | Warehouse keeper — inventory management |

### Permission System (12 flags)

Each role has a set of permission flags stored as JSONB in the `roles.permissions` table. On login, these flags are embedded into the JWT claim `"mp"` (menu permissions).

| Permission Key | Description |
|---|---|
| `can_view_dashboard` | View Dashboard page |
| `can_use_ai` | Use AI Chat |
| `can_manage_inventory` | Manage inventory (inbound/outbound/audit) |
| `can_manage_products` | Manage products |
| `can_manage_customers` | Manage customers |
| `can_manage_orders` | Manage orders |
| `can_approve` | Approve inbound/outbound receipts |
| `can_view_finance` | View finance |
| `can_manage_staff` | Manage staff |
| `can_configure_alerts` | Configure alerts |
| `can_view_store_profile` | View store profile |
| `can_view_system_logs` | View system logs |

### Permission Enforcement

- **Backend:** `@PreAuthorize("hasAuthority('can_manage_staff')")` on each controller
- **Frontend:** Sidebar auto-hides items without permission based on `menuPermissions` from Zustand store
- **Client does NOT verify JWT signature** — only parses payload for UI rendering. Backend always enforces 403.

---