# Playbook: inventory_draft — `stock_receipt` (phiếu nhập kho)

## Header (`header`)

| key | required | Ghi chú |
|-----|----------|---------|
| supplierName | yes* | Tên NCC (*hoặc supplierCode) |
| supplierCode | no | Mã NCC nếu user nêu |
| receiptDate | yes | `YYYY-MM-DD`, mặc định hôm nay |
| invoiceNumber | no | Số hóa đơn |
| notes | no | Ghi chú phiếu |
| saveMode | yes | `draft` hoặc `pending` — mặc định `draft` |

## Dòng hàng (`lines[].values`)

| key | label | required |
|-----|-------|----------|
| skuCode | Mã SKU | yes |
| productName | Tên SP | no (hỗ trợ hiển thị / fallback resolve) |
| quantity | Số lượng | yes, số nguyên > 0 |
| costPrice | Giá vốn | yes, số ≥ 0 |
| batchNumber | Số lô | no |
| expiryDate | HSD | no, `YYYY-MM-DD`, nếu có thì ≥ receiptDate |

## Bắt buộc

- Ít nhất **1 dòng**; tối đa **20 dòng**.
- `skuCode` phải có trên mỗi dòng (sản phẩm đã tồn tại trong hệ thống — user sẽ chọn/sửa nếu sai).
- Không dùng cột catalog (`salePrice`, `customerCode`, …).
- Không sinh `productId`, `supplierId`, `unitId` — hệ thống resolve lúc commit.

## Ví dụ

User: *"Tạo phiếu nhập 10 máy tính từ NCC ABC"*

```json
{
  "header": {
    "supplierName": "ABC",
    "receiptDate": "2026-05-17",
    "saveMode": "draft",
    "invoiceNumber": "",
    "notes": ""
  },
  "lineColumns": [...],
  "lines": [
    {
      "lineId": "l1",
      "values": {
        "skuCode": "PC-001",
        "productName": "Máy tính",
        "quantity": 10,
        "costPrice": 8000000
      }
    }
  ]
}
```
