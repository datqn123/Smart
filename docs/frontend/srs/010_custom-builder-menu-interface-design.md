# SRS - Thiet ke giao dien Menu Custom Builder

> File: `docs/frontend/srs/010_custom-builder-menu-interface-design.md`  
> Agent: SRS_WRITER  
> Ngay tao: 03/06/2026  
> Trang thai: READY_FOR_TECH_SPEC  
> Pham vi: Frontend UI/UX cho chuc nang tao danh muc menu cha va giao dien menu con cua Custom Entity / Workflow Builder.

---

## 1. Tom Tat

Mini ERP can mot giao dien de Owner/Admin tu tao nhom menu va man hinh nghiep vu custom theo cach tuong tu thao tac voi folder va file:

- `Danh muc menu cha` dong vai tro nhu folder tren sidebar.
- `Giao dien menu con` dong vai tro nhu file/page nam trong folder.
- User dat ten, sap xep, gan icon, cau hinh route, entity, layout, workflow va quyen cho tung giao dien con.

Giai doan nay chi viet SRS thiet ke giao dien. Backend, database, API thuc thi va code implementation se lam o cac workflow sau.

---

## 2. Tai Lieu Da Doc

| Nguon | Noi dung ap dung vao SRS |
| :--- | :--- |
| `docs/backend/srs/002_custom-entity-workflow-builder.md` | Backend SRS index, xac nhan scope da tach thanh 8 phase |
| `docs/dev/common/001_custom-builder-program-overview.md` | Nguyen tac metadata-driven, backend authoritative, frontend route/menu hien dang static |
| `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md` | Entity, field, view, record CRUD, route `/settings/custom-builder`, `/custom/:entityKey` |
| `docs/dev/common/003_custom-builder-phase2-workflow.md` | Workflow state/transition, pending guardrail |
| `docs/dev/common/004_custom-builder-phase3-logic-connector.md` | Connector builder luu rule JSON co cau truc |
| `docs/dev/common/005_custom-builder-phase4-inventory-effect.md` | Inventory effect can dry-run/confirm va khong optimistic update |
| `docs/dev/common/006_custom-builder-phase5-ai-builder-copilot.md` | AI chi suggest/diff, khong publish |
| `docs/dev/common/007_custom-builder-phase6-ai-custom-query.md` | Metadata custom la untrusted content khi expose sang AI |
| `docs/dev/common/008_custom-builder-phase7-ai-custom-draft.md` | AI chi tao draft record, user review tren UI |

CodeGraph evidence:

- Frontend hien co pattern danh muc dang tree o `frontend/mini-erp/src/features/product-management/components/CategoryTable.tsx`.
- Frontend route/menu static duoc neu trong program overview la gap can xu ly bang dynamic custom workspace routes.

---

## 3. Muc Tieu

### 3.1 Product Goals

- Owner/Admin tao duoc nhom menu custom de gom cac man hinh nghiep vu.
- Owner/Admin tao duoc giao dien menu con trong mot danh muc menu cha.
- Trai nghiem tao/sua/xoa/sap xep gan voi mo hinh folder/file de user de hieu.
- Giao dien con lien ket duoc voi custom entity/view/workflow theo metadata, khong tao code dong.

### 3.2 UX Goals

- Menu builder co hai hanh dong chinh, hien ro tren man hinh:
  - `Tao danh muc menu cha`
  - `Tao giao dien menu con`
- Cau truc menu hien thi bang tree explorer: folder co the mo/dong, file nam ben trong.
- User dang chon item nao thi panel ben phai hien chi tiet cau hinh cua item do.
- Han che mau sac noi bat; dung tone trung tinh slate/white, nhan manh bang border, icon va state ro rang.

---

## 4. Pham Vi

### 4.1 In Scope

- Thiet ke page Custom Builder menu management, de xuat route:
  - `/settings/custom-builder`
- Them khu vuc tree explorer quan ly:
  - Danh muc menu cha.
  - Giao dien menu con.
