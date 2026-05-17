# Playbook: catalog_draft — `customer` (customers)

## Valid columns (`columns` and `values`)

| key | label | type | required |
|-----|-------|------|----------|
| customerCode | Customer Code | string | yes |
| name | Customer Name | string | yes |
| phone | Phone | string | yes |
| email | Email | string | no |
| address | Address | string | no |
| status | Status | enum | no — `Active` \| `Inactive` |

## Required per row (`values`)

Each row **must include**: `customerCode`, `name`, `phone`.

- `customerCode`: unique within the table; suggested format `CUS-AI-001`, `CUS-VIP-001`.
- `name`: customer or company name; must not be empty.
- `phone`: Vietnamese phone number (10–11 digits); rows should not share the same phone if possible.
- `email`, `address`: fill in when the user provides them; may be omitted.
- `status`: defaults to `Active`.

## Do not

- Duplicate `customerCode` across rows.
- Leave `phone` empty.
- Use keys from other entities (`skuCode`, `supplierCode`, …).

## Example row

```json
{ "rowId": "r1", "values": { "customerCode": "CUS-001", "name": "Walk-in Customer Nguyen A", "phone": "0912345678", "address": "Hanoi", "status": "Active" } }
```
