# QA Spec - Task120 Interface Table Column Order

> Nguoi viet: Agent QA_SPEC_WRITER
> Ngay cap nhat: 31/05/2026
> Trang thai: Approved

## 1. Test Matrix

- Render `/settings/interface`: co title, select 3 table, 2 danh sach.
- Chon table khac: danh sach cot doi theo table.
- Chon cot optional ben trai va bam an: cot sang `Dang an`, hien unsaved state.
- Chon cot ben phai va bam hien: cot ve cuoi `Dang hien thi`.
- Cot required co badge `Bat buoc`, nut an disabled/khong tac dung.
- Move up/down doi thu tu cot trong `Dang hien thi`, disabled o bien tren/duoi.
- Reset default chi reset table dang chon.
- Save ghi localStorage co `hiddenColumns` va `columnOrder`.
- 3 table Kho hang render theo thu tu moi va an/hien dung.
- Empty state colSpan khong vo khi an nhieu cot.
- Storage cu chi co hiddenColumns van load duoc.

## 2. Commands

- `npm run build`
- `npm run lint`

## 3. Regression Scope

- `StockPage`, `InboundPage`, `DispatchPage`.
- `StockTable`, `ReceiptTable`, `DispatchTable`.
- `table-column-settings.ts` adapter migration.

