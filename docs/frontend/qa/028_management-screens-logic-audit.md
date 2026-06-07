# QA SPEC 029 — Chuẩn hoá logic giao diện quản lý (SRS-023 / Tech Spec 027)

**Ngày:** 2026-06-07
**Tác giả:** QA_SPEC_WRITER (auto)
**Tài liệu tham chiếu:**
- SRS: `docs/frontend/srs/023_management-screens-logic-audit.md`
- Tech Spec: `docs/frontend/tech_lead/027_management-screens-logic-audit.md`
**Trạng thái:** QA_READY_FOR_CODING

---

## 1. Phạm vi kiểm thử

Bao gồm **tất cả slice Phase 1 + Phase 2** từ Tech Spec 027. Không bao gồm Phase 3 (deferred).

Môi trường: React app chạy local (dev server), mock API hoặc API thật. Mọi test có thể thực hiện bằng kiểm tra thủ công trong browser hoặc unit test React Testing Library.

---

## 2. Ma trận P0/P1

### P0 — Chặn release (bug sai số liệu hoặc mất dữ liệu)

| ID | Test case | File/Slice | Kết quả mong đợi |
|----|-----------|-----------|-----------------|
| P0-1 | Xoá nhiều giao dịch, giả lập item thứ 2 lỗi (API mock 500) | TransactionsPage / Slice 1b | item 1 xoá thành công, item 3+ tiếp tục được thử; toast tổng kết "Đã xóa X, thất bại Y" |
| P0-2 | Xoá nhiều giao dịch, tất cả thành công | TransactionsPage / Slice 1b | toast "Đã xóa N giao dịch", selectedIds cleared |
| P0-3 | Thẻ "Thu (trang này)" hiển thị trang 1 vs trang 2 | TransactionsPage / Slice 1b | Giá trị thay đổi theo trang (nhãn đã cảnh báo người dùng không đây là tổng toàn bộ) |
| P0-4 | Nhãn thẻ không còn là "Tổng thu" / "Tổng chi" | TransactionsPage / Slice 1b | Nhãn phải chứa "(trang này)" |
| P0-5 | Nhãn Debt không còn là "Nợ phải thu" / "Nợ phải trả" | DebtPage / Slice 1c | Nhãn phải chứa "(trang này)" |

### P1 — Nghiêm trọng (UX sai, nhất quán, regression)

| ID | Test case | File/Slice | Kết quả mong đợi |
|----|-----------|-----------|-----------------|
| P1-1 | Đặt filter "Trạng thái: Completed" → bấm refresh → trang lỗi API | WholesalePage / Slice 1a | Toolbar (search, filter, sort) **vẫn hiển thị**; chỉ vùng bảng báo lỗi |
| P1-2 | WholesalePage đang tải lần đầu | WholesalePage / Slice 1a | Toolbar hiển thị; vùng bảng hiện "Đang tải…" |
| P1-3 | Badge "Hoàn thành" trong OrderTable | OrderTable / Slice 2a | emerald-100 + emerald-700 + border + dot |
| P1-4 | Badge "Đã hủy" trong OrderTable | OrderTable / Slice 2a | rose-100 + rose-600 + border + dot |
| P1-5 | Badge "Chờ xử lý" trong TransactionTable (Pending) | TransactionTable / Slice 2a | Nhãn = "Chờ xử lý" (context="finance") |
| P1-6 | Badge "Chờ duyệt" trong phiếu kho (inventory StatusBadge) | StatusBadge / Slice 2a | Nhãn = "Chờ duyệt" (context="warehouse" hoặc không truyền context) |
| P1-7 | Badge "Đã tất toán" trong DebtTable | DebtTable / Slice 2a | emerald-100 + emerald-700 + **có border** (không phải green, không phải border-none) |
| P1-8 | Badge "Còn nợ" trong DebtTable (status Active) | DebtTable / Slice 2a | Hiển thị "Còn nợ" amber, có border |
| P1-9 | Badge "Ngừng" trong CategoryTable | CategoryTable / Slice 2a | "Ngừng" không phải "Ngưng" |
| P1-10 | Badge "Ngừng" trong ProductTable | ProductTable / Slice 2a | "Ngừng" |
| P1-11 | Badge "Ngừng" trong CustomerTable | CustomerTable / Slice 2a | "Ngừng" |
| P1-12 | Nút "Xuất Excel" không còn trên UI | TransactionsPage / Slice 2c | Không tồn tại nút/option export |
| P1-13 | Nút "Xuất Excel" không còn trên UI | DebtPage / Slice 2c | Không tồn tại nút/option export |
| P1-14 | Nút "Chỉnh sửa hàng loạt" không còn trên UI | ProductsPage / Slice 2c | Không tồn tại nút/option bulk edit |
| P1-15 | PendingApprovals tải trang đầu — số dòng | PendingApprovalsPage / Slice 2d | Tối đa 20 dòng (không phải 50) |
| P1-16 | `toastApiError` hiện đúng message từ API | lib/toastApiError / Slice 2b | Mock ApiRequestError với body.message → toast hiện body.message |
| P1-17 | `toastApiError` với error không phải ApiRequestError | lib/toastApiError / Slice 2b | Hiện e.message hoặc fallback string |

