# TEST PLAN Task118 - Inventory table unification (3 screens)

## 1. Input docs
- SRS: [SRS_Task118_inventory-table-unification-3-screens.md](/D:/do_an_tot_nghiep/project/docs/frontend/srs/SRS_Task118_inventory-table-unification-3-screens.md)
- Tech Spec: [TECH_SPEC_Task118_inventory-table-unification-3-screens.md](/D:/do_an_tot_nghiep/project/docs/frontend/tech_lead/TECH_SPEC_Task118_inventory-table-unification-3-screens.md)

## 2. QA scope
- Route:
  - `/inventory/stock`
  - `/inventory/inbound`
  - `/inventory/dispatch`
- Components:
  - `StockTable`, `ReceiptTable`, `DispatchTable`
  - `StatusBadge`
  - Detail dialogs/panels in 3 flows

## 3. Horizontal QA analysis
- Same failure class co the lap lai:
  - Label text regression (viet tat/english leak).
  - Class mismatch giua table head/body/action column.
  - Status color mismatch do config mapping.
  - E2E fragile do thay doi className.

## 4. P0 matrix
- P0-1: Stock table renders, sticky header van hoat dong, action column van sticky.
- P0-2: Receipt table hien thi nhan `So hoa don`, `So dong hang`.
- P0-3: Dispatch table van click row mo detail, action buttons van dung.
- P0-4: Checkbox selected state dong nhat tren 3 table (slate theme).
- P0-5: Khong vo build/lint.

## 5. P1 matrix
- P1-1: StatusBadge dispatch khong con tone xanh duong/tim.
- P1-2: Detail panel table typography nhat quan voi records table.
- P1-3: Empty/loading states van doc duoc va khong vo bo cuc.
- P1-4: `data-testid` khong mat o table chinh.

## 6. Failure-mode coverage
- FM-1: Enum status khong map -> fallback label raw.
  - Expect: van render an toan, badge neutral.
- FM-2: Nhieu ten dai trong cell.
  - Expect: truncate/align khong overlap.
- FM-3: No records.
  - Expect: empty state co text ro rang.

## 7. Verification commands
- `npm run lint`
- `npm run build`

## 8. Readiness
- QA status: `QA_READY_FOR_CODING`.
