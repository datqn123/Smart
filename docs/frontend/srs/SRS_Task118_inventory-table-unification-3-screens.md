# SRS Task118 - Thong nhat giao dien bang record cho 3 man hinh Kho hang

## 1. Metadata
- Task ID: `Task118`
- Scope: Frontend Mini-ERP (`frontend/mini-erp`)
- In-scope screens:
  - `Ton kho` (`/inventory/stock`)
  - `Phieu nhap kho` (`/inventory/inbound`)
  - `Xuat kho & Dieu phoi` (`/inventory/dispatch`)
- Out-of-scope:
  - Kiem ke, vi tri kho
  - Cac module ngoai Inventory

## 2. Input va traceability
- User request: thiet ke lai de dong nhat table giua 3 man hinh Kho hang, ten hien thi thuan tieng Viet, han che mau sac giong AI.
- Rule workflow bat buoc: `AGENTS.md`, `AGENTS/WORKFLOW_RULE.md`.

## 3. Hien trang va GAP
- Da co token dung chung trong [`data-table-layout.ts`](/D:/do_an_tot_nghiep/project/frontend/mini-erp/src/lib/data-table-layout.ts) nhung chua du contract cho checkbox, empty state, status badge.
- 3 table chinh (`StockTable`, `ReceiptTable`, `DispatchTable`) chua thong nhat:
  - Nhan cot viet tat (`NV`, `So HD`, `Dong SP`).
  - Checkbox selected dung tone xanh duong o nhieu noi.
  - Row density khong dong nhat (`h-14`, `h-16` tron lan).
- Panel/detail trong inbound/dispatch con su dung mau xanh duong/tim va bo cuc gan card marketing, khong cung visual language voi table records.

## 4. Muc tieu nghiep vu
- Dong nhat trai nghiem quet du lieu tren 3 man hinh kho.
- Giam chi phi hoc giao dien cho user van hanh kho.
- Dam bao nhan hien thi thuần tieng Viet trong pham vi 3 man hinh nay.

## 5. Pham vi chuc nang
### FR-1 Table visual contract
- 3 bang chinh phai dung cung visual contract:
  - shell, border, radius, shadow
  - row density
  - sticky action column
  - checkbox selected state

### FR-2 Nhac ten cot tieng Viet
- Chuan hoa nhan cot:
  - `NV` -> `Thao tac`
  - `So HD` -> `So hoa don`
  - `Dong SP` -> `So dong hang`

### FR-3 Mau sac trung tinh
- Khong dung xanh duong/tim lam mau chu dao trong table records.
- Mau chu dao: `slate` + semantic tiet che (`amber`, `green`, `red`) cho trang thai.

### FR-4 Status badge thong nhat cho inbound + dispatch
- `StatusBadge` phai map nhan tieng Viet thong nhat.
- Trang thai dispatch (`Full`, `Partial`, `Cancelled`, `WaitingDispatch`, `Delivering`, `Delivered`) phai co nhan tieng Viet ro nghia van hanh.

### FR-5 Dong bo detail panel trong 3 flow
- Cac bang phu trong chi tiet phieu nhap/xuat va chi tiet lo ton kho phai dung typography va tone mau cung he records.
- Khong dung gradient/trang tri mau lam lech khoi bo nhan dien.

## 6. Non-functional requirements
- NFR-1: Khong thay doi API contract, payload, enum BE.
- NFR-2: Khong pha `data-testid` dang duoc E2E su dung.
- NFR-3: Build/Lint khong duoc phat sinh loi moi do thay doi nay.

## 7. Horizontal analysis
- Cung pattern checkbox/status/table head dang lap lai o nhieu module, nhung Task118 chi thay doi Inventory 3 man hinh de tranh mo rong scope.
- Root cause: thieu contract UI du day du o tang token, dan den moi component chen class rieng.

## 8. Acceptance criteria
- AC-1: 3 bang chinh (`StockTable`, `ReceiptTable`, `DispatchTable`) co visual contract nhat quan.
- AC-2: Trong 3 man hinh, khong con nhan cot viet tat kieu `NV`, `So HD`, `Dong SP`.
- AC-3: Checkbox selected trong 3 bang records dung cung class trung tinh (slate).
- AC-4: Status badge inbound/dispatch khong dung xanh duong/tim lam mau chu dao.
- AC-5: Detail views trong 3 flow khong lech visual language so voi table records.
- AC-6: Lint/Build pass o muc khong loi moi.

## 9. Open questions
- OQ-1 (non-blocker): Co can doi ten `Full` thanh `Da xuat du` va `Partial` thanh `Xuat mot phan` o toan bo app hay chi 3 man hinh nay? Task118 xu ly trong pham vi 3 man hinh.

## 10. Ready state
- SRS status: READY_FOR_TECH_SPEC
