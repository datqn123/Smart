## 3. Login / Logout / Session

### 3.1. Login

**UI:**
1. User opens app → If valid session in sessionStorage → redirects to `/dashboard`
2. Otherwise → shows `LoginForm` with 2 fields: email + password (min 6 chars)
3. User submits → "Login"

**Flow:**
```
Frontend POST /api/v1/auth/login { email, password }
  ↓
Backend AuthService.login():
  1. Check user exists and status != "Locked"
  2. Not found → 401 UNAUTHORIZED
  3. Locked → 403 FORBIDDEN
  4. Verify password (BCrypt)
     - 5 consecutive failures → lock account (status = 'Locked')
     - Success → clear failure counter
  5. Create JWT access token (HS256, TTL 5 min)
     - Claims: sub, user_id, tenant_id, name, role, mp (permissions)
  6. Create refresh token (32-char hex, 30-day expiry)
  7. Save refresh token to refresh_tokens table
  8. Update last_login
  9. Write login log to systemlogs
  10. Register session in Redis: auth:session:{userId}
  ↓
Frontend receives response:
  { accessToken, refreshToken, user }
  1. Save accessToken, refreshToken, user to sessionStorage
  2. Parse "mp" claim from JWT → update Zustand store (persist localStorage)
  3. Navigate to /dashboard
```

**Tables involved:** `users`, `roles`, `refresh_tokens`, `systemlogs`, Redis `auth:session:{userId}`

### 3.2. Token Refresh

**Trigger:** When a request with `auth: true` receives 401, frontend auto-calls refresh.

```
Frontend POST /api/v1/auth/refresh { refreshToken }
  ↓
Backend AuthService.refresh():
  1. Validate refresh token (exists, not revoked, not expired)
  2. Verify user is still Active
  3. Throttle: max 1 new access token / 5 min / user
  4. Create new access token (same process as login)
  5. Return same refresh token (no rotation)
  6. Update Redis session
  ↓
Frontend:
  1. Save new accessToken + refreshToken to sessionStorage
  2. Re-parse "mp" claim → update Zustand store
  3. Retry original request with new token
```

### 3.3. Logout

```
Frontend calls logoutAndGoToLogin():
  1. POST /api/v1/auth/logout { refreshToken } + Bearer token (best-effort)
  2. Remove accessToken, refreshToken, user from sessionStorage
  3. Reset Zustand store (clear localStorage auth-storage)
  4. Navigate to /login
  ↓
Backend AuthService.logout():
  1. Soft revoke refresh token: UPDATE refresh_tokens SET deleteYmd = now
     - Not found → 403
  2. Clear refresh throttle
  3. Write logout log to systemlogs
  4. Delete Redis session: auth:session:{userId}
```

### 3.4. Session Persistence

| Layer | Storage | Data |
|---|---|---|
| **sessionStorage** (per tab) | accessToken, refreshToken, user | Tokens + user info |
| **localStorage** (Zustand persist) | user, isAuthenticated, menuPermissions | No tokens stored (security) |
| **Redis** (server-side) | `auth:session:{userId}` → accessToken | Multi-instance sync |

### 3.5. Password Reset Request

**Only for Staff role.** Owner/Admin/Manager must contact Owner directly.

```
Frontend: "Request Password" Dialog → username + message (optional)
POST /api/v1/auth/password-reset-requests { username, message }
  ↓
Backend:
  1. Find user by username
  2. Check: role = "Staff" AND status IN ("Active", "Locked")
  3. If not met → silently return (prevents username enumeration)
  4. INSERT INTO staffpasswordresetrequests (user_id, message, status='Pending')
  5. Write log to systemlogs
  6. Notify all Owner/Admin users
  7. Return success message (always shows success)
```

---