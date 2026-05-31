# PM handoff — Task042–Task047 (quản lý nhà cung cấp)

> **WORKFLOW_RULE:** [`../../../AGENTS/WORKFLOW_RULE.md`](../../../AGENTS/WORKFLOW_RULE.md) §0.2 — **SRS đã Approved** → **PM** khởi tạo chuỗi `PM → Tech Lead → Developer → …` (G-BA coi **đạt** cho scope SRS này).

## Nguồn sự thật

| Artifact | Path |
| :--- | :--- |
| SRS (Approved) | [`../../srs/SRS_Task042-047_suppliers-management.md`](../../srs/SRS_Task042-047_suppliers-management.md) |
| API (FE contract) | `frontend/docs/api/API_Task042_suppliers_get_list.md` … `API_Task047_suppliers_bulk_delete.md` |
| Flyway | [`../../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`](../../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql) — `suppliers`, `stockreceipts`, **`partnerdebts`** (`supplier_id` **ON DELETE RESTRICT**) |
| RBAC đồng bộ | [`../../srs/SRS_Task034-041_products-management.md`](../../srs/SRS_Task034-041_products-management.md) — `can_manage_products`; **xóa / bulk-delete: chỉ Owner** (**OQ-1(a)** — trùng Task034-041 OQ-6(a)) |
| Prompt API_BRIDGE (copy chi tiết verify/wire-fe) | [`../../../../frontend/AGENTS/docs/API_BRIDGE_PROMPTS_Task042-047_suppliers.md`](../../../../frontend/AGENTS/docs/API_BRIDGE_PROMPTS_Task042-047_suppliers.md) |

## Trạng thái triển khai BE (`smart-erp`) — *cập nhật sau G-DEV*

| Mục SRS / API | Trạng thái | Ghi chú |
| :--- | :--- | :--- |
| **Task042** `GET /api/v1/suppliers` | **Đã có** | `SuppliersController` + `SupplierService` + `SupplierJdbcRepository` — `receiptCount`, sort whitelist §8.2 |
| **Task043** `POST /api/v1/suppliers` | **Đã có** | `SupplierCreateRequest` — `contactPerson` bắt buộc (**OQ-5(a)**); trùng mã → **409** |
| **Task044** `GET /api/v1/suppliers/{id}` | **Đã có** | **`lastReceiptAt`** = `MAX(stockreceipts.created_at)` (**OQ-4(b)**) |
| **Task045** `PATCH /api/v1/suppliers/{id}` | **Đã có** | `FOR UPDATE`; body `JsonNode` partial |
| **Task046** `DELETE /api/v1/suppliers/{id}` | **Đã có** | **Owner-only** (`StockReceiptAccessPolicy`); **409** `HAS_RECEIPTS` / `HAS_PARTNER_DEBTS` |
| **Task047** `POST /api/v1/suppliers/bulk-delete` | **Đã có** | **All-or-nothing**; `ids` trùng → **400**; max **50**; Owner-only |

**Test:** `SuppliersControllerWebMvcTest` (slice). **`mvn verify`** xanh trước bước **API_BRIDGE** `Mode=verify`.

> **Tech Lead:** package `catalog` vs module `suppliers` — ADR ngắn (NFR 5 mục); reuse pattern **Owner-only** / **`can_manage_products`** như `CategoriesController` / products (nếu đã có).

## Chuỗi tác vụ đề xuất (PM — thứ tự phụ thuộc)

Mỗi nhóm: **Unit (contract)** → **Feature (mã)** → **smoke** (theo `PM_AGENT_INSTRUCTIONS.md` §2).

| ID gợi ý | Phụ thuộc | Nội dung | Verify tối thiểu |
| :--- | :--- | :--- | :--- |
| **T047-PM-1** | — | **Task043** POST: validation + transaction INSERT `suppliers`; response `receiptCount: 0`, `lastReceiptAt: null` | `mvn verify` + `WebMvcTest` hoặc slice |
| **T047-PM-2** | T047-PM-1 | **Task044** GET by id: join/count `stockreceipts`; field **`lastReceiptAt`** | Controller test + SQL fixture |
| **T047-PM-3** | T047-PM-2 | **Task042** list: search, status, page/limit, sort whitelist, `receiptCount` aggregate | Test phân trang + invalid `sort` → **400** |
| **T047-PM-4** | T047-PM-2 | **Task045** PATCH: ít nhất một field; **409** trùng `supplierCode`; **200** shape §8.4 | Concurrency optional (TL) |
| **T047-PM-5** | T047-PM-2 | **Task046** DELETE + **Task047** bulk-delete: **`assertOwnerOnly`**; EXISTS `stockreceipts` → `HAS_RECEIPTS`; EXISTS `partnerdebts` → `HAS_PARTNER_DEBTS`; bulk **all-or-nothing**; duplicate **ids** → **400** | Integration hoặc manual SRS §11 |