---

## 3. Test cases chi tiết — P0

### P0-1: Bulk delete giao dịch — item giữa lỗi

**Setup:**
1. Có ít nhất 3 giao dịch trong danh sách.
2. Mock endpoint `DELETE /api/v1/cash-transactions/{id}` để item thứ 2 trả 500.

**Bước:**
1. Chọn cả 3 giao dịch (checkbox).
2. Bấm xoá → xác nhận.

**Mong đợi:**
- Item 1: xoá thành công.
- Item 2: toast lỗi xuất hiện (message từ API).
- Item 3: **vẫn được thử xoá** (không dừng ở item 2).
- Toast success cuối: "Đã xóa 2 giao dịch, thất bại 1" (hoặc tương đương).
- `selectedIds` chỉ còn item 2 (vì 1 và 3 đã xoá thành công).

**Kiểm tra tự động (nếu có test):**
```ts
// vi: 'it' tương đương jest/vitest
it('continues deleting remaining items when one fails', async () => {
  // mock: id=1 → OK, id=2 → throw, id=3 → OK
  // expect: deleteCashTransaction called 3 times
  // expect: toast.success called with "Đã xóa 2 giao dịch, thất bại 1"
})
```

---

### P0-4/P0-5: Nhãn KPI không còn là "Tổng"

**Setup:** Mở TransactionsPage hoặc DebtPage.

**Bước:** Kiểm tra text label của 3 thẻ thống kê.

**Mong đợi:** Không có nhãn chứa chữ "Tổng" độc lập — phải có "(trang này)" đi kèm.

**Fail condition:** Nhãn là "Tổng thu", "Tổng chi", "Số dư", "Nợ phải thu", "Nợ phải trả" (không cảnh báo phạm vi).

---

## 4. Test cases chi tiết — P1

### P1-1/P1-2: WholesalePage toolbar luôn hiển thị

**Bước:**
1. Mở `/orders/wholesale`.
2. Trong khi đang tải (isListPending=true): xác nhận thanh tìm kiếm + filter hiển thị.
3. Giả lập API lỗi (offline hoặc mock 500): xác nhận thanh filter vẫn hiển thị.
4. Nhập text tìm kiếm khi đang lỗi → text field nhận input (không bị disabled bởi lỗi).

**Fail condition:** Thanh filter biến mất khi loading hoặc khi error.

---

### P1-3 → P1-11: StatusBadge consistency

**Test matrix — kiểm tra trực quan trong browser:**

| Status | Context | Trang kiểm tra | Màu nền | Text | Border | Dot | Nhãn |
|--------|---------|---------------|---------|------|--------|-----|------|
| Completed | order | WholesalePage | emerald-100 | emerald-700 | emerald-200 | emerald-500 | "Hoàn thành" |
| Pending | order | WholesalePage | amber-100 | amber-700 | amber-200 | amber-400 | "Chờ xử lý" |
| Cancelled | order | WholesalePage | rose-100 | rose-600 | rose-200 | rose-400 | "Đã hủy" |
| Pending | finance | TransactionsPage | amber-100 | amber-700 | amber-200 | amber-400 | "Chờ xử lý" |
| Completed | finance | TransactionsPage | emerald-100 | emerald-700 | emerald-200 | emerald-500 | "Hoàn thành" |
| Cleared | — | DebtPage | emerald-100 | emerald-700 | **emerald-200** | emerald-500 | "Đã tất toán" |
| Active (Inactive) | — | ProductsPage | emerald-100 (slate-100) | emerald-700 (slate-500) | có border | có dot | "Hoạt động" / "Ngừng" |
| Inactive | — | CategoryTable | slate-100 | slate-500 | có border | slate-400 | **"Ngừng"** (không phải "Ngưng") |
| Pending | warehouse | InboundPage | amber-100 | amber-700 | amber-200 | amber-400 | "Chờ duyệt" |
| Approved | warehouse | InboundPage | emerald-100 | emerald-700 | emerald-200 | emerald-500 | "Đã duyệt" |

**Fail condition:** Bất kỳ ô nào trong bảng trên không khớp.

---

### P1-16/P1-17: toastApiError — unit test

