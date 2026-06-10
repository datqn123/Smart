# SRS-023 — Audit logic & nhất quán các giao diện quản lý (trừ Cài đặt)

**Ngày:** 2026-06-07
**Tác giả:** SRS_WRITER (auto)
**Trạng thái:** Draft
**Dạng tài liệu:** Audit / chẩn đoán (liệt kê vấn đề + khuyến nghị theo mức ưu tiên — **không ép một chuẩn duy nhất**; mỗi quyết định chuẩn hóa được tách thành Owner Decision ở §7)

---

## 1. Bối cảnh

Người dùng phản ánh "các giao diện quản lý không được ổn". Tài liệu này rà soát **logic đang chạy** ở toàn bộ các trang **danh sách/quản lý dữ liệu** (bảng + bộ lọc + CRUD), **loại trừ nhóm Cài đặt** (`features/settings/**`) theo yêu cầu.

Phạm vi audit (đã xác nhận với owner):

| Nhóm | Route tiêu biểu | Component |
|------|-----------------|-----------|
| Sản phẩm | `/products` | `product-management/pages/ProductsPage.tsx` |
| Danh mục | `/products/categories` | `product-management/pages/CategoriesPage.tsx` |
| Khách hàng / NCC | `/products/customers`, `/suppliers` | `CustomersPage.tsx`, `SuppliersPage.tsx` |
| Tồn kho | `/inventory/stock` | `inventory/pages/StockPage.tsx` |
| Nhập / Xuất / Kiểm kê | `/inventory/inbound`,`/dispatch`,`/audit` | `InboundPage.tsx`, `DispatchPage.tsx`, `AuditPage.tsx` |
| Đơn hàng / Hóa đơn | `/orders/wholesale`, `/retail` | `orders/pages/WholesalePage.tsx`, `ReturnsPage.tsx` |
| Thu chi / Sổ nợ / Sổ cái | `/cashflow/*` | `TransactionsPage.tsx`, `DebtPage.tsx`, `LedgerPage.tsx` |
| Chờ phê duyệt / Lịch sử duyệt | `/approvals/*` | `PendingApprovalsPage.tsx`, `ApprovalHistoryPage.tsx` |

**Ngoài phạm vi:** `settings/**`, POS bán lẻ (`orders/RetailPage.tsx`), Dashboard, Analytics, Custom Builder, AI Chat, Auth.

> Lưu ý: SRS-018→021 đã nâng cấp từng nhóm riêng lẻ. Tài liệu này là audit **cắt ngang (cross-cutting)** — soi mức độ **nhất quán giữa các trang**, không lặp lại nội dung từng SRS trước.

---

## 2. Phương pháp & bằng chứng

- **CodeGraph preflight:** `status` (855 files, 14.3k nodes, index sẵn sàng) + `context` cho cụm "management interface pages".
- **Đọc trực tiếp 7 trang đại diện trên 5 nhóm** (đủ để xác lập pattern, không suy diễn):
  `ProductsPage`, `StockPage`, `WholesalePage`, `TransactionsPage`, `CategoriesPage`, `DebtPage`, `PendingApprovalsPage`.
- **Hạ tầng dùng chung:** `lib/data-table-layout.ts`, `components/shared/ConfirmDialog.tsx`, `lib/api/http.ts`.

Mỗi phát hiện dưới đây có dẫn chứng `file:dòng`.

---

## 3. Phát hiện theo trục bất nhất (cross-cutting)

Ký hiệu mức độ: 🔴 Cao (sai/đánh lừa người dùng hoặc rủi ro dữ liệu) · 🟠 Trung bình (UX/bảo trì) · 🟡 Thấp (đồng bộ hình thức).

### 3.1 🔴 KPI / thẻ thống kê tính sai phạm vi (page-scoped vs full-dataset)

Một số trang tính "tổng" chỉ trên **các dòng của trang hiện tại** (tối đa 20 bản ghi), nhưng nhãn hiển thị như thể là tổng toàn bộ → **số liệu sai lệch và đổi theo từng trang**.

