# QA Spec 022 - Retail POS Redesign Phase 2

## Source

- SRS: `docs/frontend/srs/017_retail-pos-redesign.md`
- Tech Spec: `docs/frontend/tech_lead/021_retail-pos-redesign-phase2.md`

## Test Matrix

### Discount And Notes

- Given cart has items, when entering a manual discount, then payable amount updates through the existing store final total.
- Given discount input receives non-numeric characters, then only numeric amount is applied.
- Given notes are typed, when checkout is submitted, then `buildRetailCheckoutBody` receives the notes value.
- Given cart is cleared after checkout, then discount and notes reset.

### Partial Payment

- Given cart has items, when clicking `Trả trước`, then partial payment dialog opens.
- Given received amount is lower than payable, then remaining amount is displayed.
- Given confirm is clicked, then checkout mutation uses `paymentStatus = "Partial"`.
- Given cart is empty or checkout is pending, then partial action is blocked.

### Receipt Dialog

- Given checkout succeeds, then receipt dialog opens with returned order code and totals.
- Given cash checkout had received amount, then receipt shows customer cash and change.
- Given partial checkout had received amount, then receipt shows received and remaining amounts.
- Given `Đơn mới` is clicked, then receipt dialog closes and cart remains cleared.

### Mobile Layout

- Given viewport is below `lg`, then only the selected POS tab content is visible.
- Given `Giỏ hàng` tab is selected, then cart panel is visible and product selector is hidden.
- Given desktop viewport, then product selector and cart panel are visible side by side with `7/5` layout.

## Commands

- `npm run build`
- `npm run lint`
