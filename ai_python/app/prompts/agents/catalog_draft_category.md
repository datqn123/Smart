# Playbook: catalog_draft — `category` (product categories)

## Valid columns (`columns` and `values`)

| key | label | type | required |
|-----|-------|------|----------|
| categoryCode | Category Code | string | yes |
| name | Category Name | string | yes |
| parentName | Parent Category | string | no |
| description | Description | string | no |
| sortOrder | Sort Order | number | no |
| status | Status | enum | no — `Active` \| `Inactive` |

## Required per row (`values`)

Each row **must include**: `categoryCode`, `name`.

- `categoryCode`: unique within the table; suggested format `CAT-ELECTRONICS-001`, `CAT-AI-001`.
- `name`: display name for the category; must not be empty.
- `parentName`: parent category name (text) if the user mentions a sub-category; **do not** use `parentId`.
- `sortOrder`: integer ≥ 0 if provided; may be omitted.
- `status`: defaults to `Active`.

## Do not

- Duplicate `categoryCode` across rows.
- Use keys from other entities (`skuCode`, `supplierCode`, …).
- Generate `parentId` or database IDs.

## Example row

```json
{ "rowId": "r1", "values": { "categoryCode": "CAT-EL-001", "name": "Electronics", "parentName": "Goods", "status": "Active" } }
```