| Trang | Hành vi | Bằng chứng |
|-------|---------|-----------|
| TransactionsPage | `totalIncome/totalExpense/balance` reduce trên `transactions` (1 trang) | `TransactionsPage.tsx:147-149` |
| DebtPage | `totalReceivable/totalPayable/overdueCount` reduce trên `debtsQuery.debts` (1 trang); `overdueCount` so `new Date()` ở client | `DebtPage.tsx:89-91` |
| StockPage | KPI lấy từ **API summary riêng** (đúng — toàn tập) | `StockPage.tsx:129-166` |

→ Cùng là "thẻ tổng quan" nhưng StockPage đúng phạm vi, Transactions/Debt sai phạm vi. Tooltip `Info` ở Transactions (`:367-372`) chỉ "thú nhận" chứ không sửa bản chất.

### 3.2 🔴 Xóa hàng loạt — 3 hành vi khác nhau, có rủi ro xóa dở dang

| Trang | Cơ chế | Khi 1 item lỗi | Bằng chứng |
|-------|--------|----------------|-----------|
| ProductsPage | 1 endpoint bulk (`postProductsBulkDelete`) | Server xử lý nguyên khối, trả `deletedCount` | `ProductsPage.tsx:301-311` |
| TransactionsPage | Vòng lặp client, `await` từng id | **`break` ngay item đầu lỗi** → phần còn lại bị bỏ im lặng | `TransactionsPage.tsx:216-231` |
| CategoriesPage | Vòng lặp client, `await` từng id | **`continue`** (toast lỗi mỗi item), đếm `ok` | `CategoriesPage.tsx:279-297` |

→ Cùng thao tác "xóa N mục" cho 3 kết quả khác nhau; biến thể `break` gây mất nhất quán dữ liệu so với phản hồi UI.

### 3.3 🟠 Hai mô hình phân trang song song

| Mô hình | Trang | Bằng chứng |
|---------|-------|-----------|
| Infinite scroll (`useInfiniteQuery` + `IntersectionObserver`) | ProductsPage, StockPage | `ProductsPage.tsx:178-226`, `StockPage.tsx:106-155` |
| Phân trang cổ điển (Trước/Sau + `page/totalPages`) | WholesalePage, TransactionsPage, DebtPage, PendingApprovalsPage | `WholesalePage.tsx:123-148`, `TransactionsPage.tsx:409-437`, `DebtPage.tsx:257-284`, `PendingApprovalsPage.tsx:331-357` |
| Không phân trang (tải hết cây) | CategoriesPage — footer "Đang hiển thị X / X" (tautology) | `CategoriesPage.tsx:365-367` |

Kèm theo: `PAGE_SIZE` không thống nhất — **20** ở hầu hết trang nhưng **50** ở PendingApprovals (`PendingApprovalsPage.tsx:33`).

### 3.4 🟠 Trạng thái Loading/Error hiển thị 4 kiểu khác nhau

| Kiểu | Trang | Hệ quả |
|------|-------|--------|
| Thay cả vùng bảng, **toolbar vẫn hiển thị** | ProductsPage, StockPage, CategoriesPage | Người dùng giữ được bộ lọc khi tải/lỗi (tốt) |
| Toolbar **nằm trong nhánh success** → ẩn cả thanh lọc khi loading/error | WholesalePage | Mất bộ lọc mỗi lần tải/lỗi (kém) — `WholesalePage.tsx:80-110` |
| Overlay "Đang tải…" phủ lên bảng | TransactionsPage, DebtPage | `TransactionsPage.tsx:393-398`, `DebtPage.tsx:243-247` |
| Banner lỗi inline phía trên bảng + nút "Thử lại" | PendingApprovalsPage | `PendingApprovalsPage.tsx:275-282` |

### 3.5 🟠 Hộp xác nhận hành động — 3 pattern

