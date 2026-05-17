# SRS — Task110 AI catalog draft (HITL)

## Mục tiêu

Người dùng mô tả yêu cầu tạo nhiều bản ghi catalog; AI sinh bảng nháp; user chỉnh sửa trên chat; xác nhận ghi DB qua API commit (không SQL ghi trực tiếp).

## Phạm vi v1

- Entity: `product`, `category`, `supplier`, `customer`.
- Nháp lưu bảng `ai_catalog_draft` (TTL 72h).
- Commit từng dòng, báo lỗi partial.
- Resolve FK: `categoryName` → `categoryId`, `parentName` → `parentId`.

## Ngoài phạm vi

- Ảnh multipart sản phẩm khi commit batch.
- Import Excel/CSV.
- PATCH bản ghi đã tồn tại.

## Actors

- User có `can_use_ai` và quyền quản lý entity tương ứng.

## Luồng chính

1. User chat → intent `catalog_data_entry`.
2. Python subgraph → POST draft Spring → SSE `draft`.
3. FE `AiChatDraftTableCard` → PATCH nháp → POST commit.
4. Spring gọi catalog create services.
