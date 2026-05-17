# Playbook: catalog_draft — `category` (danh mục sản phẩm)

## Cột hợp lệ (`columns` và `values`)

| key | label | type | required |
|-----|-------|------|----------|
| categoryCode | Mã DM | string | yes |
| name | Tên danh mục | string | yes |
| parentName | Danh mục cha | string | no |
| description | Mô tả | string | no |
| sortOrder | Thứ tự | number | no |
| status | Trạng thái | enum | no — `Active` \| `Inactive` |

## Bắt buộc mỗi dòng (`values`)

Mỗi dòng **phải có đủ**: `categoryCode`, `name`.

- `categoryCode`: duy nhất trong bảng; gợi ý `CAT-DIEN-TU-001`, `DM-AI-001`.
- `name`: tên danh mục hiển thị; không để trống.
- `parentName`: tên danh mục cha (text) nếu user nói cấp con; **không** dùng `parentId`.
- `sortOrder`: số nguyên ≥ 0 nếu có; có thể bỏ qua.
- `status`: mặc định `Active`.

## Không được

- Trùng `categoryCode` giữa các dòng.
- Dùng key sản phẩm/NCC/KH (`skuCode`, `supplierCode`, …).
- Sinh `parentId` hoặc id database.

## Ví dụ một dòng

```json
{ "rowId": "r1", "values": { "categoryCode": "CAT-DT-001", "name": "Điện tử", "parentName": "Hàng hóa", "status": "Active" } }
```