| Pattern | Trang | Bằng chứng |
|---------|-------|-----------|
| `ConfirmDialog` (modal dùng chung) | ProductsPage, CategoriesPage | `ProductsPage.tsx:509-523` |
| `toast.warning` + nút action (không modal) | TransactionsPage | `TransactionsPage.tsx:203-214` |
| `Dialog` tự dựng, style riêng | PendingApprovals (approve/reject), StockPage (bulk) | `PendingApprovalsPage.tsx:360-450`, `StockPage.tsx:522-558` |

→ Cùng mức "hành động không hoàn tác" nhưng độ nghiêm túc của xác nhận khác nhau tùy trang.

### 3.6 🟠 Xử lý lỗi → toast bị nhân bản, không có helper chung

`errToast` được **định nghĩa lại gần như giống hệt** ở nhiều file; logic bóc envelope `ApiRequestError` (status 400/403/409 + `details`) cũng lặp:

- `ProductsPage.tsx:57-93` (`errToast` + `toastProductMutationEnvelope`)
- `CategoriesPage.tsx:39-79` (`errToast` + `toastCategoryMutationEnvelope` — gần trùng)
- `PendingApprovalsPage.tsx:38-44` (`errToast` riêng)
- TransactionsPage / DebtPage / StockPage: lặp khối `if (e instanceof ApiRequestError) toast.error(...) else ...` **inline** nhiều lần (`TransactionsPage.tsx:281-287,344-350`, `DebtPage.tsx:164-169,183-188`, `StockPage.tsx:270-277,293-300,337-344`).

→ Không có `@/lib/api/toastApiError` dùng chung → mỗi trang một kiểu thông điệp, dễ phân kỳ.

### 3.7 🟠 Hành động "giả" được ship ra UI

Nút bấm được nhưng không làm gì (chỉ toast), gây kỳ vọng sai:

| Hành động | Trang | Bằng chứng |
|-----------|-------|-----------|
| "Xuất Excel" | TransactionsPage, DebtPage | `TransactionsPage.tsx:181-183`, `DebtPage.tsx:121-123` |
| "Chỉnh sửa hàng loạt" | ProductsPage | `ProductsPage.tsx:364-366` |

### 3.8 🟡 Class layout: copy tay thay vì import hằng số chung

`lib/data-table-layout.ts` (`:1-16`) yêu cầu import `DATA_TABLE_SHELL_CLASS` / `DATA_TABLE_SCROLL_CLASS`, nhưng:

- **Dùng đúng (import):** StockPage (`:33,452,460`), WholesalePage (`:9,80,112`).
- **Copy chuỗi class y hệt inline:** ProductsPage (`:466,479`), TransactionsPage (`:392-393`), DebtPage (`:241-242`), CategoriesPage (`:340,351`), PendingApprovals (`:284-285`).

→ Khi chuẩn đổi, các bản copy sẽ lệch. Footer phân trang cũng có ≥2 biến thể class (`px-3 py-2 ... min-h-11` vs `px-4 py-2 text-xs font-bold`).

### 3.9 🟡 Ngôn ngữ thị giác phân kỳ giữa các trang

Hai "phong cách" tồn tại song song trong cùng khu quản lý:

- **Tiết chế (chuẩn mới):** `font-semibold tracking-tight`, slate dịu — ProductsPage/StockPage/Categories (`ProductsPage.tsx:432`).
- **Đậm/khoa trương:** `font-black uppercase tracking-widest`, `rounded-2xl`, viền/màu nặng — DebtPage (`:197,319-321`), PendingApprovals (`:199,207-213`).

Phụ: `DebtPage` StatCard có `colorMap` mà `blue` và `indigo` map ra **cùng** một bộ slate (`DebtPage.tsx:307-311`) → prop màu gần như vô nghĩa (dead code). Mỗi trang lại **tự định nghĩa `StatCard` riêng** (Transactions `:462-484`, Debt `:306-326`) thay vì 1 component chung.

### 3.10 🟠 Status badge — 5 cách render cho cùng một việc

Dự án có **duy nhất 1 StatusBadge dùng chung** tại `inventory/components/StatusBadge.tsx`, nhưng phần lớn bảng **không dùng nó** mà tự định nghĩa riêng:

