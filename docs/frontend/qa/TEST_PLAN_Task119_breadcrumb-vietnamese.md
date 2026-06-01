# QA Spec / Test Plan — Task119 — Breadcrumb Vietnamese

> **File:** `docs/frontend/qa/TEST_PLAN_Task119_breadcrumb-vietnamese.md`
> **Source SRS:** `docs/frontend/srs/SRS_Task119_breadcrumb-vietnamese.md`
> **Source Tech Spec:** `docs/frontend/tech_lead/TECH_SPEC_Task119_breadcrumb-vietnamese.md`
> **Scope:** Frontend only
> **Agent:** QA Spec Writer
> **Date:** 31/05/2026
> **Readiness:** QA_READY_FOR_CODING

---

## 1. Scope

UI-only change: breadcrumb text in Header.tsx. No backend, DB, or AI involvement.

---

## 2. Test Matrix

| # | Test | Input / Path | Expected breadcrumb | Type | Covered by AC? |
| :- | :--- | :--- | :--- | :--- | :-: |
| T1 | Home clickable link | Navigate `/` | Home icon + "Trang chủ" | Manual visual | Yes |
| T2 | Dashboard | Load `/dashboard` | "Trang chủ / Bảng điều khiển" | Manual visual | Yes |
| T3 | Inventory stock | Load `/inventory/stock` | "Trang chủ / Tồn kho" | Manual visual | Yes |
| T4 | Inbound receipt | Load `/inventory/inbound` | "Trang chủ / Phiếu nhập kho" | Manual visual | Yes |
| T5 | Dispatch | Load `/inventory/dispatch` | "Trang chủ / Xuất kho & Điều phối" | Manual visual | Yes |
| T6 | Product categories | Load `/products/categories` | "Trang chủ / Danh mục sản phẩm" | Manual visual | Yes |
| T7 | Product list | Load `/products/list` | "Trang chủ / Quản lý sản phẩm" | Manual visual | Yes |
| T8 | Suppliers | Load `/products/suppliers` | "Trang chủ / Nhà cung cấp" | Manual visual | Yes |
| T9 | Customers | Load `/products/customers` | "Trang chủ / Khách hàng" | Manual visual | Yes |
| T10 | Retail orders | Load `/orders/retail` | "Trang chủ / Đơn bán lẻ" | Manual visual | Yes |
| T11 | Wholesale orders | Load `/orders/wholesale` | "Trang chủ / Lịch sử hóa đơn" | Manual visual | Yes |
| T12 | Cashflow transactions | Load `/cashflow/transactions` | "Trang chủ / Giao dịch thu chi" | Manual visual | Yes |
| T13 | Debt | Load `/cashflow/debt` | "Trang chủ / Sổ nợ" | Manual visual | Yes |
| T14 | Ledger | Load `/cashflow/ledger` | "Trang chủ / Sổ cái tài chính" | Manual visual | Yes |
| T15 | AI chat | Load `/ai/chat` | "Trang chủ / Trợ lý ảo AI" | Manual visual | Yes |
| T16 | Store info | Load `/settings/store-info` | "Trang chủ / Thông tin cửa hàng" | Manual visual | Yes |
| T17 | Employees | Load `/settings/employees` | "Trang chủ / Quản lý nhân viên" | Manual visual | Yes |
| T18 | Alerts | Load `/settings/alerts` | "Trang chủ / Cấu hình cảnh báo" | Manual visual | Yes |
| T19 | System logs | Load `/settings/system-logs` | "Trang chủ / Nhật ký hệ thống" | Manual visual | Yes |

---

## 3. Edge Cases

| # | Test | Input | Expected | Type |
| :- | :--- | :--- | :--- | :--- |
| E1 | Unknown path segment | Load `/some/new-route` | "Trang chủ / Some-new-route" (fallback capitalize) | Manual |
| E2 | Nested path (3 levels) | Load `/a/b/c` | "Trang chủ / C" (chỉ lấy segment cuối) | Manual |

---

## 4. Regression Check

| # | Check | Why |
| :- | :--- | :--- |
| R1 | Sidebar labels unchanged | Confirm all sidebar labels still in Vietnamese as before |
| R2 | CategoryBreadcrumb on product detail | Confirm CategoryBreadcrumb (data-driven) unaffected |
| R3 | Notifications menu | Confirm notification dropdown unaffected |
| R4 | User dropdown | Confirm user menu unaffected |

---

## 5. Test Data / Mocks

None required — all tested by navigating to existing routes.

---

## 6. Automation Feasibility

Not worth automating for 19 routes + 2 edge cases. Visual manual check takes 5 minutes.

Option to add a unit test for the mapping function if extracted to a pure function:

```ts
describe("PAGE_TITLE_VI", () => {
  it("maps stock to Tồn kho", () => {
    expect(PAGE_TITLE_VI["stock"]).toBe("Tồn kho")
  })
  it("falls back to capitalized segment", () => {
    const slug = "new-page"
    expect(PAGE_TITLE_VI[slug] ?? slug.charAt(0).toUpperCase() + slug.slice(1)).toBe("New-page")
  })
})
```

But this is optional — existing codebase has no such test pattern for Header.

---

## 7. Readiness

**Status:** QA_READY_FOR_CODING

**Reason:** Single file change, no backend/AI, mapping is a 1:1 copy of Sidebar labels already approved by PO.
