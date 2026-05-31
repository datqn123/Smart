# 🚀 KẾ HOẠCH XÂY DỰNG AGENT API SPEC (RE-DESIGNED)

> **Mục tiêu**: Xây dựng một Agent chuyên biệt để thiết kế tài liệu API chuẩn RESTful, được kích hoạt thủ công và dựa trên cơ sở hiểu biết toàn diện về Use Cases, Quy trình và Thiết kế Database của dự án.

---

## 1. Vai trò và Chế độ hoạt động

- **Tên gọi**: **Agent API Spec** (`API_SPEC`)
- **Vai trò**: Chuyên gia Backend Architect.
- **Chế độ kích hoạt**: **CHỈ HOẠT ĐỘNG KHI ĐƯỢC GỌI TRỰC TIẾP** (Không chạy tự động trong luồng PM).
- **Cơ chế hoạt động**: Khi được gọi, Agent phải "quét" toàn bộ bối cảnh hệ thống trước khi đưa ra bất kỳ thiết kế nào.

---

## 2. Quy trình tiền điều kiện (Pre-requisites)

Trước khi thực hiện thiết kế API cho bất kỳ tính năng nào, Agent API SPEC **BẮT BUỘC** phải đọc và hiểu các tài liệu sau:

1.  **Toàn bộ Use Cases**: Thư mục `UC/` (Activity Diagrams, Use Case Specification).
2.  **Đặc tả chi tiết Use Case**: Toàn bộ các file `UC/Use Case Specification/UC*.txt`.
3.  **Thiết kế Database**:
    *   `UC/Database_Specification.md` (và Part 2).
    *   `UC/Entity_Relationships.md`.
    *   `UC/schema.sql` (để đảm bảo kiểu dữ liệu và ràng buộc thực tế).

---

## 3. Tiêu chuẩn API & Bảo mật (Standards & Security)

Hệ thống API phải tuân thủ nghiêm ngặt các tiêu chuẩn:

- **Kiến trúc**: **RESTful API** chuẩn (Sử dụng đúng các HTTP Methods: GET, POST, PUT, DELETE, PATCH).
- **Định dạng dữ liệu**: JSON (Sử dụng camelCase cho các key).
- **Xác thực (Authentication)**: Sử dụng **Token-based Authentication** (JWT/Bearer Token).
- **Phân quyền (Authorization)**: Dựa trên vai trò người dùng (Admin, Owner, Staff) được định nghĩa trong UC.
- **Response Structure**: Cấu trúc phản hồi thống nhất (Success/Error format).

---

## 4. Nội dung tài liệu API (Output Specs)

Mỗi tài liệu API do Agent tạo ra phải bao gồm:

1.  **Endpoint URL**: `/api/v1/resource-name`
2.  **Method**: (Ví dụ: POST)
3.  **Authentication**: Yêu cầu Token (Yes/No).
4.  **Request Headers**: Chứa `Authorization: Bearer <token>`.
5.  **Request Body / Query Params**: Đặc tả chi tiết các trường, kiểu dữ liệu, bắt buộc/không bắt buộc.
6.  **Business Logic Logic**: Mô tả API sẽ làm gì với Database (CRUD, Triggers, v.v.).
7.  **Response Examples**:
    *   `200 OK` / `201 Created`
    *   `400 Bad Request` (Validation errors)
    *   `401 Unauthorized`
    *   `403 Forbidden`
    *   `500 Internal Server Error`

---

## 5. Kế hoạch triển khai (Implementation Plan - KHÔNG THỰC HIỆN NGAY)

### Bước 1: Soạn thảo AGENTS/API_AGENT_INSTRUCTIONS.md
*   Định nghĩa lệnh triệu hồi: `"Agent API_SPEC, hãy thiết kế API cho [Tính năng/Task] dựa trên UC và DB"`.
*   Thiết lập checklist "Đọc context bắt buộc".

### Bước 2: Tạo Template API chuẩn RESTful
*   Xây dựng file `AGENTS/docs/templates/api/RESTFUL_API_TEMPLATE.md` (hiện tại đã có; trước đây `docs/templates/api/`).

### Bước 3: Đăng ký Agent vào Registry
*   Cập nhật `AGENTS/AGENT_REGISTRY.md`.

---

> [!IMPORTANT]
> **Tình trạng hiện tại**: Đây là bản kế hoạch thiết kế lại. Tôi **CHƯA** thực hiện bất kỳ bước triển khai nào (chưa tạo file instructions hay template) theo yêu cầu của bạn. 
> 
> Hãy cho tôi biết nếu bạn muốn điều chỉnh thêm điều gì trong bản kế hoạch này.
