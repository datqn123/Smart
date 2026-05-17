# Playbook: catalog_draft — `supplier` (nhà cung cấp / NCC)

## Cột hợp lệ (`columns` và `values`)

| key | label | type | required |
|-----|-------|------|----------|
| supplierCode | Mã NCC | string | yes |
| name | Tên NCC | string | yes |
| contactPerson | Người liên hệ | string | yes |
| phone | SĐT | string | yes |
| email | Email | string | no |
| address | Địa chỉ | string | no |
| taxCode | MST | string | no |
| status | Trạng thái | enum | no — `Active` \| `Inactive` |

## Bắt buộc mỗi dòng (`values`)

Mỗi dòng **phải có đủ**: `supplierCode`, `name`, `contactPerson`, `phone`.

- `supplierCode`: duy nhất trong bảng; gợi ý `NCC-AI-001`, `NCC-HN-001`.
- `name`: tên công ty / nhà cung cấp; không để trống.
- `contactPerson`: tên người liên hệ; nếu user không nêu → `"Liên hệ"`.
- `phone`: SĐT Việt Nam hợp lệ (10–11 chữ số); các dòng khác nhau không trùng số nếu có thể.
- `email`, `address`, `taxCode`: điền khi user cung cấp hoặc suy hợp lý; có thể bỏ qua.
- `status`: mặc định `Active`.

## Không được

- Trùng `supplierCode` giữa các dòng.
- Bỏ trống `contactPerson` hoặc `phone`.
- Dùng key entity khác (`skuCode`, `customerCode`, …).

## Ví dụ một dòng

```json
{ "rowId": "r1", "values": { "supplierCode": "NCC-001", "name": "Công ty ABC", "contactPerson": "Nguyễn Văn A", "phone": "0901234567", "email": "abc@example.com", "status": "Active" } }
```
