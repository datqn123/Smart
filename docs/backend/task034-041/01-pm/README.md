# PM handoff — Task034–Task041 (quản lý sản phẩm)

> **WORKFLOW_RULE:** [`../../../AGENTS/WORKFLOW_RULE.md`](../../../AGENTS/WORKFLOW_RULE.md) §0.2 — **SRS đã Approved** → **PM** khởi tạo chuỗi `PM → Tech Lead → Developer → …` (G-BA coi **đạt** cho scope SRS này).

## Nguồn sự thật

| Artifact | Path |
| :--- | :--- |
| SRS (Approved) | [`../../srs/SRS_Task034-041_products-management.md`](../../srs/SRS_Task034-041_products-management.md) |
| API (FE contract) | `frontend/docs/api/API_Task034_…` đến `API_Task039_…`, `API_Task041_…` |
| Flyway | `V1` (products / productunits / …), **`V15__productimages_one_primary_unique.sql`**, seed liên quan (vd. `V16__…` nếu team dùng) |
| Cloudinary vận hành | [`../../../smart-erp/docs/CLOUDINARY_SETUP.md`](../../../smart-erp/docs/CLOUDINARY_SETUP.md) |

## Trạng thái triển khai BE (`smart-erp`) — *đối chiếu repo tại thời điểm tạo handoff*

| Mục SRS / API | Trạng thái | Ghi chú |
| :--- | :--- | :--- |
| **Task039** `POST /api/v1/products/{id}/images` (JSON + multipart) | **Đã có** | `ProductsController` + `ProductImageService` + `CloudinaryMediaService` + `ProductImageJdbcRepository`; RBAC `can_manage_products` |
| **OQ-4** partial unique primary | **Đã có** | Flyway **V15** |
| **Task034** `GET /api/v1/products` (list + pagination) | **Chưa** | Không có handler ngoài nhánh ảnh trên cùng `@RequestMapping` |
| **Task035** `POST /api/v1/products` | **Chưa** | |
| **Task036** `GET /api/v1/products/{id}` | **Chưa** | |
| **Task037** `PATCH /api/v1/products/{id}` | **Chưa** | |
| **Task038** `DELETE /api/v1/products/{id}` | **Chưa** | Owner-only + kiểm tra tồn/chứng từ (SRS §9) |
| **Task041** `POST /api/v1/products/bulk-delete` | **Chưa** | All-or-nothing (**OQ-3(a)**) |

> **Tech Lead:** rà package `catalog` — mở rộng `ProductsController` vs tách `ProductQueryController` / service layer; ADR ngắn (NFR 5 mục) trước G-TL.

## Chuỗi tác vụ đề xuất (PM — thứ tự phụ thuộc)

Mỗi nhóm: **Unit (contract)** → **Feature (mã)** → **E2E / smoke** (theo `PM_AGENT_INSTRUCTIONS.md` §2). ID gợi ý để ghi ticket.

| ID gợi ý | Phụ thuộc | Nội dung | Verify tối thiểu |
| :--- | :--- | :--- | :--- |
| **T041-PM-1** | — | **Task035** create: transaction `products` + base `product_units` + `product_price_history`; validation SKU, category (**OQ-2**), envelope `201` | `mvn -q -pl smart-erp test` + controller test |
| **T041-PM-2** | T041-PM-1 | **Task036** get by id: units + images + giá current (**BR-2**, `CURRENT_DATE`) | WebMvcTest / slice |
| **T041-PM-3** | T041-PM-2 | **Task034** list: filter, sort whitelist, `total`, read-model stock + price base unit | Test phân trang + SQL explain (TL) |
| **T041-PM-4** | T041-PM-2 | **Task037** PATCH: `FOR UPDATE`, meta + cặp giá → INSERT history | Concurrency / conflict 409 SKU |
| **T041-PM-5** | T041-PM-2 | **Task038** + **Task041**: DELETE Owner-only (**OQ-6**); bulk all-or-nothing (**OQ-3**); checks `stock_receipt_details`, `order_details`, inventory sum | Integration hoặc manual script SRS §11 |
| **T041-PM-6** | — | **Task039** regression: JSON + multipart tắt/bật Cloudinary khớp SRS §4.3 + §8.6 | `ProductsControllerWebMvcTest`, `CloudinaryMediaServiceTest` |