| Cách | Trang áp dụng | Kiểu code |
|------|--------------|-----------|
| `StatusBadge` chung (inventory) — **đúng** | Phiếu nhập/xuất/kiểm kê/tồn kho | Config map + dot indicator |
| `StatusBadge` cục bộ trong `OrderTable` | Đơn hàng, Hóa đơn, Phê duyệt | `switch-case` inline |
| `StatusBadge` cục bộ trong `TransactionTable` | Giao dịch thu chi | `if/else` inline |
| `StatusBadge` cục bộ trong `DebtTable` | Sổ nợ | `if/else` inline, style khác hẳn |
| Badge **inline** không có component | Sản phẩm, Danh mục, Khách hàng, NCC | Ternary trực tiếp trong JSX |

Hệ quả — **3 lớp lỗi cụ thể có bằng chứng:**

**Lỗi A — Cùng status value, nhãn tiếng Việt khác nhau:**

| Status | OrderTable | TransactionTable | Bằng chứng |
|--------|-----------|-----------------|-----------|
| `Pending` | "Chờ duyệt" | "Chờ xử lý" | `OrderTable.tsx:52`, `TransactionTable.tsx:39-42` |

**Lỗi B — Cùng trạng thái "tích cực", token màu lệch:**

| Trang | Token | Bằng chứng |
|-------|-------|-----------|
| Mọi nơi | `bg-emerald-100 text-emerald-700 border border-emerald-200` | — |
| DebtTable "Đã tất toán" | `bg-green-50 text-green-700 border-none` | `DebtTable.tsx:32` |

**Lỗi C — Nhãn Active/Inactive không thống nhất:**

| Bảng | Nhãn Inactive | Bằng chứng |
|------|--------------|-----------|
| ProductTable | "Ngừng" | `ProductTable.tsx:90` |
| CategoryTable | "Ngưng" ← khác dấu | `CategoryTable.tsx:93` |
| CustomerTable | "Ngừng" | `CustomerTable.tsx:159` |

→ Mỗi bảng copy-paste một bản badge riêng; khi cần thay đổi nhãn/màu phải sửa ≥5 nơi cùng lúc.

### 3.11 🟡 Quy ước kỹ thuật vặt nhưng tích tụ

| Vấn đề | Bằng chứng |
|--------|-----------|
| Export module không nhất quán: hầu hết `export function`, riêng PendingApprovals `export default` | `PendingApprovalsPage.tsx:50` |
| Query key không có quy ước chung: `["product-management","products",...]` vs `["inventory","v1",...]` (có `v1`) vs hằng số export ở cashflow | `ProductsPage.tsx:163-176`, `StockPage.tsx:108`, `TransactionsPage.tsx:14-23` |
| Reset filter side-effect khác nhau: `useEffect` thường vs `setTimeout(...,0)` | `ProductsPage.tsx:133-135` vs `TransactionsPage.tsx:95-98`, `DebtPage.tsx:80-86` |
| Toolbar: component `*Toolbar` dùng chung vs **dựng inline** | PendingApprovals tự dựng filter bar inline `:215-273` |
| Hỗ trợ tùy biến cột (`useTableColumnOrder`) chỉ có ở vài bảng (Products/Stock/Categories), bảng khác (Order/Transaction/Debt) cố định cột | `ProductsPage.tsx:103-110` vs WholesalePage/Transactions/Debt không có |
| `select-all` lấy theo `flattenedCategories` trong khi bảng nhận `categories` (cây) → khả năng lệch số đếm chọn | `CategoriesPage.tsx:233-235,352-353` |
| Đọc `error.body.message` không optional-chaining (rủi ro nếu `body` undefined) | `CategoriesPage.tsx:347` |

---

## 4. Tổng hợp ma trận ưu tiên

