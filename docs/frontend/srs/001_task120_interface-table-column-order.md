# SRS - Task120 Interface Table Column Order

> Nguoi viet: Agent SRS_WRITER
> Ngay cap nhat: 31/05/2026
> Trang thai: Approved

## 1. Tom tat

- Van de: Trang `Cau hinh giao dien` hien tai hien thi 3 nhom checkbox cung luc, kho thao tac va chua sap xep duoc thu tu cot.
- Muc tieu: Doi sang UI chon mot bang, quan ly cot bang 2 danh sach `Dang hien thi` va `Dang an`, co nut chuyen cot va sap xep thu tu.
- Doi tuong: Owner/Admin/Staff co quyen vao menu Cai dat hien tai.

## 2. Pham vi

### In-scope

- Giu route `/settings/interface`.
- Ap dung cho 3 table Kho hang: `inventory_stock`, `inventory_receipts`, `inventory_dispatch`.
- Ho tro an/hien cot va sap xep thu tu cot hien thi.
- Luu frontend tam bang `localStorage`, tuong thich config cu chi co `hiddenColumns`.

### Out-of-scope

- Backend/API/database that.
- Drag-and-drop, resize width, ap dung ngoai 3 table Kho hang.
- Checkbox chon dong, cot `Thao tac`, footer so ban ghi.

## 3. UI/UX

- Header: `Cau hinh giao dien`, mo ta `Tuy chinh cot hien thi va thu tu cot trong bang du lieu Kho hang.`
- Select `Bang du lieu` gom 3 option.
- Noi dung chi hien thi table dang chon:
  - Trai: `Dang hien thi`, co counter.
  - Phai: `Dang an`, co counter.
  - Nut giua: an/hien cot bang icon mui ten.
  - Nut len/xuong trong panel `Dang hien thi`.
- Cot bat buoc co badge `Bat buoc`, luon nam trong `Dang hien thi`, khong an duoc.
- Mobile xep doc hai danh sach, touch target toi thieu 44px.

## 4. Data Contract

```ts
type SaveTableColumnSettingsBody = {
  items: {
    tableKey: TableKey
    hiddenColumns: string[]
    columnOrder: string[]
  }[]
}
```

- `TableColumnConfig` co them `order: number`.
- Required columns khong duoc ghi vao `hiddenColumns`.
- Neu localStorage cu thieu `columnOrder`, dung thu tu metadata mac dinh.

## 5. Acceptance Criteria

- Chi thay select va 2 danh sach cho table dang chon, khong con 3 section checkbox.
- Chuyen cot sang `Dang an`/`Dang hien thi` cap nhat trang thai `Co thay doi chua luu`.
- Cot required hien badge va khong an duoc.
- Move up/down doi thu tu cot; sau khi luu table render theo thu tu moi.
- Config cu chi co `hiddenColumns` van load duoc.

