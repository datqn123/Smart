# Playbook: catalog_draft — `supplier` (suppliers)

## Valid columns (`columns` and `values`)

| key | label | type | required |
|-----|-------|------|----------|
| supplierCode | Supplier Code | string | yes |
| name | Supplier Name | string | yes |
| contactPerson | Contact Person | string | yes |
| phone | Phone | string | yes |
| email | Email | string | no |
| address | Address | string | no |
| taxCode | Tax Code | string | no |
| status | Status | enum | no — `Active` \| `Inactive` |

## Required per row (`values`)

Each row **must include**: `supplierCode`, `name`, `contactPerson`, `phone`.

- `supplierCode`: unique within the table; suggested format `SUP-AI-001`, `SUP-HN-001`.
- `name`: company or supplier name; must not be empty.
- `contactPerson`: contact person name; if the user does not specify → use `"Contact"`.
- `phone`: valid Vietnamese phone number (10–11 digits); rows should not share the same phone if possible.
- `email`, `address`, `taxCode`: fill in when the user provides them or infer reasonably; may be omitted.
- `status`: defaults to `Active`.

## Do not

- Duplicate `supplierCode` across rows.
- Leave `contactPerson` or `phone` empty.
- Use keys from other entities (`skuCode`, `customerCode`, …).

## Example row

```json
{ "rowId": "r1", "values": { "supplierCode": "SUP-001", "name": "ABC Company", "contactPerson": "Nguyen Van A", "phone": "0901234567", "email": "abc@example.com", "status": "Active" } }
```
