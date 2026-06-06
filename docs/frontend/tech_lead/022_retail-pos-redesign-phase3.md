# Tech Spec 022 - Retail POS Redesign Phase 3

## Source

- SRS: `docs/frontend/srs/017_retail-pos-redesign.md`
- Scope: Phase 3 / P1 only
- Status: READY_FOR_CODING

## Goal

Complete the POS product browser:

- Add category tabs using the existing categories API.
- Migrate POS product loading from a single query to paged infinite loading.

## Phase Boundary

In scope:

- `POSProductSelector.tsx`
- `posProductsApi.ts`
- Existing `getCategoryList({ format: "flat", status: "Active" })`

Out of scope:

- Backend endpoint changes.
- Cart/payment changes.
- Product card redesign beyond states needed for pagination/category UX.
- Location filter.

## Implementation Slices

### Slice 1 - POS Search API Page Param

- Add `page?: number` to `SearchPosProductsParams`.
- Send `page` to `/api/v1/pos/products` when positive.
- Keep current `limit` clamp.
- Keep response shape compatible with existing `{ items }`.

### Slice 2 - Category Tabs

- Fetch active categories through `getCategoryList({ format: "flat", status: "Active" })`.
- Render horizontal tabs: `Tất cả` + active categories.
- Clicking a category sets `selectedCategoryId` and resets loaded products.
- If category load fails, product grid still works with `Tất cả`.

### Slice 3 - Infinite Loading

- Replace `useQuery` product list with `useInfiniteQuery`.
- Query key includes search text, selected category, and page limit.
- `getNextPageParam` continues while the last page has at least `POS_PAGE_LIMIT` rows.
- Flatten and de-dupe products by `productId-unitId` to guard against backend page fallback.
- Add `Tải thêm sản phẩm` button and loading state at the bottom.

## Verification

- `npm run build`
- `npm run lint`
- Route smoke: `/orders/retail` returns 200.
