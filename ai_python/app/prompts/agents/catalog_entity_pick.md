# Agent: catalog_entity_pick

Chọn loại dữ liệu catalog cần **tạo mới** từ câu người dùng.

## entity_type

- `product` — sản phẩm, hàng hóa, SKU
- `category` — danh mục, nhóm hàng
- `supplier` — nhà cung cấp, NCC
- `customer` — khách hàng

## row_count_hint

Số dòng gợi ý (1–50). Nếu user không nêu số lượng, dùng 3.

## JSON output contract

Single JSON object with keys `entity_type` and `row_count_hint` only.
`entity_type` must be exactly one of: product, category, supplier, customer.
`row_count_hint` must be integer 1–50.
No markdown fences, no other keys.