| # | Phát hiện | Mức | Loại | Ảnh hưởng |
|---|-----------|-----|------|-----------|
| 3.1 | KPI sai phạm vi (page-scoped) | 🔴 | Đúng/sai số liệu | Người dùng đọc sai tổng thu/chi/công nợ |
| 3.2 | Bulk delete `break` giữa chừng | 🔴 | Toàn vẹn dữ liệu | Xóa dở dang, UI báo không khớp thực tế |
| 3.3 | 2–3 mô hình phân trang + PAGE_SIZE lệch | 🟠 | UX/nhất quán | Trải nghiệm cuộn/lật trang khác nhau |
| 3.4 | 4 kiểu loading/error | 🟠 | UX | WholesalePage mất bộ lọc khi tải |
| 3.5 | 3 pattern xác nhận | 🟠 | UX/an toàn | Mức cảnh báo không đều |
| 3.6 | Toast lỗi nhân bản | 🟠 | Bảo trì | Thông điệp lỗi phân kỳ |
| 3.7 | Nút "giả" (Excel, sửa hàng loạt) | 🟠 | UX | Kỳ vọng sai |
| 3.8 | Copy class layout | 🟡 | Bảo trì | Lệch chuẩn khi refactor |
| 3.9 | Ngôn ngữ thị giác phân kỳ | 🟡 | Thẩm mỹ | Thiếu đồng bộ thương hiệu |
| 3.10 | Status badge — 5 cách render, lỗi nhãn/màu | 🟠 | Bảo trì/UX | Nhãn tiếng Việt lệch, màu lệch, sửa phải đụng ≥5 file |
| 3.11 | Quy ước vặt | 🟡 | Bảo trì | Tích tụ nợ kỹ thuật |

---

## 5. Khuyến nghị (yêu cầu chức năng đề xuất)

> Đây là **khuyến nghị**; chốt cuối phụ thuộc Owner Decision §7.

- **R1 (từ 3.1):** Mọi thẻ KPI/tổng phải lấy từ **endpoint summary toàn tập** (mẫu StockPage), hoặc đổi nhãn rõ ràng thành "trên trang hiện tại". Không để nhãn "Tổng" cho số page-scoped.
- **R2 (từ 3.2):** Thống nhất xóa hàng loạt qua **1 endpoint bulk** trả `{deletedCount, failed[]}`; nếu buộc lặp client thì **không `break`** — gom kết quả và báo "đã xóa X, thất bại Y".
- **R3 (từ 3.3) — phân trang theo từng loại dữ liệu (khuyến nghị):**
  - *Infinite scroll* cho danh mục lớn, duyệt-khám phá: **Sản phẩm, Tồn kho** (đang đúng) → mở rộng cho Khách hàng/NCC.
  - *Phân trang cổ điển* cho dữ liệu kế toán/đối soát cần "trang X/Y" cố định: **Thu chi, Sổ nợ, Sổ cái, Hóa đơn, Phê duyệt**.
  - *Danh mục cây* (Categories): giữ tải-hết nhưng sửa footer cho đúng nghĩa (ví dụ "N danh mục").
  - Chuẩn hóa `PAGE_SIZE = 20` (hoặc nêu lý do nếu khác).
- **R4 (từ 3.4):** Khung trang chuẩn: **toolbar luôn hiển thị**; loading/error chỉ thay **vùng bảng**; dùng overlay cho refetch nền. Bỏ kiểu ẩn toolbar (WholesalePage).
- **R5 (từ 3.5):** Mọi hành động không hoàn tác dùng **`ConfirmDialog` chung**; dialog đặc thù (chọn vị trí nhập, lý do từ chối) kế thừa cùng khung style.
- **R6 (từ 3.6):** Tạo `@/lib/api/toastApiError(e, fallbackMsg)` + `toastMutationEnvelope` dùng chung; gỡ bản sao ở từng trang.
- **R7 (từ 3.7):** Ẩn/disable hành động chưa có backend, hoặc gắn nhãn "Sắp có"; không ship nút chỉ-toast.
- **R8 (từ 3.8/3.9/3.11):** Import hằng số từ `data-table-layout.ts` (cấm copy chuỗi); 1 `StatCard`/`PageHeader`/`ListPageShell` dùng chung; thống nhất `export function`, quy ước query-key, và reset filter bằng `useEffect` thường.
- **R9 (từ 3.10):** Tạo `@/components/shared/StatusBadge.tsx` duy nhất — gộp tất cả status của dự án vào 1 config map (receipt, dispatch, audit, inventory, order, transaction, debt, product, partner). Xoá 4 bản `StatusBadge` cục bộ và 3 bản inline. Chuẩn hoá: emerald (không phải green), có `border border-*-200`, `font-semibold`; nhãn `Pending` → "Chờ xử lý" (trung tính); `Inactive` → "Ngừng" (thống nhất dấu).

