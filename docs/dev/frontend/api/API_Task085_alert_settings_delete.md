# 📄 API SPEC: `DELETE /api/v1/alert-settings/{id}` — Xóa rule cảnh báo — Task085

> **Trạng thái**: Draft  
> **Feature**: UC5

---

## 1. Endpoint

**`DELETE /api/v1/alert-settings/{id}`**

---

## 2. RBAC

Owner của `owner_id` trên bản ghi.

---

## 3. Response

**204 No Content** (không có body).

**Hành vi nghiệp vụ:** không xóa vật lý; `DELETE` = set `isEnabled=false`.

---

## 4. Lỗi

**404**, **401**, **403**, **500**.