**Song song được:** T041-PM-6 với T041-PM-1 nếu Dev khác file ảnh vs CRUD (tránh conflict nhánh).

## Gate tiếp theo (chuỗi chuẩn `WORKFLOW_RULE`)

1. **G-PM (Owner):** merge/commit artifact PM này (và ticket liên kết) lên **`develop`** trước khi Dev mở nhánh feature — [`PM_AGENT_INSTRUCTIONS.md`](../../../AGENTS/PM_AGENT_INSTRUCTIONS.md) §4.
2. **G-TL:** ADR + rào chắn package / pagination / Owner policy reuse (`StockReceiptAccessPolicy` pattern từ categories).
3. **G-DEV:** TDD; `./mvnw.cmd verify` xanh; JaCoCo cổng dự án; checklist handoff **API_BRIDGE** trong [`DEVELOPER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/DEVELOPER_AGENT_INSTRUCTIONS.md) §5.1.
4. **G-BRIDGE (bắt buộc — REST mini-erp):** sau G-DEV, **mỗi Path** một phiên `Mode=verify` (khuyến nghị) — xem **§3.1** dưới.
5. **Tester → Codebase Analyst → Doc Sync.**

---

## §3.1 `WORKFLOW_RULE` — Handoff API_BRIDGE (sau `mvn verify` xanh)

Dán từng khối vào chat / ticket (thay `Task` và `Path`).

### Task034 — list

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task034 | Path=GET /api/v1/products

Vai trò: API_BRIDGE. Tuân @backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md.
API_BRIDGE | Task=Task034 | Path=GET /api/v1/products | Mode=verify

Đọc: @frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md → @frontend/docs/api/API_Task034_products_get_list.md → grep Path trong @backend/smart-erp/src/main/java → grep trong @frontend/mini-erp/src.

Output: @frontend/docs/api/bridge/BRIDGE_Task034_products_get_list.md
```

### Task035 — create

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task035 | Path=POST /api/v1/products
API_BRIDGE | Task=Task035 | Path=POST /api/v1/products | Mode=verify
```

### Task036 — detail

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task036 | Path=GET /api/v1/products/{id}
API_BRIDGE | Task=Task036 | Path=GET /api/v1/products/{id} | Mode=verify
```

### Task037 — patch

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task037 | Path=PATCH /api/v1/products/{id}
API_BRIDGE | Task=Task037 | Path=PATCH /api/v1/products/{id} | Mode=verify
```

### Task038 — delete

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task038 | Path=DELETE /api/v1/products/{id}
API_BRIDGE | Task=Task038 | Path=DELETE /api/v1/products/{id} | Mode=verify
```

### Task039 — images *(đã có BE — chạy verify sớm để bám FE)*

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task039 | Path=POST /api/v1/products/{id}/images
API_BRIDGE | Task=Task039 | Path=POST /api/v1/products/{id}/images | Mode=verify
```

### Task041 — bulk delete

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task041 | Path=POST /api/v1/products/bulk-delete
API_BRIDGE | Task=Task041 | Path=POST /api/v1/products/bulk-delete | Mode=verify
```

**UI context (wire-fe sau):** tra [`../../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md) — `/products/list`, `ProductsPage`.

---

## Definition of Done (PM — gắn ticket sprint)

- [ ] SRS §11 AC đạt trên môi trường dev/staging.
- [ ] Mọi Path trên có `BRIDGE_Task*.md` sau phiên verify (hoặc lô PM chốt).
- [ ] `API_Task039_*.md` cập nhật multipart + Cloudinary nếu còn drift (SRS §12 GAP).

**Ngày tạo handoff:** 27/04/2026
