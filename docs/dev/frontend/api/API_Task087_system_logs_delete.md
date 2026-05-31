# 📄 API SPEC: `DELETE /api/v1/system-logs/{id}` — Xóa một nhật ký — Task087

> **Trạng thái**: Draft  
> **Feature**: `LogsPage` — xóa đơn (tuỳ chính sách tuân thủ; mặc định **chỉ Admin**)

---

## 1. Endpoint

**`DELETE /api/v1/system-logs/{id}`**

---

## 2. Cảnh báo nghiệp vụ

Nhiều hệ thống **cấm xóa** log bảo mật — nếu policy vậy, endpoint trả **403** + thông báo, và UI ẩn nút xóa. Task này mô tả khi **cho phép** purge (ví dụ lỗi nhập tay, GDPR test).

---

## 3. RBAC

Chỉ **Admin** (`role` = `Admin` và `mp.can_view_system_logs`) được gọi endpoint; policy hiện tại **cấm xóa** log → **403** (không thực hiện DELETE).

> **Đồng bộ:** [`SRS_PRD_system-audit-unified-admin-view.md`](../../../docs/backend/srs/SRS_PRD_system-audit-unified-admin-view.md) · Task086 RBAC xem log.

---

## 4. `204` / `200`

> **[CẦN CHỐT]** Dự án thường dùng envelope JSON; nếu cần đồng nhất, chọn `200` với body theo `API_RESPONSE_ENVELOPE.md`.  
> Nếu muốn “chuẩn REST” có thể dùng `204 No Content`.

---

## 5. Lỗi

**404**, **401**, **403**, **500**.
