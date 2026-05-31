# 📄 API SPEC: `POST /api/v1/inventory/audit-sessions` — Tạo đợt kiểm kê + snapshot dòng - Task022

> **Trạng thái**: Draft  
> **Feature**: UC6 — nút **Tạo đợt kiểm kê** (`AuditPage`)

---

## 1. Mục tiêu Task

- Tạo **`inventory_audit_sessions`** ở trạng thái **`Pending`**, sinh **`audit_code`** (KK-YYYY-NNNN), **chèn snapshot** các dòng **`inventory_audit_lines`** từ `Inventory` theo `scope`.

- **Out of scope**: cập nhật số thực tế → Task025; hoàn tất → Task026.

---

## 2. Mục đích Endpoint

**`POST /api/v1/inventory/audit-sessions`** — một transaction: header + N dòng (`system_quantity` = `Inventory.quantity` tại thời điểm tạo).

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.15**; [`Database_Specification.md`](../UC/Database_Specification.md) §16 `Inventory`.

---

## 4. Overview

| **Endpoint** | `/api/v1/inventory/audit-sessions` |
| **Method** | `POST` |
| **Auth** | `Bearer` |
| **RBAC** | Staff / Owner |
| **UC** | UC6 |

---

## 5. Request body

```json
{
  "title": "Kiểm kê kho A1 - Tháng 4",
  "auditDate": "2026-04-13",
  "notes": null,
  "scope": {
    "mode": "by_location_ids",
    "locationIds": [1, 2]
  }
}
```

| `scope.mode` | Ý nghĩa |
| :------------- | :------ |
| `by_location_ids` | `locationIds` bắt buộc (non-empty) — snapshot mọi `Inventory` có `location_id` ∈ danh sách |
| `by_category_id` | `categoryId` bắt buộc — join `Products` lọc `category_id` |
| `by_inventory_ids` | `inventoryIds[]` bắt buộc — chỉ các dòng tồn chỉ định |

---

## 6. Thành công — `201 Created`

Trả về shape đầy đủ giống [`API_Task023_inventory_audit_sessions_get_by_id.md`](API_Task023_inventory_audit_sessions_get_by_id.md) (session + `items[]` đã snapshot).

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → `created_by = user_id`. **401** / **403**.
2. Validate `title`, `auditDate`, `scope` → **400**.
3. **`BEGIN`**.
4. Sinh **`audit_code`** unique (KK-YYYY-NNNN).
5. **`INSERT INTO inventory_audit_sessions`** (`audit_code`, `title`, `audit_date`, `status='Pending'`, `location_filter`/`category_filter` text snapshot tùy scope, `notes`, `created_by`, timestamps).
6. **`SELECT i.id, i.quantity FROM Inventory i WHERE …`** (theo scope) — 0 dòng → **400** “Không có tồn khớp phạm vi”.
7. **`INSERT INTO inventory_audit_lines`** (`session_id`, `inventory_id`, `system_quantity`, `is_counted=false`) cho từng dòng.
8. **`INSERT SystemLogs`**.
9. **`COMMIT`**; `SELECT` join trả `201`.

### 7.2 Các ràng buộc (Constraints)

- FK `inventory_id` → `Inventory.id` (RESTRICT).  
- Không snapshot dòng `quantity = 0` nếu policy loại bỏ — ghi rõ trong triển khai (mặc định: **vẫn snapshot** để kiểm âm dương).

---

## 8. Lỗi

- **400** scope / không có dòng; **401**; **403**; **409** (nếu giới hạn song song 1 đợt `In Progress` — tùy PM); **500**.

---

## 9. Zod

```typescript
import { z } from "zod";

const ScopeSchema = z.discriminatedUnion("mode", [
  z.object({ mode: z.literal("by_location_ids"), locationIds: z.array(z.number().int().positive()).min(1) }),
  z.object({ mode: z.literal("by_category_id"), categoryId: z.number().int().positive() }),
  z.object({ mode: z.literal("by_inventory_ids"), inventoryIds: z.array(z.number().int().positive()).min(1) }),
]);

export const AuditSessionCreateSchema = z.object({
  title: z.string().min(1).max(255),
  auditDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  notes: z.string().max(2000).optional(),
  scope: ScopeSchema,
});
```

---

## Phụ lục A — DDL đề xuất (migration)

```sql
CREATE TABLE inventory_audit_sessions (
  id BIGSERIAL PRIMARY KEY,
  audit_code VARCHAR(50) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  audit_date DATE NOT NULL,
  status VARCHAR(20) NOT NULL,
  location_filter VARCHAR(100),
  category_filter VARCHAR(50),
  notes TEXT,
  created_by INT NOT NULL REFERENCES users (id),
  completed_at TIMESTAMPTZ,
  completed_by INT REFERENCES users (id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_audit_session_status CHECK (
    status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')
  )
);

CREATE TABLE inventory_audit_lines (
  id BIGSERIAL PRIMARY KEY,
  session_id BIGINT NOT NULL REFERENCES inventory_audit_sessions (id) ON DELETE CASCADE,
  inventory_id BIGINT NOT NULL REFERENCES inventory (id),
  system_quantity NUMERIC(12, 4) NOT NULL,
  actual_quantity NUMERIC(12, 4),
  is_counted BOOLEAN NOT NULL DEFAULT FALSE,
  notes VARCHAR(500),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_lines_session ON inventory_audit_lines (session_id);
CREATE INDEX idx_audit_sessions_status ON inventory_audit_sessions (status);
```

_(Đổi tên bảng `inventory` nếu schema thực tế dùng tên khác.)_
