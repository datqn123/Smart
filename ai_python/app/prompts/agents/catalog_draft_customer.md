# Playbook: catalog_draft — `customer` (khách hàng)

## Cột hợp lệ (`columns` và `values`)

| key | label | type | required |
|-----|-------|------|----------|
| customerCode | Mã KH | string | yes |
| name | Tên KH | string | yes |
| phone | SĐT | string | yes |
| email | Email | string | no |
| address | Địa chỉ | string | no |
| status | Trạng thái | enum | no — `Active` \| `Inactive` |

## Bắt buộc mỗi dòng (`values`)

Mỗi dòng **phải có đủ**: `customerCode`, `name`, `phone`.

- `customerCode`: duy nhất trong bảng; gợi ý `KH-AI-001`, `KH-VIP-001`.
- `name`: tên khách / công ty; không để trống.
- `phone`: SĐT Việt Nam (10–11 chữ số); các dòng khác nhau không trùng nếu có thể.
- `email`, `address`: điền khi user nêu; có thể bỏ qua.
- `status`: mặc định `Active`.

## Không được

- Trùng `customerCode` giữa các dòng.
- Bỏ trống `phone`.
- Dùng key entity khác (`skuCode`, `supplierCode`, …).

## Ví dụ một dòng

```json
{ "rowId": "r1", "values": { "customerCode": "KH-001", "name": "Khách lẻ Nguyễn A", "phone": "0912345678", "address": "Hà Nội", "status": "Active" } }
```