- Hai button tao moi nam o khu vuc menu builder:
  - `Tao danh muc menu cha`
  - `Tao giao dien menu con`
- Form tao/sua danh muc menu cha.
- Form tao/sua giao dien menu con.
- Sap xep folder/file bang nut len/xuong hoac drag-and-drop neu Tech Spec chon.
- Preview sidebar/menu sau khi cau hinh.
- Guardrail pending, validation, confirm khi xoa/archive/publish.

### 4.2 Out Of Scope

- Chua implement backend/API/database that.
- Chua tao SQL table vat ly tu UI.
- Chua cho user viet SQL, JavaScript, Groovy, SpEL hoac custom endpoint.
- Chua implement AI Copilot UI trong task nay, chi danh dau diem tich hop tuong lai.
- Chua implement inventory effect builder chi tiet trong man hinh menu.
- Chua ap dung ngoai custom builder.

---

## 5. Builder Phase Boundary

SRS nay phai duoc hieu theo 2 lop scope rieng biet:

| Lop | Trang thai trong phase nay | Mo ta |
| :--- | :--- | :--- |
| Builder management UI | Active | Man hinh `/settings/custom-builder` de tao/sua/sap xep folder/page va xem preview cau hinh |
| Runtime custom menu | Requirement contract | Mo ta cach folder/page da publish di vao sidebar that, chua bat buoc implement trong UI mock dau tien |
| Runtime custom page | Requirement contract | Mo ta route resolver `/custom/:pageKey`, chua bat buoc build day du record table/form trong phase builder UI dau tien |
| Entity/view/workflow tabs | Boundary ro | Tab nao active/placeholder/read-only/disabled duoc quy dinh tai muc 9.2 |
| AI Copilot | Extension point | AI chi de xuat diff; user review/apply; AI khong duoc publish |

### 5.1 Active In First UI Build

- Header, explorer, detail panel.
- Hai button tao folder/page.
- Form thong tin chung cho folder/page.
- Preview cay menu.
- Dirty state, pending state, validation state co ban.

### 5.2 Placeholder / Read-only In First UI Build

- Tab `Du lieu`, `Giao dien`, `Quy trinh`, `Quyen truy cap` co the hien placeholder/read-only summary neu backend metadata chua san sang.
- Tab `Xem truoc` chi can preview cay menu va route/page metadata o muc mock.
- Runtime page `/custom/:pageKey` co the la placeholder route resolver neu Tech Spec chua implement record table/form.

### 5.3 Disabled Until Backend Contract Exists

- Publish that len server.
- Validate workflow/connector/effect that.
- Preview theo role/user neu backend chua tra permission matrix.
- Drag-and-drop persist that neu backend reorder endpoint chua co.

---

## 6. Nguoi Dung Va Quyen

| Role | Quyen tren giao dien |
| :--- | :--- |
| Owner/Admin | Truy cap builder, tao/sua/sap xep/publish danh muc va giao dien con |
| Staff | Khong mac dinh duoc quan ly builder; chi thay menu custom da publish neu co quyen |

Quyen de xuat:

- `can_manage_custom_builder`: quan ly cau hinh menu/entity/view/workflow.
- `can_use_custom_entities`: truy cap workspace custom theo entity permission.

Backend van la nguon validate quyen cuoi cung.

---

## 7. Runtime Integration Requirements

### 7.1 Static + Dynamic Sidebar Merge

Sidebar hien tai co `navConfig` tinh. Khi custom menu runtime san sang, frontend phai merge 2 nguon:

| Nguon | Vai tro |
| :--- | :--- |
| Static menu | Cac module loi san co nhu Kho hang, San pham, Don hang, Cai dat |
| Dynamic custom menu | Folder/page da publish tu Custom Builder |

Merge rules:

1. Static menu khong bi ghi de boi custom menu.
2. Dynamic custom menu nam o vi tri duoc backend tra ve qua `sortOrder` hoac trong mot group rieng `Tuy chinh` neu Product chua chot chen vao root sidebar.
3. Folder custom chi hien khi:
   - `status = Published`.
   - User co quyen thay folder.
   - Co it nhat mot child page published ma user duoc quyen thay.
