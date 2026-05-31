# PM handoff — Task029–Task033 (danh mục sản phẩm)

> **WORKFLOW_RULE:** [`../../../AGENTS/WORKFLOW_RULE.md`](../../../AGENTS/WORKFLOW_RULE.md) — Owner yêu cầu triển khai khi SRS còn **Draft** (ngoại lệ gate §0; PO vẫn cần **Approved** + §13 sign-off trước merge chính thức nếu team siết gate).

## Nguồn sự thật

| Artifact | Path |
| :--- | :--- |
| SRS | [`../../srs/SRS_Task029-033_categories-management.md`](../../srs/SRS_Task029-033_categories-management.md) |
| API | `frontend/docs/api/API_Task029_…` đến `API_Task033_…` |
| Flyway | `smart-erp/.../V14__categories_deleted_at.sql` |

## Trạng thái triển khai BE (`smart-erp`)

- **Controller:** `com.example.smart_erp.catalog.controller.CategoriesController` — `GET/POST/PATCH/DELETE` `/api/v1/categories`.
- **Nghiệp vụ:** `CategoryService` + `CategoryJdbcRepository` (cây / flat / search / soft-delete Owner-only, OQ-2-B null merge).
- **Bảo mật:** `@PreAuthorize("can_manage_products")`; `DELETE` → `StockReceiptAccessPolicy.assertOwnerOnly` + message SRS.

## Gate tiếp theo (chuỗi chuẩn)

1. **PO:** `SRS_Task029-033…` → **Approved** + điền §13.
2. **G-DEV:** `./mvnw.cmd verify` xanh trên nhánh feature.
3. **API_BRIDGE** (theo `WORKFLOW_RULE` §0.3): một phiên / Path hoặc theo lô — `frontend/docs/api/bridge/BRIDGE_Task029_*.md` … Task033.
4. **Tester → Doc Sync** theo registry.

**Ghi chú 26/04/2026:** Đồng bộ `API_Task033_categories_delete.md` với soft-delete + RBAC Owner; chỉnh message lỗi trong `CategoryService` khớp SRS §8.