**Song song được:** T047-PM-3 với T047-PM-4 sau khi có **Task044** (cùng phụ thuộc detail/list không block nhau nếu tách file).

## Gate tiếp theo (chuỗi chuẩn `WORKFLOW_RULE`)

1. **G-PM (Owner):** merge artifact PM (folder này + ticket) lên **`develop`** trước khi Dev mở nhánh feature — [`PM_AGENT_INSTRUCTIONS.md`](../../../AGENTS/PM_AGENT_INSTRUCTIONS.md) §4.
2. **G-TL:** ADR + package + policy DELETE (reuse access policy pattern).
3. **G-DEV:** TDD; `./mvnw.cmd verify` xanh; checklist handoff **API_BRIDGE** trong [`DEVELOPER_AGENT_INSTRUCTIONS.md`](../../../AGENTS/DEVELOPER_AGENT_INSTRUCTIONS.md) §5.1.
4. **G-BRIDGE (bắt buộc — REST mini-erp):** sau G-DEV, **mỗi Path** một phiên `Mode=verify` — [`WORKFLOW_RULE.md`](../../../AGENTS/WORKFLOW_RULE.md) §3.1; chi tiết prompt → file `API_BRIDGE_PROMPTS_Task042-047_suppliers.md`.
5. **Tester → Codebase Analyst → Doc Sync.**

---

## §3.1 `WORKFLOW_RULE` — Handoff API_BRIDGE (sau `mvn verify` xanh)

Dán từng khối vào chat / ticket (thay `Task` và `Path` nếu cần).

### Task042 — list

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task042 | Path=GET /api/v1/suppliers

Vai trò: API_BRIDGE. Tuân @backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md.
API_BRIDGE | Task=Task042 | Path=GET /api/v1/suppliers | Mode=verify

Đọc: @frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md → @frontend/docs/api/API_Task042_suppliers_get_list.md → grep Path trong @backend/smart-erp/src/main/java → grep trong @frontend/mini-erp/src.

Output: @frontend/docs/api/bridge/BRIDGE_Task042_suppliers_get_list.md
```

### Task043 — create

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task043 | Path=POST /api/v1/suppliers
API_BRIDGE | Task=Task043 | Path=POST /api/v1/suppliers | Mode=verify
```

### Task044 — detail

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task044 | Path=GET /api/v1/suppliers/{id}
API_BRIDGE | Task=Task044 | Path=GET /api/v1/suppliers/{id} | Mode=verify
```

### Task045 — patch

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task045 | Path=PATCH /api/v1/suppliers/{id}
API_BRIDGE | Task=Task045 | Path=PATCH /api/v1/suppliers/{id} | Mode=verify
```

### Task046 — delete

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task046 | Path=DELETE /api/v1/suppliers/{id}
API_BRIDGE | Task=Task046 | Path=DELETE /api/v1/suppliers/{id} | Mode=verify
```

### Task047 — bulk delete

```text
HANDOFF_API_BRIDGE | Post=G-DEV | Task=Task047 | Path=POST /api/v1/suppliers/bulk-delete
API_BRIDGE | Task=Task047 | Path=POST /api/v1/suppliers/bulk-delete | Mode=verify
```

**UI context (wire-fe sau verify):** [`../../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md) — `/products/suppliers`, `SuppliersPage`.

---

## Definition of Done (PM — gắn ticket sprint)

- [ ] SRS §11 AC đạt trên dev/staging.
- [ ] Mọi Path Task042–047 có `BRIDGE_Task*.md` sau phiên verify (hoặc lô PM chốt).
- [ ] Không có **500** khi DELETE có `partnerdebts` — kiểm tra app trước DELETE (**BR-2**).

**Ngày tạo handoff:** 27/04/2026