4. Page custom chi hien khi:
   - `status = Published`.
   - Folder parent hop le va published.
   - User co menu visibility permission.
   - User co entity/data read permission cho `entityKey`.
5. Neu folder co quyen folder nhung toan bo child page bi an vi thieu quyen, folder khong hien.
6. Neu custom route dang active, sidebar phai auto-expand folder custom chua page do.
7. Neu dynamic menu API loi, static menu van phai render binh thuong; custom group hien retry/khong hien tuy Tech Spec chot.

### 7.2 Dynamic Route Resolver

Can co runtime route resolver cho page da publish:

| Route | Purpose |
| :--- | :--- |
| `/custom/:pageKey` | Runtime page resolver theo page key |
| `/custom/:pageKey/:recordId` | Detail route neu page type can record detail |

Resolver rules:

1. Load page definition by `pageKey`.
2. Validate page status published.
3. Validate user menu permission va entity/data permission.
4. Load entity definition, view definition, workflow metadata theo published version.
5. Render page theo `pageType`:
   - `record_list`: table/list runtime.
   - `form`: form create/edit runtime.
   - `table_detail`: table + detail drawer/page.
6. Neu `pageKey` khong ton tai: hien 404 trong app shell.
7. Neu user thieu quyen: hien 403 voi message tieng Viet, khong expose metadata nhay cam.
8. Neu definition da bi archive/hidden: hien empty/error state an toan va khong render stale config.

### 7.3 Runtime Permission Visibility

Permission runtime gom 3 lop, phai AND voi nhau:

| Lop | Vi du | Rule |
| :--- | :--- | :--- |
| Menu permission | User co quyen thay folder/page tren sidebar | Quyet dinh item co hien tren menu hay khong |
| Entity permission | User co quyen doc/tao/sua/xoa entity | Quyet dinh route/page va action record |
| Data permission | User co quyen xem data theo role/store/scope | Quyet dinh record nao duoc query/hien thi |

Frontend chi dung permission de hien/an/disable UI. Backend phai enforce tat ca endpoint.

---

## 8. Mo Hinh Giao Dien

### 8.1 Page Layout

Page `Trinh thiet ke du lieu` gom 3 vung:

| Vung | Noi dung |
| :--- | :--- |
| Header | Title, mo ta ngan, trang thai draft/published, nut `Luu nhap`, `Xem truoc`, `Publish` |
| Left explorer | Tree folder/file, hai nut tao moi, tim kiem nhanh |
| Right detail panel | Form chi tiet cua folder/file dang chon |

Khong dung nhieu card lap lai. Explorer va detail panel la hai panel chinh co border/radius nhe.

### 8.2 Hai Button Chinh

Hai button nam tren dau left explorer:

| Button | Icon de xuat | Hanh vi |
| :--- | :--- | :--- |
| `Tao danh muc menu cha` | `FolderPlus` | Mo form tao folder/menu group moi |
| `Tao giao dien menu con` | `FilePlus` | Mo form tao page trong folder dang chon hoac yeu cau chon folder |

Rules:

- Neu chua co danh muc menu cha, button `Tao giao dien menu con` disabled va hien tooltip `Can tao danh muc menu cha truoc`.
- Neu dang chon mot giao dien con, tao giao dien moi se mac dinh parent la folder cua giao dien dang chon.
- Neu dang chon folder, tao giao dien moi se mac dinh parent la folder do.

### 8.3 Tree Explorer

Tree explorer hien thi:

- Folder row:
  - Icon folder.
  - Ten danh muc menu cha.
  - So luong giao dien con.
  - Nut mo/dong.
  - Menu thao tac: doi ten, sua thong tin, sap xep, archive.
- File row:
  - Icon file/page.
  - Ten giao dien menu con.
  - Badge trang thai: `Ban nhap`, `Da publish`, `Can cau hinh`.
  - Menu thao tac: sua, nhan ban, di chuyen, archive.

