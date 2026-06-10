# SRS - Mo Rong Cai Dat Giao Dien Cho 4 Trang Menu San Pham

> Agent: SRS_WRITER  
> Ngay tao: 01/06/2026  
> Trang thai: READY_FOR_TECH_SPEC  
> Scope chinh: `frontend/mini-erp`  
> Lien quan backend: `backend/smart-erp` table column settings API  
> User request: Da co chuc nang cai dat giao dien voi 3 trang Kho hang, mo rong them 4 trang menu San pham.

## 1. Tom Tat

Hien tai chuc nang `Cau hinh giao dien` da phuc vu 3 bang trong menu `Kho hang`:

- `inventory_stock`
- `inventory_receipts`
- `inventory_dispatch`

Yeu cau moi la mo rong cung co che cai dat cot sang 4 trang trong menu `San pham`:

- `Danh muc san pham` - `/products/categories`
- `Quan ly san pham` - `/products/list`
- `Nha cung cap` - `/products/suppliers`
- `Khach hang` - `/products/customers`

Muc tieu: Admin/Owner cau hinh an/hien cot va thu tu cot cho cac bang San pham, cac user co quyen xem menu tuong ung se nhan effective setting khi reload/refetch.

## 2. Evidence Va Traceability

### Frontend routes/menu

- `frontend/mini-erp/src/App.tsx`
  - `/products/categories` -> `CategoriesPage`
  - `/products/list` -> `ProductsPage`
  - `/products/suppliers` -> `SuppliersPage`
  - `/products/customers` -> `CustomersPage`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
  - `Danh muc san pham`, `Quan ly san pham`, `Nha cung cap`: `can_manage_products`
  - `Khach hang`: `can_manage_customers`

### Frontend table files

- `frontend/mini-erp/src/features/product-management/components/CategoryTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/ProductTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/SupplierTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/CustomerTable.tsx`

### Current settings implementation

- `frontend/mini-erp/src/lib/table-column-settings.ts`
  - Dang khai bao `TableKey` chi gom 3 bang Kho hang.
  - Dang goi `/api/v1/interface-settings/table-columns?scope=inventory`.
- `frontend/mini-erp/src/features/settings/pages/InterfaceSettingsPage.tsx`
  - Dropdown `Bang du lieu` hien theo danh sach setting backend tra ve.
  - Save tat ca item hien co trong `draftSettings`.
- `frontend/mini-erp/src/features/inventory/hooks/useTableVisibleColumns.ts`
  - Hook dang dung rieng trong inventory, co the tong quat hoa hoac tao hook chung.

### Backend current implementation

- `backend/smart-erp/src/main/java/com/example/smart_erp/settings/tablecolumns/model/TableColumnCatalog.java`
  - Catalog metadata moi co 3 key inventory.
- `backend/smart-erp/src/main/java/com/example/smart_erp/settings/tablecolumns/controller/InterfaceSettingsTableColumnsController.java`
  - GET chi chap nhan `scope=inventory`.
  - PUT save inventory scope.
- `backend/smart-erp/src/main/resources/db/migration/V54__task122_global_table_column_settings.sql`
  - Check constraint `table_key IN ('inventory_stock', 'inventory_receipts', 'inventory_dispatch')`.

## 3. Problem Statement

Neu chi them UI table settings o frontend ma khong mo rong backend catalog/DB constraint, save se fail voi table key moi.

Neu chi them backend key ma khong wire 4 table product-management vao hook visible columns, trang `Cau hinh giao dien` co the luu thanh cong nhung table thuc te khong thay doi.

Root cause can xu ly dung la table-column-settings hien dang bi dong khung theo `inventory scope`, trong khi business muon bien no thanh cau hinh giao dien dung chung cho nhieu module.

## 4. Proposed Scope

### In scope

- Mo rong table-column-settings cho 4 table menu San pham.
- Giu source-of-truth backend global setting hien co.
- Trang `Cau hinh giao dien` hien du 7 bang:
  - 3 bang Kho hang hien co.
  - 4 bang San pham moi.
