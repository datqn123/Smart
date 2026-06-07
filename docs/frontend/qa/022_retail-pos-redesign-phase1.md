# QA Spec 021 - Retail POS Redesign Phase 1

## Source

- SRS: `docs/frontend/srs/017_retail-pos-redesign.md`
- Tech Spec: `docs/frontend/tech_lead/020_retail-pos-redesign-phase1.md`

## Test Matrix

### Barcode Quick Add

- Given the cashier focuses `Quét/Nhập mã`, when they enter a SKU/barcode and press `Enter`, then the frontend calls product search and adds the single matching in-stock product to cart.
- Given search returns no rows, when the cashier presses `Enter`, then the input shows an inline not-found message and the cart is unchanged.
- Given search returns multiple rows, when the cashier presses `Enter`, then the candidate list appears and selecting a row adds only that row.
- Given the page is open, when the cashier presses F2, then the barcode input receives focus.
- Given the matched product has no price or no stock, when it is selected, then the existing validation prevents adding it.

### Customer Selector

- Given POS cart header shows `Khách hàng`, when clicking `Thay đổi`, then the customer dialog opens.
- Given the dialog is open, when typing a search keyword, then customer results refresh from `getCustomerList`.
- Given a customer row is selected, then the cart header updates to that customer's name and the dialog closes.
- Given `Khách lẻ` is selected, then the cart resets to walk-in customer and the dialog closes.
- Given API loading, empty, or error state occurs, then the dialog renders a clear state without breaking the page.

### Cash Calculator

- Given cart has items, when clicking `Tiền mặt`, then a cash panel expands instead of immediately creating checkout.
- Given received amount is lower than payable, then confirm cash checkout is disabled and remaining amount is visible.
- Given received amount equals or exceeds payable, then change is visible and confirm can call checkout with `Paid`.
- Given checkout succeeds, then cart is cleared and cash panel/input reset.
- Given cart is empty, then cash payment actions remain blocked.

### Regression

- `Thẻ/Chuyển khoản` still creates checkout with `Unpaid`.
- Voucher preview payable amount is respected by the cash calculator.
- Product card search and manual add still work.

## Commands

- `npm run build`
