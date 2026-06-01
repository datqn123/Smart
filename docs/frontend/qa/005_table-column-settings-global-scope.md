# QA Spec - Table Column Settings Global Scope

> Agent: QA_SPEC_WRITER  
> Ngay cap nhat: 01/06/2026  
> Trang thai: QA_READY_FOR_CODING

## 1. Test Matrix

- `GET /api/v1/interface-settings/table-columns?scope=inventory` tra effective global settings.
- `PUT /api/v1/interface-settings/table-columns`:
  - Admin/Owner: 200.
  - Staff: 403.
- Payload validation:
  - unknown table key -> 400.
  - unknown column key -> 400.
  - duplicate column in order -> 400.
  - required column in hidden -> 400.
- Frontend:
  - `StockPage`, `InboundPage`, `DispatchPage` dung chung order khi backend da save.
  - Save xong dispatch custom event va page dang mo reload order.
  - GET loi -> fallback default khong crash.

## 2. Regression Scope

- Inventory list tables:
  - `inventory_stock`
  - `inventory_receipts`
  - `inventory_dispatch`
- Khong anh huong:
  - auth refresh flow
  - cac endpoint inventory CRUD khac
  - AI chat.

## 3. Command De Xuat

- Backend:
  - `mvn -q -DskipTests compile`
- Frontend:
  - `npm run build`
  - `npm run test -- mockCatalog`
