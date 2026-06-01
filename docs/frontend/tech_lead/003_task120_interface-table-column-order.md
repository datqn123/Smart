# Tech Spec - Task120 Interface Table Column Order

> Nguoi viet: Agent TECH_SPEC_WRITER
> Ngay cap nhat: 31/05/2026
> Trang thai: Approved

## 1. Huong tiep can

- Nang cap `table-column-settings.ts` de metadata co `order`, payload co `columnOrder`.
- Giu tuong thich localStorage cu bang cach doc duoc map `{ [tableKey]: hiddenColumns[] }`.
- Doi hook inventory tu Set visible sang ordered keys de table render header/cell theo thu tu.
- Viet lai `InterfaceSettingsPage` thanh mot bo quan ly 2 danh sach cho table dang chon.

## 2. Thay doi ky thuat

- `TableColumnConfig`: them `order: number`.
- `SaveTableColumnSettingsBody.items[]`: them `columnOrder: string[]`.
- Storage moi chap nhan shape:

```ts
Record<TableKey, { hiddenColumns: string[]; columnOrder: string[] }>
```

- Adapter doc ca storage cu:
  - Array cu => `hiddenColumns`.
  - Object moi => `hiddenColumns` + `columnOrder`.
- Hook moi `useTableColumnOrder(tableKey, defaultColumnKeys)` tra ve `string[]` ordered visible keys.
- 3 table dung mappers `{ key, head, cell }`, render theo ordered keys va tinh `colSpan` = visible data columns + system columns.

## 3. UI Mapping

- `InterfaceSettingsPage` state:
  - `selectedTableKey`
  - `draftSettings`
  - `selectedVisibleKey`
  - `selectedHiddenKey`
- `Hide`: chi thuc hien neu selected visible column khong required.
- `Show`: dua column vao cuoi danh sach hien thi.
- `Move up/down`: swap item trong `columns` cua table dang chon.
- `Reset default`: chi reset table dang chon.
- `Save`: save ca 3 settings hien tai.

## 4. Rui ro va fallback

- Neu storage loi JSON hoac thieu key, dung metadata mac dinh.
- Neu `columnOrder` co key la, bo qua key la va noi cac key metadata con thieu vao cuoi.
- Khong thay doi width constants trong `data-table-layout.ts`.

