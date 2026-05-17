# Agent: inventory_entity_pick (legacy)

Đã thay bằng **`inventory_draft_slots.md`** — tách đủ slot (`doc_type`, `quantity`, `product_query`, `supplier_*`, …) cho tra DB.

Node `classify_inventory_doc` gọi `inventory_draft_slots` (LLM), không dùng file này trong runtime.
