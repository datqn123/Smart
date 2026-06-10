# SRS - Custom Builder Settings-first UI Redesign

> File: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Agent: SRS_WRITER  
> Ngay tao: 03/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Thay the: `010_custom-builder-menu-interface-design.md`, `011_custom-builder-ui-gap-plan.md` cho pham vi thiet ke giao dien Custom Builder.  
> Pham vi: Thiet ke lai giao dien cai dat de tao giao dien custom, uu tien ro rang, tung buoc, khong nhoi nhet runtime/workflow/inventory/AI vao mot man hinh.

---

## 1. Ly Do Viet Lai SRS

Giao dien Custom Builder hien tai va cac SRS UI cu dang co xu huong gom qua nhieu lop vao cung mot man hinh:

- Menu folder/page.
- Entity/field metadata.
- Table/form layout.
- Runtime preview.
- Workflow.
- Connector.
- Inventory effect.
- AI copilot.

Ket qua la user kho biet nen bat dau o dau, dang cau hinh cai gi, va hanh dong nao se anh huong den dau. SRS nay viet lai theo huong `settings-first`: truoc tien lam cho giao dien cai dat de tao ra giao dien custom that ro rang, de thao tac, de kiem soat. Cac phan hien thi runtime, workflow, inventory va AI se chi la diem mo rong sau, khong chen vao flow chinh luc dau.

---

## 2. Nguyen Tac Thiet Ke Moi

| Nguyen tac | Yeu cau |
| :--- | :--- |
| One task per screen | Moi buoc chi tap trung mot nhom quyet dinh |
| Progressive disclosure | Chi hien phan nang cao khi user can |
| Settings before runtime | Uu tien UI cai dat tao cau hinh, chua voi runtime display |
| Draft first | Moi thay doi vao draft, user validate/publish sau |
| Backend authoritative | UI chi huong dan, backend validate khi co API that |
| No dangerous action by default | Publish/archive/effect/AI apply phai bi chan neu chua hop le |
| No free script | Khong co SQL/JS/custom endpoint input |
| Human-readable | Label, status, loi, warning phai ro rang bang ngon ngu nghiep vu |

---

## 3. Tai Lieu Bi Thay The / Van Con Gia Tri

| File | Trang thai moi | Cach dung tiep |
| :--- | :--- | :--- |
| `010_custom-builder-menu-interface-design.md` | SUPERSEDED_BY_012 | Chi dung de tham khao y tuong folder/page, khong dung lam SRS UI chinh |
| `011_custom-builder-ui-gap-plan.md` | SUPERSEDED_BY_012 | Chi dung de tham khao horizontal gap, khong dung lam flow UI chinh |
| `docs/dev/common/001-008` | STILL_AUTHORITATIVE | Van la phase nghiep vu/backend/AI, SRS nay chi dinh nghia UI settings-first |

Neu co xung dot giua SRS nay va 010/011 ve UI, SRS nay uu tien hon.

---

## 4. Muc Tieu

### 4.1 Product Goal

Owner/Admin co the tao mot giao dien quan ly moi bang cach di qua cac buoc de hieu:

1. Dat ten giao dien.
2. Chon noi hien thi trong menu.
3. Tao/cau hinh du lieu can quan ly.
4. Chon cach hien thi bang/form.
5. Kiem tra cau hinh.
6. Luu draft hoac publish khi san sang.

### 4.2 UX Goal

- User nhin vao la biet dang o buoc nao.
- Khong can hieu ngay workflow, connector, inventory effect hay AI.
- Khong co man hinh 3-4 panel day dac ngay tu dau.
- Moi loi validation noi dung ro: loi o buoc nao, can sua gi, vi sao publish bi chan.
- Advanced configuration nam trong khu vuc rieng, mac dinh dong.

---

## 5. Out Of Scope Cho Lan Thiet Ke Nay

Lan thiet ke nay chua tap trung vao:

- Runtime page hien thi du lieu that.
- Workflow designer day du.
- Connector/formula builder day du.
- Inventory effect mapping/dry-run that.
- AI copilot panel that.
- Backend API/database implementation.

Cac phan tren co the co placeholder nho de user biet "se co sau", nhung khong duoc chiem dien tich chinh hoac lam flow tao giao dien bi roi.

---

## 6. Cau Truc Giao Dien De Xuat

### 6.1 Route

Route quan ly:

```text
/settings/custom-builder
```

Ten menu de xuat:

```text
Trinh thiet ke giao dien
```

Khong dung ten qua rong nhu `Trinh thiet ke du lieu` neu man hinh dang tap trung vao viec tao giao dien quan ly. Neu sau nay builder lon hon, co the tach menu:

- `Trinh thiet ke giao dien`
- `Cau hinh du lieu custom`
- `Quy trinh custom`