```ts
import { toastApiError, toastMutationEnvelope } from "@/lib/api/toastApiError"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"

vi.mock("sonner")

describe("toastApiError", () => {
  it("shows body.message when ApiRequestError has body", () => {
    const err = new ApiRequestError(400, { message: "SKU đã tồn tại" }, "Bad Request")
    toastApiError(err)
    expect(toast.error).toHaveBeenCalledWith("SKU đã tồn tại")
  })

  it("shows e.message when body.message is absent", () => {
    const err = new ApiRequestError(500, {}, "Internal Server Error")
    toastApiError(err)
    expect(toast.error).toHaveBeenCalledWith("Internal Server Error")
  })

  it("shows fallback for non-ApiRequestError", () => {
    toastApiError(new Error("network timeout"), "Không kết nối được")
    expect(toast.error).toHaveBeenCalledWith("network timeout")
  })

  it("shows custom fallback for unknown error", () => {
    toastApiError("some string error", "Lỗi không xác định")
    expect(toast.error).toHaveBeenCalledWith("Lỗi không xác định")
  })
})

describe("toastMutationEnvelope", () => {
  it("is silent for 400 with details", () => {
    const err = new ApiRequestError(400, { message: "Lỗi", details: { name: "Tên bắt buộc" } }, "Bad Request")
    toastMutationEnvelope(err)
    expect(toast.error).not.toHaveBeenCalled()
  })

  it("shows message for 409", () => {
    const err = new ApiRequestError(409, { message: "Mã SKU đã tồn tại" }, "Conflict")
    toastMutationEnvelope(err)
    expect(toast.error).toHaveBeenCalledWith("Mã SKU đã tồn tại")
  })

  it("shows message for 403", () => {
    const err = new ApiRequestError(403, { message: "Không có quyền" }, "Forbidden")
    toastMutationEnvelope(err)
    expect(toast.error).toHaveBeenCalledWith("Không có quyền")
  })
})
```

---

## 5. Regression — các tính năng không được phá vỡ

| Tính năng | Trang | Kiểm tra |
|-----------|-------|---------|
| StatusBadge inventory vẫn hiển thị đúng | InboundPage, DispatchPage, AuditPage, StockPage | Mở trang → badge render đúng nhãn/màu như trước |
| Phân trang WholesalePage vẫn hoạt động | WholesalePage | Bấm Trước/Sau → đổi trang đúng |
| Filter trạng thái TransactionsPage vẫn lọc | TransactionsPage | Chọn "Hoàn thành" → chỉ hiện Completed |
| Xoá 1 giao dịch vẫn hoạt động | TransactionsPage | Xoá 1 item → toast success, item biến khỏi danh sách |
| Form tạo/sửa sản phẩm vẫn mở | ProductsPage | Bấm "Thêm sản phẩm" → form hiện |
| Phê duyệt / Từ chối phiếu nhập | PendingApprovalsPage | Bấm ✓ → dialog chọn vị trí → xác nhận → toast success |
| Nhãn "Chờ duyệt" trong phiếu kho giữ nguyên | InboundPage (StatusBadge Pending) | Không bị đổi thành "Chờ xử lý" |

---

## 6. Failure mode coverage

| Scenario | Hành vi mong đợi |
|----------|-----------------|
| API trả 500 khi xoá giao dịch | `toastApiError` hiện message lỗi; item không bị xoá khỏi danh sách client |
| API trả 409 khi tạo sản phẩm trùng SKU | `toastMutationEnvelope` hiện message server; form không đóng |
| API trả 400 + details (field error) | `toastMutationEnvelope` im lặng; form tự setError lên field |
| WholesalePage API 404 | Banner lỗi trong vùng bảng; toolbar vẫn dùng được |
| StatusBadge nhận status value không trong config | Hiện nhãn = status value (string thô) + slate styling (không crash) |
| DebtTable nhận status = "Active" | Hiển thị "Còn nợ" amber (đã map qua "Active_debt") |

---

## 7. Danh sách file cần review sau coding

```
src/components/shared/StatusBadge.tsx           (mới)
src/lib/api/toastApiError.ts                    (mới)
src/features/orders/pages/WholesalePage.tsx
src/features/cashflow/pages/TransactionsPage.tsx
src/features/cashflow/pages/DebtPage.tsx
src/features/orders/components/OrderTable.tsx
src/features/cashflow/components/TransactionTable.tsx
src/features/cashflow/components/DebtTable.tsx
src/features/product-management/components/ProductTable.tsx
src/features/product-management/components/CategoryTable.tsx
src/features/product-management/components/CustomerTable.tsx
src/features/product-management/components/SupplierTable.tsx
src/features/inventory/components/StatusBadge.tsx  (re-export)
src/features/product-management/pages/ProductsPage.tsx
src/features/product-management/pages/CategoriesPage.tsx
src/features/approvals/pages/PendingApprovalsPage.tsx
src/features/approvals/pages/ApprovalHistoryPage.tsx
src/features/orders/hooks/useSalesOrdersListQuery.ts
```

---

## 8. Bộ test tối thiểu trước khi merge

- [ ] `lib/api/toastApiError.test.ts` — 6 unit tests (P1-16/17 ở §4).
- [ ] Kiểm tra thủ công P0-1 (bulk delete with failure) và P0-4 (nhãn KPI).
- [ ] Kiểm tra thủ công P1-1 (WholesalePage toolbar khi lỗi).
- [ ] Kiểm tra trực quan bảng P1-3→P1-11 (StatusBadge matrix) trên browser.
- [ ] Regression smoke: mở InboundPage → badge đúng; WholesalePage → phân trang đúng; PendingApprovals → approve/reject đúng.
- [ ] TypeScript `tsc --noEmit` không có lỗi mới.

---

**Readiness:** `QA_READY_FOR_CODING`

**CodeGraph:** status + explore (StatusBadge, errToast, ConfirmDialog, DATA_TABLE_SHELL_CLASS).
**Superpowers:** TDD (test cases + expected failures defined before implementation).
