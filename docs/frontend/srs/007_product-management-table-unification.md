# SRS - Dong bo giao dien bang record menu San pham

> Agent: SRS_WRITER  
> Ngay tao: 01/06/2026  
> Pham vi: Frontend Mini-ERP (`frontend/mini-erp`)  
> Trang thai: READY_FOR_TECH_SPEC

## 1. Metadata

- Task ID: `Task007_product_management_table_unification`
- Scope: UI-only, khong doi API/backend contract.
- In-scope screens trong menu `San pham`:
  - `Danh muc san pham` - `/products/categories`
  - `Quan ly san pham` - `/products/list`
  - `Nha cung cap` - `/products/suppliers`
  - `Khach hang` - `/products/customers`
- Out-of-scope:
  - Cac man hinh Kho hang da dong bo truoc do.
  - Orders/POS, Cashflow, Settings.
  - Cau hinh an/hien cot table.
  - Resize cot, keo tha cot, backend/API/database.

## 2. Input va traceability

- User request: sau khi da dong bo table 3 trang Kho hang, tiep theo dong bo 4 giao dien menu San pham de giong nhau.
- CodeGraph preflight:
  - `codegraph status --json`
  - `codegraph sync` vi co pending changes truoc khi doc scope.
  - `codegraph context "product management table UI unification categories products suppliers customers frontend" --format json`
  - `codegraph query "CategoriesPage ProductsPage SuppliersPage CustomersPage ProductTable SupplierTable CustomerTable CategoryTable" --json`
- Evidence files:
  - `docs/dev/frontend/mini-erp/features/FEATURES_UI_INDEX.md`
  - `docs/frontend/srs/SRS_Task118_inventory-table-unification-3-screens.md`
  - `frontend/mini-erp/src/lib/data-table-layout.ts`
  - `frontend/mini-erp/src/features/product-management/pages/CategoriesPage.tsx`
  - `frontend/mini-erp/src/features/product-management/pages/ProductsPage.tsx`
  - `frontend/mini-erp/src/features/product-management/pages/SuppliersPage.tsx`
  - `frontend/mini-erp/src/features/product-management/pages/CustomersPage.tsx`
  - `frontend/mini-erp/src/features/product-management/components/CategoryTable.tsx`
  - `frontend/mini-erp/src/features/product-management/components/ProductTable.tsx`
  - `frontend/mini-erp/src/features/product-management/components/SupplierTable.tsx`
  - `frontend/mini-erp/src/features/product-management/components/CustomerTable.tsx`
  - `frontend/mini-erp/src/features/product-management/components/CategoryToolbar.tsx`
  - `frontend/mini-erp/src/features/product-management/components/ProductToolbar.tsx`
  - `frontend/mini-erp/src/features/product-management/components/SupplierToolbar.tsx`
  - `frontend/mini-erp/src/features/product-management/components/CustomerToolbar.tsx`

## 3. Hien trang va GAP

| ID | GAP | Evidence | Tac dong |
| :-- | :-- | :-- | :-- |
| GAP-1 | 4 table da dung mot phan token trong `data-table-layout.ts`, nhung page shell/footer/loading chua dong nhat. | Products/Customers co error/loading trong shell; Categories/Suppliers co loading/error nam ngoai shell. | User cam thay 4 man hinh cung menu nhung khac mau/bo cuc. |
| GAP-2 | Checkbox selected con dung tone xanh duong (`text-blue-600`, `border-blue-600`). | 4 table component. | Lech voi contract Kho hang va yeu cau han che mau AI/xanh. |
| GAP-3 | Nhan cot con viet tat: `SL SP`, `SĐT`, `Mã NCC`, `Mã KH`, `Tạo SP`, `Tạo NCC`, `Tạo KH`. | Category/Product/Supplier/Customer table + toolbar. | Chua "thuan tieng Viet", kho nhin voi user moi. |
| GAP-4 | Cot `Thao tac` khong dong nhat: icon xoa bi an theo quyen o mot so bang, trong khi Kho hang da yeu cau hien du icon nhung disabled neu khong thao tac duoc. | Product/Supplier/Customer/Category table. | Layout cot thao tac thay doi theo role, mat tinh on dinh. |
| GAP-5 | Footer record counter khong dong nhat: Products/Suppliers/Customers co footer; Categories khong co footer. Noi dung footer cung khac nhau. | 4 page. | Vi tri thong tin so ban ghi khong nhat quan. |
| GAP-6 | Sort control nam ngoai toolbar va label sort hien raw enum o Suppliers/Customers. | SuppliersPage, CustomersPage. | UI sap xep khong cung pattern voi bo loc khac. |
| GAP-7 | Width cot chua can bang: Category `description` va Supplier `address/email` co the hut qua nhieu; Product `categoryName` dang rong ngang productName. | `data-table-layout.ts`. | Table bi lech nhan thi giac, kho scan. |

## 4. Muc tieu nghiep vu

