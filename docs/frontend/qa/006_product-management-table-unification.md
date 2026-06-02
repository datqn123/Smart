# QA Spec - Product Management Table Unification

> Agent: QA_SPEC_WRITER  
> Ngay cap nhat: 01/06/2026  
> Trang thai: QA_READY_FOR_CODING

## 1. Test Scope

- Routes:
  - `/products/categories`
  - `/products/list`
  - `/products/suppliers`
  - `/products/customers`
- Components:
  - 4 tables + 4 toolbars + page shells/footers.

## 2. Test Matrix

- Visual consistency:
  - same shell border/radius/shadow.
  - same header/row density and sticky action column behavior.
  - same footer position and spacing.
- Label consistency:
  - no abbreviations (`SL SP`, `SĐT`, `NCC`, `KH`, `Tao SP`).
- Permission behavior:
  - delete action icon always visible.
  - delete icon disabled without permission and click does nothing.
- Selection behavior:
  - checkbox and selected row use neutral slate style in all 4 tables.
- Loading/error/empty:
  - first-load/error shown inside shell.
  - footer counters render correctly (including categories flatten count).

## 3. Regression Focus

- Category expand/collapse tree row behavior still works.
- Select-all and row selection still work.
- Existing CRUD actions still reachable via action buttons.
- Infinite scroll and load-more sentinel on products/suppliers/customers still work.

## 4. Commands

- `npm run build`
- `npm run lint`
