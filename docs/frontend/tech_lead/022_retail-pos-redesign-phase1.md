# Tech Spec 020 - Retail POS Redesign Phase 1

## Source

- SRS: `docs/frontend/srs/017_retail-pos-redesign.md`
- Scope: Phase 1 / P0 only
- Status: READY_FOR_CODING

## Goal

Implement the first POS usability slice without backend schema changes:

- Add barcode / quick code input in the product selector.
- Add customer search dialog and connect the `Thay đổi` customer action.
- Add inline cash calculator before confirming cash checkout.

## Phase Boundary

In scope:

- `POSProductSelector.tsx`
- `POSCartPanel.tsx`
- New customer selection dialog component under order components.
- Existing APIs only:
  - `searchPosProducts({ search, limit })`
  - `getCustomerList({ search, page, limit })`
  - Existing retail checkout mutation.

Out of scope for Phase 1:

- Discount editor.
- Order notes.
- Partial payment.
- Receipt modal.
- Mobile tab redesign.
- Product categories and infinite scroll.
- Backend changes.

## Implementation Slices

### Slice 1 - Barcode Quick Add

File: `frontend/mini-erp/src/features/orders/components/POSProductSelector.tsx`

- Add a compact input labeled for `Quét/Nhập mã`.
- Pressing `Enter` searches products by barcode/SKU using `searchPosProducts`.
- If exactly one usable product is found, add it to cart via the existing `handleAddProduct`.
- If no product is found, show inline error and toast-free local feedback.
- If multiple products are returned, show a small candidate list and let the cashier choose.
- Add F2 keyboard shortcut to focus the barcode input.

### Slice 2 - Customer Selector

Files:

- `frontend/mini-erp/src/features/orders/components/POSCartPanel.tsx`
- `frontend/mini-erp/src/features/orders/components/CustomerSearchDialog.tsx`

Requirements:

- `Thay đổi` opens a dialog.
- Dialog searches existing customers through `getCustomerList({ search, page: 1, limit: 8 })`.
- Selecting a customer calls `useOrderStore.setCustomer(id, name)`.
- Dialog includes `Khách lẻ` action to reset customer to anonymous.
- Loading, empty, and API error states are visible.

### Slice 3 - Cash Calculator

File: `frontend/mini-erp/src/features/orders/components/POSCartPanel.tsx`

- Clicking `Tiền mặt` expands an inline cash calculator instead of immediately checking out.
- Show payable amount, `Khách đưa`, and `Tiền thừa`.
- Disable confirm while cart is empty, checkout is pending, or received amount is less than payable.
- Confirming cash calls the existing checkout mutation with `paymentStatus = "Paid"`.
- Existing `Thẻ/Chuyển khoản` remains unchanged and still calls `Unpaid`.

## Risks And Guards

- Barcode search uses the existing product search endpoint, so it must tolerate zero, one, or several returned rows.
- Customer selector must not assume backend returns mapped domain models; it uses `CustomerListItemDto` fields directly.
- Cash calculator must use the voucher preview payable amount when available, otherwise the store final total.
- No changes to order store shape are required.

## Verification

- `npm run build`
- Browser smoke test on `/orders/retail`:
  - F2 focuses barcode input.
  - Customer dialog opens and can select/reset customer.
  - Cash button expands calculator and does not checkout until confirmed.