Folder va file co selected state bang nen slate nhe hoac border slate. Khong dung mau neon/gradient.

### 8.4 Detail Panel

Khi chon folder:

- Title: ten danh muc.
- Tabs/sections:
  - `Thong tin chung`
  - `Hien thi tren menu`
  - `Quyen truy cap`
  - `Lich su thay doi`

Khi chon giao dien con:

- Title: ten giao dien.
- Tabs/sections:
  - `Thong tin chung`
  - `Du lieu`
  - `Giao dien`
  - `Quy trinh`
  - `Quyen truy cap`
  - `Xem truoc`

---

## 9. Form Danh Muc Menu Cha

### 9.1 Fields

| Field | Required | Mo ta |
| :--- | :---: | :--- |
| `Ten danh muc` | Co | Ten hien thi tren sidebar, vi du `Bao hanh`, `Kiem hang`, `Quan ly noi bo` |
| `Ma danh muc` | Co | Slug/key unique, lowercase/underscore, co the auto-generate tu ten |
| `Icon` | Khong | Chon tu icon allowlist |
| `Mo ta` | Khong | Ghi chu noi bo, khong hien tren sidebar mac dinh |
| `Trang thai` | Co | `Ban nhap`, `Da publish`, `Ngung hien thi` |
| `Thu tu hien thi` | Co | Vi tri trong menu custom |
| `Quyen xem danh muc` | Co | Role/user group duoc thay folder tren menu |

### 9.2 Validation

- Ten danh muc khong duoc rong.
- Ma danh muc unique trong custom menu.
- Ma danh muc chi gom chu thuong, so va dau gach duoi.
- Khong archive folder neu con giao dien con dang publish, tru khi user archive ca nhom sau confirm.

---

## 10. Form Giao Dien Menu Con

### 10.1 Fields

| Field | Required | Mo ta |
| :--- | :---: | :--- |
| `Ten giao dien` | Co | Ten menu con, vi du `Phieu kiem hang hong` |
| `Ma giao dien` | Co | Entity/page key unique |
| `Danh muc menu cha` | Co | Folder chua giao dien nay |
| `Route` | Co | Duong dan de xuat `/custom/{pageKey}` hoac `/custom/{entityKey}` |
| `Loai giao dien` | Co | `Danh sach record`, `Form nhap lieu`, `Bang + chi tiet`, tuy Tech Spec chot |
| `Entity lien ket` | Co | Tao moi entity hoac chon entity custom da co |
| `Mo ta` | Khong | Mo ta nghiep vu |
| `Icon` | Khong | Icon rieng cho menu con neu can |
| `Trang thai` | Co | `Ban nhap`, `Da publish`, `Ngung hien thi` |
| `Quyen xem` | Co | Role/user group co the thay menu con |
| `Quyen tao/sua/xoa record` | Co | Permission cho thao tac record |

### 10.2 Tabs Cau Hinh Va Phase Boundary

| Tab | Noi dung | Trang thai trong phase builder UI dau tien |
| :--- | :--- | :--- |
| `Thong tin chung` | Ten, key, parent folder, route, status | Active/editable |
| `Du lieu` | Entity, field definitions, reference target, required/filterable/sortable | Placeholder hoac read-only summary neu backend chua co |
| `Giao dien` | List columns, form sections, empty state, table footer, action column | Placeholder/read-only; khong build table runtime day du trong phase nay |
| `Quy trinh` | States, transitions, lock edit, transition permission | Disabled/placeholder neu workflow API chua co |
| `Quyen truy cap` | Read/create/update/delete/transition permissions | Active neu co permission catalog, nguoc lai read-only/placeholder |
| `Xem truoc` | Preview sidebar item, preview route/page, preview theo role/user, preview validation | Active mot phan; preview role/user can backend permission matrix |

UI phai hien ro tab nao chua san sang bang badge `Sap ra mat`, `Can backend`, hoac disabled state; khong de user nghi rang tab da co tac dung that.

