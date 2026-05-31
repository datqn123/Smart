# 📄 API SPEC: `GET /api/v1/users/next-staff-code` — Gợi ý mã nhân viên tiếp theo — Task078_02

> **Trạng thái:** Draft  
> **SRS:** [`../../../backend/docs/srs/SRS_Task078-02_next-employee-code-suggestion.md`](../../../backend/docs/srs/SRS_Task078-02_next-employee-code-suggestion.md)

---

## 1. Endpoint

**`GET /api/v1/users/next-staff-code`**

---

## 2. RBAC

- **Bearer JWT** bắt buộc (cùng chế độ Resource Server như `POST /api/v1/users`).
- Chỉ người có quyền **tạo / quản lý nhân viên** (`can_manage_staff` — cùng policy Task078) mới được gọi; không đủ quyền → **403**.

---

## 3. Query

| Tham số | Bắt buộc | Mô tả |
| :------ | :------- | :---- |
| `roleId` | **Có** | `INT` > 0 — khớp `users.role_id` / giá trị gửi khi `POST /api/v1/users`. |
| `staffFamily` | Không (khuyến nghị có) | `ADMIN` \| `MANAGER` \| `WAREHOUSE` \| `STAFF` — dòng mã trên form (cùng nhãn dropdown FE); cho phép **prefix khác nhau** khi cùng `roleId` (seed DB gộp Admin/Manager → một `role_id`). Nếu bỏ qua, BE dùng mặc định theo `roleId` (xem SRS Task078_02). |
| `prefix` | Không | Override thủ công — mặc định **tắt**; không dùng song song nếu chưa có spec bổ sung. |

---

## 4. Response `200 OK`

Envelope chuẩn dự án; `data`:

| Field | Kiểu | Mô tả |
| :---- | :--- | :---- |
| `nextCode` | string | Mã gợi ý tiếp theo, độ dài ≤ 50 (khớp `users.staff_code`). |
| `prefix` | string | Tiền tố đã dùng để tính (echo từ cấu hình sau `roleId`). |
| `roleId` | number | Echo tham số đầu vào. |
| `staffFamily` | string | Echo nếu client đã gửi `staffFamily`. |

Ví dụ:

```json
{
  "success": true,
  "data": {
    "nextCode": "NV-MAN-003",
    "prefix": "NV-MAN",
    "roleId": 2
  },
  "message": "Thành công"
}
```

---

## 5. Lỗi

| HTTP | Khi |
| :--- | :--- |
| **400** | `roleId` thiếu / ≤ 0 / không có trong ánh xạ prefix |
| **401** | Thiếu hoặc JWT không hợp lệ |
| **403** | JWT hợp lệ nhưng không có quyền quản lý nhân viên |

---

## 6. Ghi chú

- Endpoint **chỉ đọc** — không giữ chỗ mã; trùng khi tạo user xử lý bởi unique `staff_code` + **409** (Task078).
