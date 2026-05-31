# 📄 API SPEC: `DELETE /api/v1/users/{userId}` — Xóa / vô hiệu nhân viên — Task081

> **Trạng thái**: Draft  
> **Feature**: UC3 — xóa nhân viên (`EmployeesPage`)

---

## 1. Endpoint

**`DELETE /api/v1/users/{userId}`**

---

## 2. Chiến lược

- **Khuyến nghị (đồng bộ DB + codebase)**: implement `DELETE` như **vô hiệu hóa** tài khoản bằng cách set `users.status = 'Locked'` (soft lock).  
- **Hard delete**: không khuyến nghị vì dễ vỡ FK/audit; nếu cần nên tách endpoint/admin tool riêng.

**HTTP khi thành công**: **`204 No Content`** (không body).

---

## 3. RBAC

Owner / Admin. **Cấm** xóa chính mình; **cấm** xóa user đang là chủ sở hữu tenant duy nhất (policy).

**Gợi ý đồng bộ RBAC**: dùng claim quyền **`can_manage_staff`** (Task078/078_02).

---

## 4. Lỗi

**404**, **409** (còn phiếu/đơn liên quan — RESTRICT), **401**, **403**, **500**.

---

## 5. Zod

Dùng `UserIdParamsSchema` (Task079).