- 4 table San pham doc `visibleColumnKeys` tu effective setting backend.
- Save/invalidate van dung co che global va event hien tai.

### Out of scope

- Resize cot, drag-drop bang mouse.
- Personal user override.
- Role-specific setting.
- Them setting cho Orders/Cashflow/Analytics.
- Doi API CRUD san pham/danh muc/nha cung cap/khach hang.
- Refactor visual table UI ngoai pham vi can thiet de an/hien-thu tu cot.

## 5. Table Key De Xuat

| Table key | Route | Label UI | Permission doc |
| :-- | :-- | :-- | :-- |
| `product_categories` | `/products/categories` | `Danh muc san pham` | `can_manage_products` |
| `product_list` | `/products/list` | `San pham` | `can_manage_products` |
| `product_suppliers` | `/products/suppliers` | `Nha cung cap` | `can_manage_products` |
| `product_customers` | `/products/customers` | `Khach hang` | `can_manage_customers` |

Ghi chu: Ten key uu tien tieng Anh, on dinh theo module, khong bam vao route qua chat de tranh doi route lam mat config.

## 6. Column Metadata De Xuat

### 6.1 Danh muc san pham - `product_categories`

| Key | Label | Required | Default order |
| :-- | :-- | :-- | :-- |
| `categoryCode` | `Ma phan loai` | true | 0 |
| `categoryName` | `Ten danh muc` | true | 1 |
| `productCount` | `So san pham` | false | 2 |
| `description` | `Mo ta` | false | 3 |
| `status` | `Trang thai` | false | 4 |

### 6.2 San pham - `product_list`

| Key | Label | Required | Default order |
| :-- | :-- | :-- | :-- |
| `skuCode` | `Ma san pham` | true | 0 |
| `productName` | `Ten san pham` | true | 1 |
| `categoryName` | `Danh muc` | false | 2 |
| `stock` | `Ton kho` | false | 3 |
| `price` | `Gia ban` | false | 4 |
| `status` | `Trang thai` | false | 5 |

### 6.3 Nha cung cap - `product_suppliers`

| Key | Label | Required | Default order |
| :-- | :-- | :-- | :-- |
| `supplierCode` | `Ma nha cung cap` | true | 0 |
| `supplierName` | `Nha cung cap` | true | 1 |
| `contactName` | `Nguoi lien he` | false | 2 |
| `email` | `Email` | false | 3 |
| `address` | `Dia chi` | false | 4 |
| `status` | `Trang thai` | false | 5 |

### 6.4 Khach hang - `product_customers`

| Key | Label | Required | Default order |
| :-- | :-- | :-- | :-- |
| `customerCode` | `Ma khach hang` | true | 0 |
| `customerName` | `Khach hang` | true | 1 |
| `phone` | `So dien thoai` | false | 2 |
| `email` | `Email` | false | 3 |
| `orderCount` | `So don hang` | false | 4 |
| `status` | `Trang thai` | false | 5 |

Ghi chu: Cot checkbox/select va cot `Thao tac` khong nam trong setting. Hai cot nay la cot he thong, luon hien de giu thao tac on dinh.

## 7. Functional Requirements

### FR-1: Backend catalog phai ho tro 7 table key

- `TableColumnCatalog` phai them 4 key San pham.
- `inventoryScope()` nen doi thanh scope tong quat hon hoac them scope moi:
  - `inventory`
  - `products`
  - `all`
- API can co cach tra ve ca 7 table cho trang `Cau hinh giao dien`.
- Neu tiep tuc dung endpoint cu, de xuat:
  - `GET /api/v1/interface-settings/table-columns?scope=all`
  - `GET /api/v1/interface-settings/table-columns?scope=inventory`
  - `GET /api/v1/interface-settings/table-columns?scope=products`

### FR-2: DB constraint phai chap nhan table key moi

