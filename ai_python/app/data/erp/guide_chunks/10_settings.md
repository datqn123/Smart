## 10. System Settings

### 10.1. Employee Management

> Requires permission: `can_manage_staff`

#### Employee List

```
GET /api/v1/users?search=&status=all&roleId=&page=1&limit=20
  ↓
Backend UsersManagementService:
  1. requireActorCanManageStaff() — checks actor is Active + has permission
  2. JOIN users → roles
  3. ORDER BY created_at DESC
```

#### Create Employee

```
Frontend: EmployeeForm (Zod validation)
  - username (3-100), password (8-128), fullName (1-255), employeeCode (1-50)
  - email (valid), phone (≤20), role (Admin/Staff), status (Active/Inactive)
  - "Get code from server" → GET /api/v1/users/next-staff-code → NV-ADM-001, NV-STF-001, ...
POST /api/v1/users { username, password, fullName, email, phone, roleId, status }
  ↓
Backend UserCreationService:
  1. Check actor is Active + can_manage_staff
  2. Lookup role → BLOCK assigning "Owner" role (403)
  3. Check duplicates: username + email → 409 CONFLICT
  4. Map status: UI "Inactive" → DB "Locked"
  5. Encode password (BCrypt)
  6. INSERT INTO users
```

#### Edit Employee

```
PATCH /api/v1/users/{userId} { fullName?, staffCode?, email?, phone?, status?, roleId?, password? }
  ↓
Backend UsersManagementService:
  1. Block empty body (400)
  2. **Role change guard**: only Owner can change roleId; cannot assign "Owner" role
  3. Apply partial updates
  4. Catch DataIntegrityViolationException → 409 (duplicate email/staffCode)
```

#### Delete Employee (Soft Delete — locks account)

```
DELETE /api/v1/users/{userId}
  ↓
Backend:
  1. Cannot delete self → 409
  2. Cannot delete Owner → 409
  3. UPDATE users SET status = 'Locked' WHERE id = ? AND status = 'Active'
```

#### Generate Next Staff Code

```
GET /api/v1/users/next-staff-code?roleId=3&staffFamily=ADMIN
  ↓
Backend NextStaffCodeService:
  1. Validate roleId exists, staffFamily compatible with roleId
  2. Prefix: NV-OWN (Owner), NV-ADM (Admin), NV-MAN (Manager), NV-STF (Staff), NV-WH (Warehouse)
  3. Query: SELECT staff_code FROM users WHERE staff_code LIKE 'NV-ADM-%'
  4. Parse suffix, find max, +1 → format zero-padded 3 digits
  ↓
Response: { nextCode: "NV-ADM-001", prefix: "NV-ADM" }
```

### 10.2. Store Profile

#### View Profile

```
GET /api/v1/store-profile
  ↓
Backend StoreProfileService.getOrCreate():
  1. INSERT ... ON CONFLICT DO NOTHING (auto-create if missing)
  2. SELECT by owner_id
```

#### Edit Profile (Differential PATCH)

```
Frontend: buildPatchBody() — only sends changed fields. Empty string → null. No changes → toast
PATCH /api/v1/store-profile { name?, address?, phone?, email?, website?, taxCode?, ... }
  ↓
Backend:
  1. Validate body not empty, accepts only 12 whitelisted keys
  2. Per-field validation: name not blank, email has "@", website/logo/facebook is valid URI
  3. Validate defaultRetailLocationId exists in warehouselocations
  4. Dynamic SQL UPDATE
```

#### Upload Logo

```
POST /api/v1/store-profile/logo  (multipart/form-data, part "file")
  ↓
Backend:
  1. Upload to Cloudinary: smart-erp/store-profiles/{ownerId}/{UUID}
  2. UPDATE storeprofiles SET logo_url = ?
```

### 10.3. Alert Settings

> **Owner only** can configure alerts.

#### List

```
GET /api/v1/alert-settings?ownerId=&alertType=&isEnabled=
  ↓
Backend: Owner → force ownerId = JWT userId; Admin → uses provided ownerId; else → 403
```

#### Create Alert

```
POST /api/v1/alert-settings { alertType, channel:"App", frequency:"Realtime", thresholdValue?, isEnabled:true, recipients? }
  ↓
Backend:
  1. Owner-only
  2. Normalize threshold: only allowed for LowStock/ExpiryDate/HighValueTransaction/PartnerDebtDueSoon; block negative
  3. Validate recipients usernames exist
  4. INSERT with recipients as JSONB
  5. Unique constraint (owner_id, alert_type) → 409 if duplicate
```

#### Toggle Alert (Soft Disable)

```
DELETE /api/v1/alert-settings/{id}
→ UPDATE alertsettings SET is_enabled = FALSE  (not a hard delete)
```

### 10.4. System Logs

> **Admin only** + `can_view_system_logs` required.

#### List

```
GET /api/v1/system-logs?search=&module=&logLevel=&dateFrom=&dateTo=&page=&limit=
  ↓
Backend:
  1. Admin-only: checks role = "Admin" AND mp.can_view_system_logs = true
  2. Validate: page ≥ 1, limit 1-100, search ≤200, module ≤100, logLevel valid
  3. JOIN users to get full_name
  4. Search spans: message, action, module, full_name, context_data (ILIKE)
```

#### Delete Logs

```
DELETE /api/v1/system-logs/{id}  or  POST /api/v1/system-logs/bulk-delete
→ ALWAYS returns 403 FORBIDDEN: "Not allowed to delete system logs per system policy"
→ System logs are IMMUTABLE
```

---