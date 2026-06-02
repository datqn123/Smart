# SRS - Custom Builder Program Overview

> File: `docs/dev/common/001_custom-builder-program-overview.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: Tai lieu tong quan dieu huong cho chuoi SRS custom entity/workflow/connector/inventory/AI.

---

## 1. Muc Tieu

Mini ERP can chuyen tu cach fix cung tung bang sang nen tang ERP low-code co kiem soat:

- Owner/Admin tao duoc bang nghiep vu moi bang metadata.
- User tao/xem/sua record theo form/table dong.
- Owner/Admin thiet ke workflow va logic connector giua cac man hinh.
- Tac dong ton kho chi duoc thuc thi qua executor an toan.
- AI dong hanh nhu copilot, khong tu commit hanh dong rui ro.

Tinh nang nay khong cho user tao SQL table vat ly, viet SQL, viet JavaScript/Groovy/SpEL, tao endpoint dong, hay tu update truc tiep `Inventory.quantity`.

---

## 2. Source / Gap Evidence

| ID | Van de | Evidence | Xu ly trong SRS |
| :--- | :--- | :--- | :--- |
| GAP-1 | Hien moi cau hinh cot cho bang co dinh, chua co bang user tao | `TableColumnCatalog` hard-code table key | Phase 1 metadata engine |
| GAP-2 | Ton kho la loi nghiep vu, khong cho user tu cong/tru bang script | `Inventory.quantity`, `InventoryLogs`, receipt/dispatch baseline | Phase 4 Inventory Effect Executor |
| GAP-3 | AI hien co SQL read-only + Harness, chua co custom entity schema | `ai_python` SQL branch/schema explorer/Harness | Phase 6/7 AI-safe metadata + scoped tools |
| GAP-4 | Frontend route/menu static | `frontend/mini-erp/src/App.tsx`, `Sidebar.tsx` | Dynamic custom workspace routes |

---

## 3. Out Of Scope Cho MVP

- User tu tao SQL table vat ly.
- User tu viet SQL/JavaScript/Groovy/SpEL.
- User tao endpoint backend dong.
- BPMN phuc tap co nhanh song song, timer, SLA.
- Field-level RBAC qua chi tiet.
- Attachment/file upload.
- Custom report builder nhieu join phuc tap.
- Reservation/hold stock neu chua co bang reservation rieng.
- AI tu publish definition, submit/approve record, hoac chay inventory effect.

---

## 4. Module Bi Anh Huong

| Layer | Anh huong | Ghi chu |
| :--- | :---: | :--- |
| Frontend Mini-ERP | Co | Builder UI, workspace custom, dynamic table/form |
| Backend Spring | Co | API, validation, RBAC, transaction, inventory executor |
| Database | Co | Metadata, JSONB records, workflow, connector, effect events |
| AI Python | Co o phase sau | Builder copilot, query custom data, draft branch, Harness tool |
| External service | Khong | Khong can provider moi |

---

## 5. Tai Lieu Tach Phase

| Thu tu | File | Noi dung |
| :--- | :--- | :--- |
| 001 | `001_custom-builder-program-overview.md` | Tong quan, nguyen tac, phase, open questions chung |
| 002 | `002_custom-builder-phase1-entity-record-foundation.md` | Entity/field/view/record, JSONB, polymorphic reference, scale |
| 003 | `003_custom-builder-phase2-workflow.md` | Workflow state/transition, pending state, audit |
| 004 | `004_custom-builder-phase3-logic-connector.md` | Logic connector/formula builder, line items, cycle detection |
| 005 | `005_custom-builder-phase4-inventory-effect.md` | Inventory effect executor, dry-run, idempotency, lock ordering |
| 006 | `006_custom-builder-phase5-ai-builder-copilot.md` | AI copilot trong builder, diff review, prompt-injection guardrail |
| 007 | `007_custom-builder-phase6-ai-custom-query.md` | AI query custom metadata/data, read-only |
| 008 | `008_custom-builder-phase7-ai-custom-draft.md` | AI tao draft custom record, Harness tool, user review |

---

## 6. Cross-layer Principles

| Nguyen tac | Bat buoc |
| :--- | :--- |
| Metadata-driven | User tao definition/field/view/workflow/connector metadata, khong tao code/table SQL dong |
| Backend authoritative | Backend validate/publish/execute; UI chi la trai nghiem builder |
| No free script | Khong cho SQL/JS/Groovy/SpEL/custom API call tu user |
| Polymorphic reference | Reference dung `{refType, refEntityKey, refId, labelSnapshot}` |
| Versioned definition | Record giu `definition_version`, khong tu dong ap definition moi vao record cu |
| Inventory safety | Moi cong/tru/chuyen kho qua Inventory Effect Executor |
| UI guardrail | Disable/confirm/dry-run cho hanh dong rui ro |
| AI safety | AI chi suggest/draft; Harness/Spring la lop chan thuc thi |

---

## 7. Shared UI Guardrails

Frontend guardrail khong thay backend validation, nhung bat buoc de giam thao tac nham va double submit.

| Hanh dong | UI bat buoc |
| :--- | :--- |
| Save/publish definition | Disable nut va tab lien quan khi mutation pending |
| Save record | Disable submit trong luc pending |
| Execute transition | Disable tat ca transition buttons cua record |
| Inventory effect | Khong optimistic update; refetch sau backend response |
| Delete/archive entity | Confirm + disable sau click dau tien |
| Bulk action | Disable bulk toolbar khi dang xu ly |
| AI apply suggestion | Chi enable sau diff review va backend validation pass |

Button rui ro phai disabled khi:

- Request/mutation pending.
- Form chua pass client validation.
- Backend dry-run chua pass.
- User khong co quyen.
- Record dang o state khong cho sua/chuyen.
- Definition dang publish hoac version conflict.
- AI suggestion chua duoc user chap nhan.

Confirm theo rui ro:

| Rui ro | Vi du | Yeu cau |
| :--- | :--- | :--- |
| Thap | Luu draft field/view | Khong can confirm |
| Trung binh | Publish definition moi | Confirm + summary thay doi |
| Cao | Transition cong/tru kho | Dry-run + confirm san pham/kho/so luong |
| Rat cao | Archive entity, bulk transition | Confirm bat buoc + Owner/Admin |

---

## 8. Common API Errors

| Status | Message |
| :--- | :--- |
| 400 | `Du lieu khong hop le. Vui long kiem tra lai cac truong duoc danh dau.` |
| 401 | `Phien dang nhap da het han. Vui long dang nhap lai.` |
| 403 | `Ban khong co quyen thuc hien thao tac nay.` |
| 409 | `Khong the thuc hien vi du lieu hien tai khong con phu hop.` |
| 422 | `Cau hinh chua hop le. Vui long kiem tra lai truong du lieu, workflow, connector va effect.` |

---

## 9. Roadmap

### Phase 1 - Custom Entity / Record Foundation

User tao duoc bang custom, field, layout, record, list/detail; chua workflow, chua ton kho.

### Phase 2 - Workflow

Them state machine, transition, audit timeline, pending guardrail.

### Phase 3 - Logic Connector

User keo-tha logic trigger/source/operation/target. Connector luu JSON rule co cau truc, co dry-run va cycle detection.

### Phase 4 - Inventory Effect

Connector/effect tac dong kho compile thanh template executor; dam bao transaction, lock, rollback, idempotency.

### Phase 5 - AI Builder Copilot

AI ho tro user tao cau hinh bang, workflow, connector/effect va canh bao rui ro; khong tu publish.

### Phase 6 - AI Custom Query

AI hoi du lieu custom theo metadata AI-safe va quyen user; read-only.

### Phase 7 - AI Custom Draft

AI tao draft custom record qua Spring/Harness scoped tool; user tu review va submit/approve tren UI.

---

## 10. Shared Business Rules

| ID | Rule |
| :--- | :--- |
| BR-COM-01 | Khong cho ton kho am |
| BR-COM-02 | Khong duoc bo qua workflow transition |
| BR-COM-03 | Khong duoc doi field type lam hong record cu |
| BR-COM-04 | Khong duoc xoa/archive target dang duoc custom reference dung neu chua impact check |
| BR-COM-05 | Khong duoc ha thap quyen kho bang permission dong trong builder |
| BR-COM-06 | Khong optimistic update voi transition/effect rui ro |
| BR-COM-07 | AI suggestion phai qua user confirmation va backend validation |
| BR-COM-08 | Metadata label/description la untrusted content khi expose sang AI |
| BR-COM-09 | Dry-run khong duoc mutate database |

---

## 11. Non-functional / Risk Controls

| Nhom | Yeu cau | Cach verify |
| :--- | :--- | :--- |
| Security | Khong cho user chay SQL/script tuy y | Code review + tests |
| Security | RBAC backend cho moi endpoint | Security tests |
| Data integrity | Reference JSONB co index/impact check | Integration tests |
| Data integrity | Transition + effect atomic | Transaction tests |
| Reliability | Lock ordering thong nhat voi nghiep vu kho | Concurrency tests |
| Idempotency | Khong apply effect hai lan | Unique key + tests |
| UI safety | Button rui ro disabled khi pending/invalid/no permission | Component/manual QA |
| Performance | List record phan trang, index ro, co scale plan | Query plan/load test |
| Audit | Timeline definition/record/workflow/connector/effect | DB inspection |
| AI safety | AI copilot chi suggest/draft | Graph/tool tests |

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| User cau hinh sai lam lech ton kho | Rat cao | Template effect, dry-run, transaction, idempotency |
| JSONB query cham khi du lieu lon | Cao | Pagination, search_text, field index, partition/materialized view phase scale |
| Connector tao vong lap/cascade | Rat cao | Cycle detection, operation allowlist, scope sync nho |
| Formula builder thanh script engine tra hinh | Rat cao | Structured JSON rule, cam JS/SQL/API tu do |
| Prompt injection qua metadata | Cao | Sanitize, structured JSON, untrusted boundary, Harness/Spring guardrails |
| UI double submit | Cao | Disable pending + backend idempotency |

---

## 12. Feature Flags

- `CUSTOM_BUILDER_ENABLED=0` mac dinh.
- `CUSTOM_LOGIC_CONNECTORS_ENABLED=0` mac dinh.
- `CUSTOM_INVENTORY_EFFECTS_ENABLED=0` mac dinh.
- `CUSTOM_BUILDER_AI_COPILOT_ENABLED=0` mac dinh.
- Chi bat inventory effects sau khi Phase 1/2/3 da on dinh.
- Chi bat AI Copilot sau khi backend validation va dry-run da on dinh.

---

## 13. Open Questions Chung

| ID | Cau hoi | De xuat mac dinh |
| :--- | :--- | :--- |
| OQ-COM-01 | Ten menu dung gi? | `Trinh thiet ke du lieu` |
| OQ-COM-02 | Role nao co `can_manage_custom_builder`? | Owner/Admin true, Staff false |
| OQ-COM-03 | Co lam reservation trong MVP khong? | Chua dua vao MVP |
| OQ-COM-04 | Reference integrity dung polymorphic table hay FK table rieng? | MVP polymorphic + service impact check |
| OQ-COM-05 | `line_items` luu JSONB hay table phu? | MVP JSONB gioi han, phase scale tach table |
| OQ-COM-06 | Co can permission rieng cho high-risk inventory effect? | Can nhac `can_execute_inventory_effect` |
| OQ-COM-07 | Connector cross-entity sync hay async? | MVP sync chi khi transaction an toan; async qua outbox phase scale |

---

## 14. PO Sign-off Checklist

- [ ] Chot ten menu.
- [ ] Chot RBAC entity-level.
- [ ] Chot chua lam reservation trong MVP.
- [ ] Chot luu record bang JSONB + version definition.
- [ ] Chot reference integrity polymorphic.
- [ ] Chot operation allowlist cho connector/formula builder.
- [ ] Chot `line_items` MVP luu JSONB hay tach bang phu.
- [ ] Chot inventory effect bat buoc qua executor.
- [ ] Chot strict lock ordering voi nghiep vu kho loi.
- [ ] Chot idempotency chi block status `Applied`, cho retry sau `Failed`.
- [ ] Chot AI metadata sanitize/untrusted boundary.
- [ ] Chot UI guardrails pending/dry-run/confirm/diff review.
- [ ] Chot scale/index thresholds.
- [ ] Chot AI chi suggest/draft-only.

---

## 15. Files Can Doc Khi Tech Spec

- `backend/smart-erp/src/main/java/com/example/smart_erp/inventory/*`
- `backend/smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql`
- `backend/smart-erp/src/main/java/com/example/smart_erp/settings/tablecolumns/*`
- `frontend/mini-erp/src/App.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
- `ai_python/app/graph/main_graph.py`
- `ai_python/app/harness/runtime.py`

SRS handoff state: `READY_FOR_PHASED_TECH_SPEC`.