---

## 11. Draft / Publish / Versioning

### 11.1 Metadata Can Co

Folder va page runtime can them metadata de tranh ghi de khi nhieu Admin cung sua:

```ts
type CustomMenuVersionInfo = {
  version: number
  draftVersion?: number
  publishedVersion?: number
  hasDraft: boolean
  publishedAt?: string
  publishedByName?: string
  updatedAt: string
  updatedByName?: string
  etag: string
  validationSummary?: {
    valid: boolean
    errors: {
      section: "general" | "data" | "view" | "workflow" | "permission" | "runtime"
      message: string
      fieldKey?: string
    }[]
    warnings: {
      section: "general" | "data" | "view" | "workflow" | "permission" | "runtime"
      message: string
    }[]
  }
}
```

### 11.2 Rules

1. Save draft gui `etag` hoac `updatedAt` hien tai.
2. Neu server phat hien version conflict, tra 409; UI hien `Du lieu da duoc cap nhat boi nguoi khac` va cho reload/compare.
3. Publish chi publish draft version da validate pass.
4. Published version bat bien voi runtime cho toi lan publish tiep theo.
5. Runtime sidebar/page chi doc published version, khong doc draft.
6. Builder UI phai hien `hasDraft`, `publishedAt`, `updatedByName`, `validationSummary`.
7. Rename key cua item da published can confirm vi anh huong route/sidebar; Tech Spec co the khoa key sau publish.

---

## 12. Preview Requirements

Preview phai tach ro cac loai sau:

| Preview | Mo ta | Yeu cau |
| :--- | :--- | :--- |
| Preview cay menu | Folder/page trong sidebar | Luon co trong builder UI |
| Preview trang runtime | Trang `/custom/:pageKey` se render nhu the nao | Co the mock/placeholder neu runtime chua san sang |
| Preview theo role/user | Kiem tra Owner/Admin/Staff hoac user cu the thay gi | Can backend permission matrix |
| Preview loi validation | Danh sach loi/warning theo section | Can hien truoc publish |

Preview theo role/user khong duoc thay the backend RBAC; chi la cong cu debug cau hinh.

---

## 13. Reorder / Drag-drop Guardrails

Neu Tech Spec chon reorder bang drag-and-drop hoac nut len/xuong, phai co guardrail:

1. Disable reorder khi save/publish/reorder request dang pending.
2. Khong cho move page sang parent khac neu UI dang o che do reorder noi bo; move parent phai la action rieng co confirm.
3. Khong cho move folder/page vao parent sai loai.
4. Co keyboard fallback: nut len/xuong va focus state ro rang.
5. Khi backend reorder thanh cong, refetch tree hoac apply server order returned.
6. Neu server tra 409 vi thu tu da doi boi Admin khac, UI hien conflict va yeu cau reload/merge.
7. Reorder khong duoc optimistic cho publish/runtime neu backend chua xac nhan.

---

## 14. AI Copilot Extension Point

AI Copilot chua can build trong phase nay, nhung UI/backend contract phai de san extension point:

1. AI chi duoc de xuat thay doi dang structured diff.
2. Diff gom field nao them/sua/xoa, workflow nao them/sua, permission nao thay doi, va risk warning.
3. User phai review va bam apply tung phan hoac apply all.
4. Apply diff chi cap nhat draft, khong publish.
5. AI khong co action publish, archive, execute transition, hay inventory effect.
6. Metadata label/description la untrusted content khi dua vao AI.

---

## 15. Business Rules

