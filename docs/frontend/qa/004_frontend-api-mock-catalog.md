# QA Spec - Frontend API Mock Catalog

> Agent: QA_SPEC_WRITER  
> Ngay cap nhat: 31/05/2026  
> Trang thai: QA_READY_FOR_CODING

## 1. Test Matrix

- Catalog co entry cho cac endpoint trong SRS.
- Moi entry co `method`, `path`, `auth`, `kind`, `sampleData`.
- Envelope success tra `{ success: true, data }`.
- Envelope error tra `{ success: false, error, message, details? }`.
- List helper tinh `totalPages` dung.
- Lookup helper tim duoc endpoint theo method/path.
- AI stream endpoint duoc danh dau `kind = "sse"` thay vi JSON envelope.

## 2. Commands

- `npm run test -- mockCatalog`
- `npm run build`
- `npm run lint`