### 6.2 Layout Tong The

Bo cuc moi gom 3 lop, khong phai 5 panel cung luc:

| Lop | Mo ta |
| :--- | :--- |
| Header | Title, status draft, nut quay lai, save draft, validate, publish |
| Main content | Wizard/stepper o giua, noi user cau hinh tung buoc |
| Side summary | Tom tat cau hinh va loi can xu ly, co the collapse |

Left tree explorer chi hien sau khi user da co nhieu giao dien custom. Trong trang tao moi dau tien, khong dat tree explorer lam tam diem.

---

## 7. Information Architecture Moi

### 7.1 Trang Danh Sach Giao Dien Custom

Man hinh dau tien khi vao `/settings/custom-builder` phai la danh sach ro rang, khong auto-select item mock.

Thanh phan:

- Header: `Trinh thiet ke giao dien`.
- Nut primary: `Tao giao dien moi`.
- Search: tim theo ten/key.
- Filter status: `Tat ca`, `Ban nhap`, `Can sua`, `Da publish`, `Ngung hien thi`.
- Table/list cac giao dien:
  - Ten giao dien.
  - Menu cha.
  - Loai hien thi.
  - So truong du lieu.
  - Trang thai.
  - Cap nhat lan cuoi.
  - Hanh dong: sua, xem truoc, nhan ban, ngung hien thi.
- Empty state neu chua co giao dien nao.

Khong hien workflow/AI/inventory o trang danh sach.

### 7.2 Flow Tao Giao Dien Moi

Nut `Tao giao dien moi` mo wizard 5 buoc:

| Buoc | Ten buoc | Muc tieu |
| :--- | :--- | :--- |
| 1 | Thong tin co ban | Dat ten, mo ta, icon, ma giao dien |
| 2 | Vi tri tren menu | Chon tao menu cha moi hoac chon menu cha co san |
| 3 | Du lieu can quan ly | Tao entity va field co ban |
| 4 | Cach hien thi | Chon table/form/detail template va cot hien thi |
| 5 | Kiem tra & luu | Xem tom tat, validation, save draft/publish |

Moi buoc co:

- Title ngan.
- Mo ta mot cau.
- Noi dung form cua buoc do.
- Nut `Quay lai`, `Tiep tuc`.
- Side summary voi cac muc da chon.

Khong hien tab workflow/connector/inventory/AI trong wizard dau.

---

## 8. Chi Tiet Tung Buoc

### 8.1 Buoc 1 - Thong Tin Co Ban

Fields:

| Field | Required | UI |
| :--- | :---: | :--- |
| Ten giao dien | Co | Input |
| Ma giao dien | Co | Input auto-generate, co edit truoc publish |
| Mo ta | Khong | Textarea ngan |
| Icon | Khong | Icon picker allowlist |
| Loai giao dien | Co | Segmented control: `Bang du lieu`, `Form nhap`, `Bang + chi tiet` |

UX rules:

- Khi user nhap ten, ma giao dien auto-generate.
- Neu user da sua ma giao dien thu cong, khong auto-overwrite nua.
- Giai thich ngan: `Ma giao dien dung cho route va tich hop, nen giu ngan gon.`

Validation:

- Ten khong rong.
- Ma chi gom lowercase, number, underscore.
- Ma unique trong scope custom builder.

### 8.2 Buoc 2 - Vi Tri Tren Menu

Muc tieu: user hieu giao dien nay se nam o dau trong sidebar.

UI:

- Radio:
  - `Dung menu cha co san`
  - `Tao menu cha moi`
- Neu dung menu co san: select menu cha.
- Neu tao moi: input ten menu cha, icon menu cha.
- Preview nho sidebar chi gom nhom custom, khong render toan bo app sidebar.

UX rules:

- Neu chua co menu cha, mac dinh chon `Tao menu cha moi`.
- Khong bat user quan ly tree phuc tap o buoc tao dau tien.
- Sap xep/menu tree nang cao de sau trong trang chinh sua.

### 8.3 Buoc 3 - Du Lieu Can Quan Ly

Muc tieu: user tao duoc bo field co ban de giao dien co du lieu.

UI:

- Entity name mac dinh lay theo ten giao dien.
- Field builder dang bang don gian:
  - Ten truong.
  - Ma truong.
  - Kieu du lieu.
  - Bat buoc.
  - Hien tren bang.
  - Hanh dong xoa/sua.
- Nut `Them truong`.
- Mau field goi y theo loai giao dien.

Field type MVP:

| Type | UI |
| :--- | :--- |
| text | Input ngan |
| long_text | Textarea |
| number | Number input |
| money | Money input |
| date | Date picker |
| boolean | Toggle |
| single_select | Option editor |
| reference | Reference target picker |

