# QA Spec 023 - Retail POS Redesign Phase 3

## Source

- SRS: `docs/frontend/srs/017_retail-pos-redesign.md`
- Tech Spec: `docs/frontend/tech_lead/022_retail-pos-redesign-phase3.md`

## Test Matrix

### Category Tabs

- Given POS product selector loads, then it shows `Tất cả` and active categories from the category API.
- Given user clicks a category tab, then product search includes `categoryId`.
- Given category API errors, then product selector still renders the `Tất cả` tab and product grid.
- Given user changes search text, then selected category remains applied.

### Infinite Product Loading

- Given the first product page returns `limit` rows, then `Tải thêm sản phẩm` is visible.
- Given user clicks `Tải thêm sản phẩm`, then the next request includes the next page.
- Given backend returns duplicate rows across pages, then UI de-dupes by product/unit.
- Given the last page returns fewer than `limit` rows, then no further load button is shown.

### Regression

- Barcode quick-add still works.
- Manual product card add still works.
- Empty, loading, and API error states still render.

## Commands

- `npm run build`
- `npm run lint`
