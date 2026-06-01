# TECH SPEC Task118 - Inventory table unification (3 screens)

## 1. Input
- SRS: [SRS_Task118_inventory-table-unification-3-screens.md](/D:/do_an_tot_nghiep/project/docs/frontend/srs/SRS_Task118_inventory-table-unification-3-screens.md)

## 2. Scope
- In-scope:
  - `src/features/inventory/components/StockTable.tsx`
  - `src/features/inventory/components/ReceiptTable.tsx`
  - `src/features/inventory/components/DispatchTable.tsx`
  - `src/features/inventory/components/StatusBadge.tsx`
  - `src/features/inventory/components/StockBatchDetailsDialog.tsx`
  - `src/features/inventory/components/ReceiptDetailPanel.tsx`
  - `src/features/inventory/components/DispatchDetailDialog.tsx`
  - `src/features/inventory/components/StockActionDialog.tsx`
  - `src/features/inventory/pages/StockPage.tsx`
  - `src/features/inventory/pages/InboundPage.tsx`
  - `src/features/inventory/pages/DispatchPage.tsx`
  - `src/lib/data-table-layout.ts`
- Out-of-scope:
  - Inventory audit/location pages
  - Modules ngoai Inventory

## 3. Root-cause architecture analysis
- Van de khong nam o 1 file don le ma nam o thieu visual contract tong hop:
  - Token co san nhung thieu token checkbox chung.
  - Nhieu component detail panel duoc style doc lap so voi table contracts.
  - Nhieu nhan cot/tooltip duoc hardcode rieng theo man hinh.

## 4. Implementation slices
### Slice A - Shared contract
- Add `DATA_TABLE_CHECKBOX_CLASS` trong `data-table-layout.ts`.
- Dieu chinh `DATA_TABLE_SHELL_CLASS` ve radius/shadow trung tinh hon.

### Slice B - 3 table records
- `StockTable`:
  - Dung checkbox class chung.
  - Doi cot `NV` -> `Thao tac`.
- `ReceiptTable`:
  - `So HD` -> `So hoa don`.
  - `Dong SP` -> `So dong hang`.
  - Chuan hoa row density.
- `DispatchTable`:
  - Chuan hoa row density.
  - Dam bao action/tooltip tieng Viet.

### Slice C - Status semantics
- `StatusBadge`:
  - Tiet che palette: slate/amber/green/red.
  - Bo xanh duong/tim o dispatch statuses.
  - Nhan dispatch ro nghia van hanh.

### Slice D - Detail table harmonization
- `ReceiptDetailPanel`, `DispatchDetailDialog`, `StockBatchDetailsDialog`, `StockActionDialog`:
  - Don visual decorations lech pattern.
  - Dua ve typography/cell spacing gan voi table records.
  - Giu nguyen hanh vi nghiep vu.

### Slice E - Container consistency
- `StockPage`, `InboundPage`, `DispatchPage`:
  - Shell table cung radius/shadow contract.
  - Khong doi data flow.

## 5. Guardrails
- Khong doi API calls, request/response mapping.
- Khong doi enum backend.
- Khong xoa `data-testid` dang dung.

## 6. Verification plan
- `npm run lint`
- `npm run build`
- Co the bo sung: smoke check 3 route inventory neu can.

## 7. Risks
- R1: E2E co the fragile neu dang assert class cu.
  - Mitigation: giu `data-testid`, khong doi structure semantic table.
- R2: Color change o `StatusBadge` co the anh huong man hinh inventory khac.
  - Mitigation: gioi han thay doi mapping chi theo enum inventory va kiem tra nhanh page usage.

## 8. Coding handoff
- Files to edit: listed in Scope.
- Tests to run: lint + build.
- Readiness: `READY_FOR_CODING`.