- Migration moi phai update check constraint cua `global_table_column_settings`.
- Neu van giu bang `user_table_column_settings` de backward compatibility, can update constraint o bang cu hoac xac nhan bang cu khong con dung.

### FR-3: Frontend settings page hien nhom module

- Trang `Cau hinh giao dien` phai hien 7 bang.
- Dropdown `Bang du lieu` nen phan nhom hoac label ro:
  - `Kho hang - Ton kho`
  - `Kho hang - Phieu nhap kho`
  - `Kho hang - Xuat kho & Dieu phoi`
  - `San pham - Danh muc san pham`
  - `San pham - San pham`
  - `San pham - Nha cung cap`
  - `San pham - Khach hang`
- Copy hien tai `cho toan bo nguoi dung co quyen Kho hang` phai doi thanh copy tong quat:
  - `cho toan bo nguoi dung co quyen tren tung module`.

### FR-4: Product-management pages phai doc effective setting

- 4 page phai dung chung helper/hook table column settings.
- Moi page truyen `visibleColumnKeys` vao table component tuong ung.
- Neu API settings loi, fallback ve order/visible mac dinh cua chinh table do.
- Save config xong, cac page dang mo cung tab doc lai setting qua event hien co.

### FR-5: Table components phai render theo visibleColumnKeys

- `CategoryTable`, `ProductTable`, `SupplierTable`, `CustomerTable` can nhan prop:
  - `visibleColumnKeys?: string[]`
- Cac cot business phai render theo order cua `visibleColumnKeys`.
- Required columns luon visible, ke ca khi payload backend co hidden sai.
- Cot select/action khong bi anh huong.

### FR-6: RBAC

- GET settings:
  - User co `can_manage_inventory`, `can_manage_products`, hoac `can_manage_customers` co the doc effective settings lien quan.
  - De don gian giai doan dau: authenticated user co it nhat mot quyen module duoc doc settings.
- PUT global settings:
  - Chi `Owner|Admin`.
  - Tiep tuc dung gate hien co `can_manage_staff` neu do la cach xac dinh Admin/Owner trong project.
  - Backend service van phai check role claim `Owner|Admin`, khong chi tin frontend.

### FR-7: API response backward compatible

- Contract response `items[]` giu shape:
  - `tableKey`
  - `tableLabel`
  - `columns[]`
  - `updatedAt`
  - `updatedByName`
- Co the bo sung optional:
  - `moduleKey`
  - `moduleLabel`
  - `scopeType`
- Frontend phai tolerate field optional de khong vo voi data cu.

## 8. Backend HTTP Contract De Xuat

### GET all settings

```http
GET /api/v1/interface-settings/table-columns?scope=all
Authorization: Bearer <token>
```

Response:

```json
{
  "items": [
    {
      "tableKey": "product_list",
      "tableLabel": "San pham",
      "moduleKey": "products",
      "moduleLabel": "San pham",
      "scopeType": "GLOBAL",
      "columns": [
        { "key": "skuCode", "label": "Ma san pham", "required": true, "visible": true, "order": 0 },
        { "key": "productName", "label": "Ten san pham", "required": true, "visible": true, "order": 1 },
        { "key": "categoryName", "label": "Danh muc", "required": false, "visible": true, "order": 2 },
        { "key": "stock", "label": "Ton kho", "required": false, "visible": true, "order": 3 },
        { "key": "price", "label": "Gia ban", "required": false, "visible": true, "order": 4 },
        { "key": "status", "label": "Trang thai", "required": false, "visible": true, "order": 5 }
      ],
      "updatedAt": "2026-06-01T10:00:00Z",
      "updatedByName": "System Administrator"
    }
  ]
}
```

### PUT settings

```http
PUT /api/v1/interface-settings/table-columns
Authorization: Bearer <admin_or_owner_token>
Content-Type: application/json
```

Request:

```json
{
  "scope": "all",
  "items": [
    {
      "tableKey": "product_list",
      "hiddenColumns": ["price"],
      "columnOrder": ["skuCode", "productName", "stock", "categoryName", "status", "price"]
    }
  ]
}
```