- Dong bo trai nghiem scan record trong 4 man hinh San pham.
- Giu cung ngon ngu thiet ke voi table Kho hang da dong bo: tone trung tinh `slate`, row density on dinh, footer/counter nam cung vi tri.
- Doi label viet tat sang tieng Viet ro nghia.
- Giam layout shift giua role Owner/Admin/Staff khi cot thao tac thay doi.

## 5. Functional requirements

### FR-1 - Table visual contract chung

4 table phai dung cung contract:

- Table shell: `DATA_TABLE_SHELL_CLASS` hoac class tuong duong ve border/radius/shadow.
- Scroll area: `DATA_TABLE_SCROLL_CLASS`.
- Table root: `DATA_TABLE_ROOT_CLASS`.
- Header sticky cung `z-index`, bg, border, typography.
- Row height mac dinh `h-14`, hover/selected state giong nhau.
- Empty state nam trong table body, can giua, chieu cao va mau chu dong nhat.
- Loading/error state nam trong table shell, khong nam roi ben ngoai shell.

### FR-2 - Header/page layout chung

4 page phai co layout:

- Container: padding/gap/h-full/min-h-0/overflow-hidden giong nhau.
- Title typography giong nhau, khong page nao uppercase rieng.
- Mo ta ngan gon, tieng Viet, khong chen ma task vao noi dung user-facing.
- Toolbar nam ngay duoi header va truoc table.
- Sort neu co phai nam trong toolbar hoac trong mot hang dieu khien co style giong nhau.

### FR-3 - Toolbar/filter contract

4 toolbar phai dong nhat:

- Search input cung chieu cao, border, focus tone `slate`, icon search cung mau.
- Filter select cung chieu cao, radius, border, focus tone `slate`.
- Action group can phai cung khoang cach.
- Button tao moi dung label day du:
  - `Tao danh muc`
  - `Tao san pham`
  - `Tao nha cung cap`
  - `Tao khach hang`
- Khong dung label viet tat: `SP`, `NCC`, `KH`, `SĐT`.
- Khi co selection, bulk action hien dung cung vi tri va style.

### FR-4 - Ten cot thuan tieng Viet

Label cot phai doi sang ro nghia:

| Man hinh | Label hien tai | Label moi |
| :-- | :-- | :-- |
| Danh muc san pham | `SL SP` | `So san pham` |
| Nha cung cap | `Ma NCC` | `Ma nha cung cap` |
| Khach hang | `Ma KH` | `Ma khach hang` |
| Khach hang | `SDT` / `SĐT` | `So dien thoai` |
| Khach hang | `Don` | `So don hang` |
| Quan ly san pham | `Ma SKU` | `Ma san pham` hoac `Ma SKU` neu product owner xac nhan SKU la thuat ngu nghiep vu |

Neu label dai, uu tien tang width hop ly/truncate noi dung cell, khong rut gon header bang viet tat.

### FR-5 - Checkbox va selection state

- Tat ca checkbox trong 4 table dung `DATA_TABLE_CHECKBOX_CLASS`.
- Selected row dung nen `bg-slate-50`, khong dung xanh duong.
- Indeterminate state dung cung mau slate.
- Checkbox column width cung `48px`.

### FR-6 - Cot thao tac on dinh

- Cot `Thao tac` phai co width on dinh tren 4 table.
- Tat ca icon thao tac co the xuat hien trong feature phai hien day du theo contract:
  - Xem chi tiet.
  - Chinh sua.
  - Xoa.
  - Rieng Danh muc co them `Them danh muc con`.
- Neu role khong du quyen, icon van hien nhung disabled, co title/tooltip ro:
  - `Chi Owner moi duoc xoa`
  - `Chi Admin moi duoc xoa khach hang`
- Khong an icon lam thay doi kich thuoc/action column theo role.
- Disabled icon khong goi handler.

### FR-7 - Footer/counter dong nhat

Footer phai nam duoi table shell tren 4 page, cung height, padding, bg, border top.

- Products: `Dang hien thi 20 / 35 san pham`.
- Suppliers: `Dang hien thi 20 / 35 nha cung cap`.
- Customers: `Dang hien thi 20 / 35 khach hang`.
- Categories: vi API `GET /categories` chi tra `items` dang cay, footer dung flatten count:
  - `Dang hien thi 12 danh muc`.
  - Neu sau nay API co `total`, doi sang `Dang hien thi X / Y danh muc`.
- Loading more text nam ben phai cung vi tri.
- Huong dan cuon `Cuon xuong de tai them` chi hien neu co next page, style text nho va trung tinh.

### FR-8 - Width/cell alignment

- Width cot phai du de header tieng Viet khong bi vo xau.
- Text chinh dung left align; so luong/tien/count dung right hoac center theo contract.
- Cac cot dai nhu `Dia chi`, `Email`, `Mo ta` truncate trong cell va khong lam day cot hanh dong.
- Khong dung width qua rong cho `Danh muc`, `Dia chi`, `Mo ta` neu lam mat can bang.
- Header/cell width phai khop, khong giat cot khi scroll.

### FR-9 - Status badge

- 4 table dung chung style badge:
  - `Hoat dong`: green semantic tiet che.
  - `Ngung`: slate/neutral.