| ID | Rule |
| :--- | :--- |
| BR-UI-MENU-01 | Moi giao dien menu con bat buoc thuoc mot danh muc menu cha |
| BR-UI-MENU-02 | User khong tao duoc giao dien menu con neu chua co danh muc menu cha |
| BR-UI-MENU-03 | Folder va file key phai unique trong scope custom builder |
| BR-UI-MENU-04 | Doi ten hien thi khong duoc tu dong doi key neu item da publish |
| BR-UI-MENU-05 | Archive folder co file published phai confirm va hien danh sach file bi anh huong |
| BR-UI-MENU-06 | Publish giao dien con chi enable khi entity/view/workflow toi thieu hop le |
| BR-UI-MENU-07 | Frontend khong duoc coi canvas/form state la source of truth; backend validate truoc khi save/publish |
| BR-UI-MENU-08 | Metadata label/description la untrusted content khi dua vao AI hoac preview HTML |
| BR-UI-MENU-09 | Moi save/publish/delete/archive phai disable button khi pending de tranh double submit |
| BR-UI-MENU-10 | Runtime sidebar chi hien folder khi co it nhat mot child page published ma user duoc quyen thay |
| BR-UI-MENU-11 | Runtime page chi render khi user co menu permission, entity permission va data permission phu hop |
| BR-UI-MENU-12 | Runtime chi doc published version, builder moi duoc doc draft version |
| BR-UI-MENU-13 | Save/publish/reorder phai gui `etag` hoac `updatedAt` de tranh ghi de cau hinh cua Admin khac |
| BR-UI-MENU-14 | AI suggestion chi duoc apply vao draft sau user confirmation, khong duoc publish |

---

## 16. Data Can Backend Cung Cap

### 16.1 Menu Tree Response

```ts
type CustomMenuNode =
  | {
      nodeType: "folder"
      id: string
      key: string
      label: string
      icon?: string
      description?: string
      status: "Draft" | "Published" | "Hidden"
      sortOrder: number
      childCount: number
      permissions: string[]
      children: CustomMenuPageNode[]
      version: number
      hasDraft: boolean
      publishedAt?: string
      etag: string
      validationSummary?: ValidationSummary
      updatedAt: string
      updatedByName?: string
    }
  | CustomMenuPageNode

type CustomMenuPageNode = {
  nodeType: "page"
  id: string
  key: string
  label: string
  icon?: string
  parentKey: string
  routePath: string
  entityKey: string
  status: "Draft" | "Published" | "NeedsConfig" | "Hidden"
  sortOrder: number
  permissions: string[]
  version: number
  hasDraft: boolean
  publishedAt?: string
  etag: string
  validationSummary?: ValidationSummary
  updatedAt: string
  updatedByName?: string
}

type ValidationSummary = {
  valid: boolean
  errors: { section: string; message: string; fieldKey?: string }[]
  warnings: { section: string; message: string }[]
}
```

### 16.2 Suggested API Contract For UI

| Method | Path | Purpose |
| :--- | :--- | :--- |
| GET | `/api/v1/custom/menu-tree` | Lay tree folder/file cho builder va sidebar preview |
| GET | `/api/v1/custom/runtime-menu` | Lay dynamic custom menu da publish theo quyen user hien tai |
| GET | `/api/v1/custom/pages/{pageKey}/runtime` | Resolve runtime page definition cho `/custom/:pageKey` |
| POST | `/api/v1/custom/menu-folders` | Tao danh muc menu cha |
| PATCH | `/api/v1/custom/menu-folders/{folderKey}` | Cap nhat folder |
| POST | `/api/v1/custom/menu-pages` | Tao giao dien menu con |
| PATCH | `/api/v1/custom/menu-pages/{pageKey}` | Cap nhat page |
| POST | `/api/v1/custom/menu/reorder` | Luu thu tu folder/file |
| POST | `/api/v1/custom/menu/validate` | Validate cau hinh truoc publish |
| POST | `/api/v1/custom/menu/publish` | Publish folder/page da hop le |
| POST | `/api/v1/custom/menu/preview` | Preview menu/page theo role/user va validation state |
| DELETE/PATCH | `/api/v1/custom/menu-folders/{folderKey}/archive` | Archive folder |
| DELETE/PATCH | `/api/v1/custom/menu-pages/{pageKey}/archive` | Archive page |

Ten endpoint chinh thuc se do Tech Spec/backend chot, nhung UI can cac capability tren.