Reference UI:

- Dung mot type chinh `reference`.
- Target picker gom:
  - Core entity: san pham, kho/vi tri, nha cung cap, khach hang, user.
  - Custom entity published.
- Luu shape canonical:

```json
{
  "refType": "core",
  "refEntityKey": "products",
  "refId": null,
  "labelSnapshot": ""
}
```

Khong dung `product_ref`, `location_ref` lam source chinh trong UI. Co the hien label preset, nhung backend/frontend contract van normalize ve `reference`.

Validation:

- It nhat 1 field.
- Field key unique.
- Field required phai co label.
- Reference phai co target.

### 8.4 Buoc 4 - Cach Hien Thi

Muc tieu: user chon giao dien table/form ro rang, chua can runtime phuc tap.

UI chia thanh 2 tab nho trong buoc:

- `Bang danh sach`
- `Form nhap lieu`

Bang danh sach:

- Chon cot hien thi bang checkbox.
- Keo tha/nut len xuong de doi thu tu cot.
- Chon cot mac dinh sort.
- Chon field co filter nhanh.

Form nhap lieu:

- Chon field hien trong form.
- Nhom field thanh section don gian.
- Doi thu tu field.
- Xem preview form mau.

Preview:

- Preview nam ben phai hoac ben duoi, khong phai full runtime page.
- Preview chi dung sample data.
- Neu mobile, preview chuyen thanh tab rieng `Xem thu`.

Validation:

- It nhat 1 cot table neu loai giao dien co table.
- Form phai gom tat ca field required.
- Cot/filter khong duoc tham chieu field da xoa.

### 8.5 Buoc 5 - Kiem Tra & Luu

Muc tieu: user thay ro cau hinh da san sang hay con thieu.

UI:

- Summary card:
  - Ten giao dien.
  - Menu cha.
  - Route de xuat.
  - So field.
  - Loai hien thi.
  - Quyen mac dinh.
- Validation panel:
  - Loi bat buoc can sua.
  - Canh bao co the sua sau.
- Actions:
  - `Luu ban nhap`
  - `Luu va xem thu`
  - `Publish` disabled neu loi.

Rules:

- `Publish` khong hien noi bat neu chua validate.
- Neu con loi, nut primary la `Sua loi dau tien`.
- Save draft luon cho phep neu du ten + key hop le.

---

## 9. Trang Chinh Sua Sau Khi Tao

Sau khi tao draft, user vao trang edit co sidebar nho theo section, khong quay lai man hinh nhieu panel.

Sections:

| Section | Noi dung |
| :--- | :--- |
| Tong quan | Ten, status, menu, route, summary |
| Du lieu | Field builder |
| Hien thi | Table/form layout |
| Quyen truy cap | Role co the xem/tao/sua/xoa |
| Kiem tra | Validation, preview, publish |
| Nang cao | Workflow/connector/inventory/AI placeholders |

`Nang cao` mac dinh collapsed. Khi feature chua san sang, hien:

```text
Tinh nang nay se duoc cau hinh sau khi giao dien du lieu co ban da on dinh.
```

Khong cho advanced section chiem dien tich chinh.

---

## 10. Permission UX

MVP permission khong nen qua phuc tap.

Default:

- Owner/Admin: quan ly builder.
- Staff: khong quan ly builder.
- Runtime permission cho page custom:
  - `Co the xem`
  - `Co the tao`
  - `Co the sua`
  - `Co the xoa`

UI:

- Permission nam o section rieng sau khi da tao data/view.
- Trong wizard lan dau, chi can chon preset:
  - `Chi quan tri vien`
  - `Nhan vien co quyen module lien quan`
  - `Tuy chinh sau`

Backend van enforce permission cuoi cung.

---

## 11. Trang Thai UI Bat Buoc

| State | UI behavior |
| :--- | :--- |
| Empty | Hien CTA `Tao giao dien moi`, khong hien panel rong phuc tap |
| Draft | Badge `Ban nhap`, cho sua tat ca tru key da publish |
| NeedsConfig | Badge `Can sua`, click vao dua den loi dau tien |
| Published | Badge `Da publish`, canh bao khi sua key/field nguy hiem |
| Loading | Skeleton dung vi tri, khong nhay layout |
| Saving | Disable nut save/next/publish lien quan |
| Validation failed | Hien loi theo buoc, co action jump |
| 409 conflict | Hien reload/compare, khong ghi de |
| 403 | An hoac disable action voi ly do ngan |

---

## 12. Business Rules UI

