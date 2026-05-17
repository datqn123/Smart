# Playbook: catalog_draft — `product` (sản phẩm / SKU)

## Cột hợp lệ (`columns` và `values`)

| key | label | type | required |
|-----|-------|------|----------|
| skuCode | Mã SKU | string | yes |
| name | Tên SP | string | yes |
| categoryName | Danh mục | string | no |
| baseUnitName | Đơn vị | string | yes |
| costPrice | Giá vốn | number | yes |
| salePrice | Giá bán | number | yes |
| barcode | Barcode | string | no |
| status | Trạng thái | enum | no — `Active` \| `Inactive` |

## Bắt buộc mỗi dòng (`values`)

Mỗi dòng **phải có đủ**: `skuCode`, `name`, `baseUnitName`, `costPrice`, `salePrice`.

- `skuCode`: duy nhất trong bảng; gợi ý dạng `DIEN-TU-001`, `SP-AI-001` (chữ/số/gạch).
- `name`: không để trống; suy từ chủ đề user (vd. "điện tử" → "Sản phẩm điện tử 1", "Sản phẩm điện tử 2").
- `baseUnitName`: mặc định `"Cái"` nếu user không nêu đơn vị.
- `costPrice`, `salePrice`: số ≥ 0; nếu user chỉ nêu một giá → coi là `salePrice`, `costPrice` ≈ 80% giá bán (làm tròn số nguyên).
- `categoryName`: tên danh mục (text), **không** dùng `categoryId`; có thể bỏ qua nếu user không nhắc danh mục.
- `status`: mặc định `Active`.

## Không được

- Bỏ trống `skuCode`, `name`, `baseUnitName`, `costPrice`, `salePrice`.
- Trùng `skuCode` giữa các dòng.
- Dùng key của entity khác (`supplierCode`, `customerCode`, …).
- Sinh `categoryId` hoặc id database.

## Ví dụ một dòng

```json
{ "rowId": "r1", "values": { "skuCode": "DT-001", "name": "Tai nghe Bluetooth 1", "categoryName": "Điện tử", "baseUnitName": "Cái", "costPrice": 40000, "salePrice": 50000, "status": "Active" } }
```