---

## 17. UI States

| State | UI behavior |
| :--- | :--- |
| Empty | Hien empty state trong explorer va primary action `Tao danh muc menu cha` |
| Folder selected | Detail panel hien form folder |
| Page selected | Detail panel hien tabs cau hinh page |
| Dirty state | Footer sticky hien `Co thay doi chua luu`, nut `Luu nhap` |
| Save pending | Disable form action, hien loading trong button |
| Publish validation failed | Hien danh sach loi theo tab/section |
| Backend conflict 409 | Hien message version conflict va action reload |
| No permission | Disable action va hien reason |
| Runtime route missing | Hien 404 trong app shell |
| Runtime permission denied | Hien 403, khong expose metadata nhay cam |
| Dynamic menu load failed | Static menu van render, custom menu hien retry hoac an an toan |
| Reorder pending | Disable drag/drop, nut len/xuong, archive va publish |

---

## 18. Acceptance Criteria

```gherkin
Given Owner mo trang Trinh thiet ke du lieu
When trang tai xong
Then explorer hien hai button "Tao danh muc menu cha" va "Tao giao dien menu con"
And neu chua co folder thi nut tao giao dien menu con bi disabled
```

```gherkin
Given Owner bam "Tao danh muc menu cha"
When nhap ten "Kiem hang" va luu
Then tree explorer hien mot folder "Kiem hang"
And folder co the duoc chon de cau hinh chi tiet
```

```gherkin
Given da co folder "Kiem hang"
When Owner chon folder va bam "Tao giao dien menu con"
Then form tao page mo ra voi parent mac dinh la "Kiem hang"
And sau khi luu, page hien ben trong folder nhu mot file trong folder
```

```gherkin
Given Owner chon mot giao dien menu con
When cau hinh entity/view/workflow chua hop le
Then nut Publish bi disabled hoac backend validate tra loi theo tung section
```

```gherkin
Given folder co giao dien con da publish
When Owner archive folder
Then UI yeu cau confirm va hien danh sach giao dien con bi anh huong
```

```gherkin
Given Staff chi co quyen doc page custom "Phieu kiem hang hong"
When sidebar runtime load custom menu
Then folder cha chua page do duoc hien
And cac page khac trong folder bi an neu Staff khong co quyen
```

```gherkin
Given Admin truy cap /custom/phieu_kiem_hang_hong
When page definition da published va Admin co quyen entity/data
Then route resolver render runtime page theo pageType
And neu thieu quyen thi hien 403 an toan
```

```gherkin
Given Admin A va Admin B cung sua mot page custom
When Admin A da luu truoc lam thay doi etag
And Admin B luu voi etag cu
Then backend tra 409
And UI hien conflict reload/compare, khong ghi de cau hinh cua Admin A
```

```gherkin
Given AI Copilot de xuat them field va workflow
When user xem diff
Then user co the apply vao draft
And AI khong co action publish
```

---

## 19. Test Plan

| Nhom | Test | Expected |
| :--- | :--- | :--- |
| Render | Page builder co header, explorer, detail panel | UI dung layout 2 panel |
| Empty | Chua co folder | Chi enable tao folder, disable tao page |
| Create folder | Nhap ten/key hop le | Folder them vao tree |
| Create page | Chon folder roi tao page | Page nam duoi folder dung parent |
| Validation | Key trung/rong | Loi inline, khong save |
| Reorder | Doi thu tu folder/file | Tree va preview cap nhat dung |
| Dirty state | Sua form chua luu | Footer hien `Co thay doi chua luu` |
| Pending guardrail | Bam save/publish | Disable nut trong luc request pending |
| Permission | User khong co quyen | Action disabled hoac an theo policy |
| Archive impact | Folder co page published | Confirm + impact summary |
| Responsive | Mobile/tablet | Explorer va detail xep doc, touch target >= 44px |
| Runtime sidebar | Merge static + dynamic menu | Static menu khong mat, custom folder/page hien dung quyen |
| Runtime route | `/custom/:pageKey` | Resolve published page, 404/403 dung trang thai |
| Version conflict | Save voi etag cu | UI hien conflict, khong ghi de |
| Preview as role | Chon role/user de preview | Hien folder/page theo quyen cua role/user |
| Reorder conflict | Server order da doi | UI hien conflict va yeu cau reload |
| AI diff | AI suggestion | Chi apply vao draft sau user confirmation |