| ID | Rule |
| :--- | :--- |
| BR-SET-UI-01 | Trang custom builder dau tien phai la danh sach/empty state, khong auto-select mock item |
| BR-SET-UI-02 | Tao giao dien moi phai di qua wizard tung buoc |
| BR-SET-UI-03 | Khong hien workflow/connector/inventory/AI trong flow chinh cua wizard MVP |
| BR-SET-UI-04 | Advanced settings mac dinh collapsed |
| BR-SET-UI-05 | Save draft cho phep truoc publish, nhung publish can validation pass |
| BR-SET-UI-06 | Field reference UI dung canonical `reference` voi `refType/refEntityKey` |
| BR-SET-UI-07 | Form preview chi la preview, khong duoc coi la runtime/source of truth |
| BR-SET-UI-08 | Khong co UI cho SQL/JS/script/custom endpoint |
| BR-SET-UI-09 | Moi mutation co pending disabled state |
| BR-SET-UI-10 | Loi validation phai co nut dua user den noi can sua |

---

## 13. Implementation Plan UI-first Moi

### Stage S0 - Supersede UI Docs

- Danh dau 010 va 011 la superseded.
- Tech Spec tu session moi chi dung 012 lam SRS UI chinh.

### Stage S1 - Builder List Page

- Tao trang danh sach giao dien custom.
- Empty state ro rang.
- CTA `Tao giao dien moi`.
- Mock adapter tra list draft/published.

### Stage S2 - Create Interface Wizard

- Implement 5 buoc:
  - Thong tin co ban.
  - Vi tri tren menu.
  - Du lieu can quan ly.
  - Cach hien thi.
  - Kiem tra & luu.
- Moi buoc co validation rieng.
- Side summary collapse duoc.

### Stage S3 - Edit Interface Settings

- Sau khi tao draft, mo trang edit theo sections:
  - Tong quan.
  - Du lieu.
  - Hien thi.
  - Quyen truy cap.
  - Kiem tra.
  - Nang cao collapsed.

### Stage S4 - Preview Nhe

- Chi lam preview table/form sample data trong settings.
- Chua lam runtime display phuc tap.
- Chua lam workflow/inventory/AI that.

### Stage S5 - Usability QA

- Test desktop/mobile.
- Test user tao giao dien moi tu empty state.
- Test user sua loi validation.
- Test khong bi roi vao advanced section.

---

## 14. Acceptance Criteria

```gherkin
Given Admin mo /settings/custom-builder
When chua co giao dien custom nao
Then UI hien empty state de hieu
And primary action la "Tao giao dien moi"
And khong hien tree/panel cau hinh phuc tap
```

```gherkin
Given Admin bam "Tao giao dien moi"
When wizard mo ra
Then Admin thay 5 buoc ro rang
And moi buoc chi hien form lien quan den buoc do
```

```gherkin
Given Admin dang o buoc Du lieu can quan ly
When them field reference
Then UI bat chon refType va refEntityKey
And khong yeu cau user hieu product_ref/location_ref hard-code
```

```gherkin
Given Admin dang o buoc Kiem tra & luu
When cau hinh con loi
Then Publish bi disabled
And UI co action dua ve buoc loi dau tien
```

```gherkin
Given Admin da tao draft
When mo trang sua cau hinh
Then sections Tong quan, Du lieu, Hien thi, Quyen truy cap, Kiem tra hien ro
And section Nang cao mac dinh collapsed
```

---

## 15. Test Plan

| Nhom | Test | Expected |
| :--- | :--- | :--- |
| Empty state | Chua co item | Hien CTA tao moi, khong hien UI day dac |
| Wizard step | Di chuyen buoc | Khong mat data da nhap |
| Basic info | Key invalid | Loi inline va chan next |
| Menu step | Chua co menu cha | Mac dinh tao menu cha moi |
| Field builder | Them/xoa/reorder field | Summary va preview cap nhat |
| Reference | Chon target reference | Luu canonical ref config |
| Layout | Required field bi an khoi form | Validation loi |
| Review | Con loi | Publish disabled, jump to error |
| Pending | Save draft | Disable buttons lien quan |
| Mobile | Wizard tren mobile | Stepper va summary khong de nhau |
| Advanced | Feature chua san sang | Collapsed/disabled, khong lam roi user |

---

## 16. Handoff Cho Session Moi

Khi mo session moi de implement giao dien, dung prompt:

```text
AUTO_RUN, doc AGENTS.md va docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md.
Trien khai UI-first theo Stage S1-S3 truoc.
Khong sua backend, khong sua ai_python.
Dung fixture/mock adapter frontend.
Loai bo viec bam theo SRS 010/011 cho UI chinh vi da superseded.
```

Session moi phai:

- Chay CodeGraph preflight.
- Tao Tech Spec theo SRS 012.
- Tao QA Spec.
- Implement frontend UI settings-first.
- Verify bang browser/screenshot desktop va mobile.

SRS handoff state: `READY_FOR_TECH_SPEC`.