- Label status phai dong nhat: chon mot trong hai cap va dung toan bo:
  - `Hoat dong` / `Ngung`.
- Khong mix `Ngung`, `Ngung hoat dong`, `Ngừng` khac nhau trong cung scope.

### FR-10 - Error/loading/empty state

- Loading first page hien trong shell, khong tao layout shift.
- Error first page hien trong shell, co message tieng Viet va nut `Thu lai` neu co query refetch.
- Empty state copy rieng tung man hinh nhung style giong nhau.
- Background/spacing khong thay doi khi chuyen tu loading sang empty/data.

## 6. Non-functional requirements

- NFR-1: Khong thay doi API request/response, permission, business rules.
- NFR-2: Khong pha `data-testid` hoac test hien co neu co.
- NFR-3: Build khong phat sinh loi TypeScript.
- NFR-4: Lint khong phat sinh error moi; warning cu neu co phai ghi ro.
- NFR-5: Responsive desktop/tablet/mobile khong bi overlap text/button.
- NFR-6: Khong them palette xanh/tim lam mau chu dao; uu tien `slate`.

## 7. Business rules / permission display

| Feature | Quyen thao tac xoa | UI yeu cau |
| :-- | :-- | :-- |
| Danh muc san pham | Owner | Icon xoa luon hien; disabled neu khong Owner. |
| Quan ly san pham | Owner | Icon xoa luon hien; disabled neu khong Owner. |
| Nha cung cap | Owner | Icon xoa luon hien; disabled neu khong Owner. |
| Khach hang | Admin | Icon xoa luon hien; disabled neu khong Admin. |

Bulk delete:

- Neu khong du quyen, bulk delete khong can hien nhu primary action, nhung neu co hien thi thi phai disabled ro ly do.
- Customer bulk delete hien tai out-of-use; khong bat buoc them bulk delete moi.

## 8. Horizontal analysis

- Root cause giong Task118: thieu contract table day du nen moi component tu chen class rieng.
- Cung pattern can ra soat trong 4 scope:
  - Page shell + toolbar.
  - Table header/body/action column.
  - Footer/counter.
  - Checkbox/selected row.
  - Loading/error/empty state.
  - Dialog detail khong nam trong scope chinh, nhung khong duoc lam mat dong bo neu table action mo dialog.
- Chua ap dung sang Orders/Cashflow de tranh mo rong scope.

## 9. Acceptance criteria

```gherkin
Given user mo 4 man hinh trong menu San pham
When quan sat table shell, header, row, footer
Then 4 man hinh co cung mau nen, border, radius, row height, footer height va typography
```

```gherkin
Given user co role khong du quyen xoa
When mo table San pham, Nha cung cap, Danh muc hoac Khach hang
Then icon xoa van hien trong cot Thao tac
And icon xoa bi disabled
And cot Thao tac khong doi width so voi user co quyen
```

```gherkin
Given table dang co selection
When user chon checkbox o bat ky table nao
Then checkbox va row selected dung slate neutral
And khong con mau xanh duong trong selected state
```

```gherkin
Given user mo Danh muc san pham
When danh sach render xong
Then footer nam cung vi tri voi 3 man hinh con lai
And hien tong so danh muc da flatten
```

```gherkin
Given user mo 4 man hinh San pham
When doc header cot va button tao moi
Then khong con label viet tat `SL SP`, `SĐT`, `NCC`, `KH`, `Tao SP`
```

## 10. Test strategy

- Unit/component:
  - `ProductTable`, `CategoryTable`, `SupplierTable`, `CustomerTable` render action icon disabled theo role.
  - Empty state colSpan dung voi so cot hien tai.
  - Footer counter dung voi total/infinite page va category flatten count.
- Visual/manual QA:
  - Chup desktop va mobile cho 4 route.
  - Kiem tra header/cell/action column khop width khi co/khong co quyen xoa.
  - Kiem tra long label tieng Viet khong overlap.
- Regression:
  - Tao/sua/xem/xoa van goi handler dung.
  - Bulk delete Owner khong bi mat.
  - Customer delete chi Admin.
- Commands:
  - `npm run build`
  - `npm run lint`
  - Test lien quan neu co: product-management table tests.

## 11. Open questions

| ID | Cau hoi | Blocker |
| :-- | :-- | :-- |
| OQ-1 | Header cot san pham nen dung `Ma SKU` hay doi thanh `Ma san pham`? | Non-blocker; mac dinh giu `Ma SKU` neu SKU la thuat ngu nghiep vu. |
| OQ-2 | Customer bulk delete co tiep tuc an/khong dung hay can disabled action khi chon nhieu? | Non-blocker; mac dinh khong them bulk delete moi. |
| OQ-3 | Category footer co can yeu cau backend bo sung total hay dung flatten count FE la du? | Non-blocker; giai doan nay dung flatten count. |

## 12. Ready state

- SRS status: READY_FOR_TECH_SPEC
- De xuat stage tiep theo: TECH_SPEC_WRITER tao handoff cho 4 page + 4 table + 4 toolbar + `data-table-layout.ts`.