---

## 20. Non-functional Requirements

| Nhom | Yeu cau |
| :--- | :--- |
| Accessibility | Button co label ro, icon co aria-label/tooltip, focus state thay duoc |
| Performance | Tree menu paginate/lazy load neu so luong folder/page lon |
| Reliability | Khong optimistic update cho publish/archive rui ro |
| Security | Khong render label/description nhu HTML unsafe |
| Consistency | Table/list preview dung design table da dong bo gan day |
| Observability | Loi validate/publish can co correlation id neu backend cung cap |

---

## 21. Horizontal Analysis / Root Cause

Van de khong chi la them hai button. Root cause la frontend menu hien dang thien ve static navigation, trong khi custom builder can tach ro 3 lop:

| Lop | Trach nhiem |
| :--- | :--- |
| Menu taxonomy | Folder/page, label, icon, route, sort order, visibility |
| Entity/view metadata | Field, list columns, form sections, record UI |
| Runtime/workflow | Record state, transition, connector/effect, AI draft/query |

SRS nay chi thiet ke UI cho lop `Menu taxonomy` va diem lien ket sang entity/view/workflow. Tech Spec khong nen tron viec tao folder/page voi viec execute workflow hay inventory effect, vi nhu vay se lam builder kho validate va kho dam bao an toan.

Bo sung sau review: neu chi lam builder management UI ma khong dac ta runtime sidebar/route, Tech Spec rat de dung lai o viec them mot page cai dat dep nhung khong giai quyet duoc custom builder hoan chinh. Vi vay SRS nay tach:

- Builder UI: noi user tao va publish cau hinh.
- Runtime sidebar: noi cau hinh da publish xuat hien trong navigation that.
- Runtime route resolver: noi page custom da publish duoc render theo metadata.
- Permission/versioning: lop an toan de tranh expose menu sai quyen va tranh Admin ghi de nhau.

---

## 22. Open Questions

| ID | Cau hoi | De xuat mac dinh |
| :--- | :--- | :--- |
| OQ-UI-MENU-01 | Ten menu chinh dung gi? | `Trinh thiet ke du lieu` |
| OQ-UI-MENU-02 | Co cho folder long nhau khong? | MVP chi 1 cap folder cha + page con |
| OQ-UI-MENU-03 | Route page custom theo `pageKey` hay `entityKey`? | Dung `pageKey`, page lien ket `entityKey` rieng |
| OQ-UI-MENU-04 | Page co duoc di chuyen sang folder khac sau publish khong? | Co, nhung can confirm vi anh huong sidebar |
| OQ-UI-MENU-05 | Staff co thay builder khong? | Khong, chi thay menu custom da publish theo quyen |
| OQ-UI-MENU-06 | Dynamic custom menu chen vao root sidebar hay group rieng? | Mac dinh group rieng `Tuy chinh` neu Product chua chot |
| OQ-UI-MENU-07 | Key co duoc doi sau publish khong? | Mac dinh khoa key sau publish, doi route can action rieng |
| OQ-UI-MENU-08 | Preview theo role dung role mau hay user cu the? | Ho tro role truoc, user cu the sau |

---

## 23. Handoff

Trang thai handoff: `READY_FOR_TECH_SPEC`.

Tech Spec can doc tiep:

- `docs/dev/common/001_custom-builder-program-overview.md`
- `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md`
- `docs/frontend/srs/010_custom-builder-menu-interface-design.md`
- `frontend/mini-erp/src/App.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
- `frontend/mini-erp/src/features/product-management/components/CategoryTable.tsx`