---

## 6. Tiêu chí nghiệm thu của audit (Definition of Done cho tài liệu này)

1. Mọi phát hiện §3 có ít nhất 1 dẫn chứng `file:dòng` đã kiểm chứng — ✅.
2. Ma trận ưu tiên §4 phân loại Cao/Trung/Thấp — ✅.
3. Khuyến nghị §5 truy vết 1–1 về phát hiện §3 — ✅.
4. Các điểm cần owner chốt được tách rõ ở §7 (không tự quyết trong audit).

---

## 7. Owner Decisions cần chốt (trước khi sang Tech Spec)

| OD   | Câu hỏi                                                                                                       | Mặc định đề xuất             |
| ---- | ------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| OD-1 | KPI sai phạm vi: chuyển sang summary toàn tập **hay** chỉ đổi nhãn?                                           | Summary toàn tập (R1)        |
| OD-2 | Phân trang: theo từng-loại (R3) hay ép 1 chuẩn duy nhất?                                                      | Theo từng-loại (R3)          |
| OD-3 | Phạm vi triển khai sửa: làm **một đợt chuẩn hóa** hay **cuốn chiếu từng nhóm** theo các SRS nâng cấp đang có? | Cuốn chiếu, ưu tiên 🔴 trước |
| OD-4 | Có chấp nhận tạo lớp component/helper dùng chung mới (`ListPageShell`, `StatCard`, `toastApiError`) không?    | Có                           |
| OD-5 | Nút "giả" (Excel/sửa hàng loạt): ẩn ngay hay giữ và gắn "Sắp có"?                                             | Ẩn cho tới khi có BE         |
| OD-6 | Nhãn `Pending`: thống nhất 1 nhãn ("Chờ xử lý") hay giữ ngữ cảnh ("Chờ duyệt" kho/duyệt, "Chờ xử lý" tài chính)? | Tách 2 nhãn theo ngữ cảnh |

---

## 8. Truy vết (Traceability)

- **Trang đã đọc:** `ProductsPage.tsx`, `CategoriesPage.tsx`, `StockPage.tsx`, `WholesalePage.tsx`, `TransactionsPage.tsx`, `DebtPage.tsx`, `PendingApprovalsPage.tsx`.
- **Hạ tầng:** `lib/data-table-layout.ts`, `lib/api/http.ts`, `components/shared/ConfirmDialog.tsx`.
- **Liên quan:** SRS-007 (product table unification), SRS-008 (order/invoice unification), SRS-018→021 (redesign từng nhóm). Audit này bổ trợ ở góc **nhất quán cắt ngang**.
- **Chưa đọc đầy đủ (đề nghị soi tiếp khi sang Tech Spec):** `CustomersPage`, `SuppliersPage`, `InboundPage`, `DispatchPage`, `AuditPage`, `ReturnsPage`, `LedgerPage`, `ApprovalHistoryPage` — kỳ vọng lặp lại các pattern §3.

---

**CodeGraph:** status + context + files (index sẵn sàng, 855 files; không có pending changes).
**Superpowers:** brainstorming (khám phá yêu cầu + tách owner decisions).
**Next stage:** chốt §7 → `TECH_SPEC_WRITER` lập kế hoạch chuẩn hóa theo ưu tiên 🔴→🟠→🟡.