## 9. Horizontal Analysis

- Inventory va Products nen dung cung engine settings, khong tao 2 helper song song.
- DB constraint la diem de vo ngang: neu them frontend key ma quen migration, save fail.
- Mock catalog/API docs can cap nhat quyen va sample data, neu khong test/mock drift.
- Product tables hien co co cot select/action va role-dependent action; settings chi nen dieu khien business columns.
- Category tree co nested data; setting cot khong duoc pha indent/tree expand trong cot `categoryName`.
- Products page co image/gallery/dialog logic; hide/reorder business columns khong duoc tac dong create/edit/detail dialogs.
- Customer route dung permission `can_manage_customers`, khac 3 page con lai la `can_manage_products`; GET scope all phai tinh den quyen nay.

## 10. Acceptance Criteria

```gherkin
Given Admin vao Cau hinh giao dien
When mo dropdown Bang du lieu
Then thay du 7 bang gom 3 bang Kho hang va 4 bang San pham
```

```gherkin
Given Admin an cot Gia ban cua bang San pham
When Admin bam Luu thay doi
And reload /products/list
Then cot Gia ban khong hien trong table San pham
And cot checkbox va cot Thao tac van hien
```

```gherkin
Given Admin doi thu tu cot Khach hang thanh Ma khach hang, Khach hang, So don hang, So dien thoai, Email, Trang thai
When Staff/Admin co quyen Khach hang reload /products/customers
Then table hien dung thu tu cot da cau hinh
```

```gherkin
Given backend settings API bi loi
When user vao /products/suppliers
Then table Nha cung cap van render theo cot mac dinh
And trang khong crash
```

```gherkin
Given user khong phai Owner/Admin
When goi PUT table-column-settings voi tableKey product_list
Then backend tra 403
And frontend hien thong bao khong co quyen cau hinh giao dien toan he thong
```

## 11. Test Strategy

- Frontend unit/component:
  - Normalize settings cho 7 table.
  - Fallback default khi API fail.
  - `ProductTable`, `CategoryTable`, `SupplierTable`, `CustomerTable` render theo `visibleColumnKeys`.
  - Required columns khong bi an.
  - Select/action columns luon hien.
- Backend service:
  - Catalog tra du metadata 7 table.
  - Save key product hop le thanh cong.
  - Save unknown key/unknown column/duplicate order -> 400.
  - Staff PUT -> 403.
- Integration/manual:
  - Admin save setting product, user khac reload thay doi.
  - Test 4 routes products.
  - Test existing 3 routes inventory khong regression.
- Commands:
  - Backend: `mvnw -q -DskipTests compile`
  - Frontend: `npm run build`
  - Targeted tests neu co: product-management table tests va table-column-settings tests.

## 12. Open Questions

| ID | Cau hoi | De xuat mac dinh |
| :-- | :-- | :-- |
| OQ-1 | Scope API nen mac dinh `all` hay giu `inventory` neu khong truyen scope? | Giu default `inventory` de backward compatible; settings page moi goi `scope=all`. |
| OQ-2 | Co can chia UI thanh tab `Kho hang` / `San pham` trong Cau hinh giao dien? | Co nen lam neu dropdown 7 item bat dau dai; khong blocker. |
| OQ-3 | Customer settings co nen visible voi user chi co `can_manage_customers` khong co `can_manage_products`? | Co, vi Khach hang la route rieng permission. |
| OQ-4 | Co migrate data cu cua inventory vao global all-scope moi khong? | Khong can neu van dung chung bang global hien tai. |

## 13. Ket Luan

Task nay nen mo rong table-column-settings thanh engine dung chung cho nhieu module, thay vi hard-code inventory. Giai phap dung san nen them 4 `tableKey` San pham vao backend catalog/DB constraint, cho settings page goi `scope=all`, va wire 4 table product-management vao hook visible columns chung.

Trang thai SRS: READY_FOR_TECH_SPEC.
