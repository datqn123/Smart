# Tech Spec 021 - Retail POS Redesign Phase 2

## Source

- SRS: `docs/frontend/srs/017_retail-pos-redesign.md`
- Scope: Phase 2 / P1 only
- Status: READY_FOR_CODING

## Goal

Complete the POS cart workflow after Phase 1:

- Expose manual order discount.
- Add order notes to the POS store and checkout body.
- Add partial payment confirmation dialog.
- Show receipt dialog after successful checkout.
- Add mobile/tablet tab layout between products and cart.

## Phase Boundary

In scope:

- `RetailPage.tsx`
- `POSCartPanel.tsx`
- `useOrderStore.ts`
- New `ReceiptDialog.tsx`
- Existing `buildRetailCheckoutBody` notes field.

Out of scope:

- Product category tabs.
- Product infinite scroll.
- Backend API changes for partial amount persistence.
- Thermal/PDF receipt printing.
- Hold order draft flow.

## Implementation Slices

### Slice 1 - Discount And Notes

- Render manual discount input in cart summary.
- Use existing `setDiscount(amount)` and clamp invalid/negative values to zero.
- Add `notes` and `setNotes` to `useOrderStore`.
- Send `notes` through `buildRetailCheckoutBody`.

### Slice 2 - Partial Payment

- Add `Trả trước` button in the payment area.
- Open a dialog with payable amount, received amount, remaining amount, and confirm action.
- Confirm calls checkout with `paymentStatus = "Partial"`.
- Because backend contract has no `receivedAmount` field yet, keep entered amount as local UI metadata for receipt display only.

### Slice 3 - Receipt Dialog

- Add `ReceiptDialog.tsx`.
- After checkout success, keep the returned `SalesOrderDetailDto` and show receipt dialog.
- Include order code, customer, line summary, manual discount/final amount, payment status, notes, and local cash/partial metadata when present.
- `Đơn mới` closes the dialog; print action is not implemented in this phase.

### Slice 4 - Mobile Layout

- On screens below `lg`, replace simultaneous product/cart layout with two tabs:
  - `Sản phẩm`
  - `Giỏ hàng`
- Show cart item count in the cart tab.
- Desktop remains two columns, adjusted to `7/5` per SRS.

## Risks And Guards

- Checkout clears the persisted cart; receipt must capture response before clearing UI state.
- Store migration must tolerate older persisted state without `notes`.
- Partial amount is not persisted server-side until backend contract is extended.
- Existing unpaid/card checkout should remain unchanged except label clarity.

## Verification

- `npm run build`
- `npm run lint`
- Smoke route `/orders/retail`:
  - Discount and notes render.
  - Partial dialog opens.
  - Mobile tabs render under small viewport.
  - Receipt dialog can render after success path.
