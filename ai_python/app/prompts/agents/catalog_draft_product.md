# Playbook: catalog_draft — `product` (products / SKUs)

## Valid columns (`columns` and `values`)

| key | label | type | required |
|-----|-------|------|----------|
| skuCode | SKU Code | string | yes |
| name | Product Name | string | yes |
| categoryName | Danh mục (tên) | string | yes* |
| categoryCode | Mã danh mục | string | no |
| baseUnitName | Unit | string | yes |
| costPrice | Cost Price | number | yes |
| salePrice | Sale Price | number | yes |
| barcode | Barcode | string | no |
| status | Status | enum | no — `Active` \| `Inactive` |

## Required per row (`values`)

Each row **must include**: `skuCode`, `name`, `baseUnitName`, `costPrice`, `salePrice`.

- `skuCode`: unique within the table; suggested format `ELECTRONICS-001`, `SP-AI-001` (letters/digits/hyphens).
- `name`: must not be empty; infer from the user's topic (e.g. "electronics" → "Electronics Product 1", "Electronics Product 2").
- `baseUnitName`: defaults to `"Piece"` if the user does not specify a unit.
- `costPrice`, `salePrice`: numbers ≥ 0; if the user mentions only one price → treat it as `salePrice`, set `costPrice` ≈ 80% of sale price (round to integer).
- **Danh mục bắt buộc**: `categoryName` *hoặc* `categoryCode` — phải **đã có trong database** (Active). Không bịa danh mục mới khi tạo sản phẩm qua nháp này.
- `categoryName`: tên danh mục đúng như trên hệ thống; **do not** use `categoryId`.
- `status`: defaults to `Active`.

## Do not

- Leave `skuCode`, `name`, `baseUnitName`, `costPrice`, or `salePrice` empty.
- Duplicate `skuCode` across rows.
- Use keys from other entities (`supplierCode`, `customerCode`, …).
- Generate `categoryId` or database IDs.

## Example row

```json
{ "rowId": "r1", "values": { "skuCode": "EL-001", "name": "Bluetooth Headphones 1", "categoryName": "Electronics", "baseUnitName": "Piece", "costPrice": 40000, "salePrice": 50000, "status": "Active" } }
```
