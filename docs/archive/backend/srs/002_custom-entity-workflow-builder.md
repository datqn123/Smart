# SRS Index - Custom Entity / Workflow Builder

> File: `docs/backend/srs/002_custom-entity-workflow-builder.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: SPLIT_TO_PHASED_SRS  
> Ghi chu: Tai lieu lon da duoc tach thanh cac SRS nho trong `docs/dev/common`.

---

## 1. Ly Do Tach File

Ban SRS cu qua dai va gom nhieu scope khac nhau: entity foundation, workflow, connector, inventory effect, AI copilot, AI query va AI draft. De Tech Spec/Coding Agent doc dung scope va tiet kiem context, noi dung da duoc tach theo phase/task.

---

## 2. SRS Moi Theo Phase

| Thu tu | File | Scope |
| :--- | :--- | :--- |
| 001 | `docs/dev/common/001_custom-builder-program-overview.md` | Tong quan chuong trinh, principles, roadmap, open questions chung |
| 002 | `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md` | Entity/field/view/record, JSONB, polymorphic reference, scale |
| 003 | `docs/dev/common/003_custom-builder-phase2-workflow.md` | Workflow state/transition, pending UI, audit |
| 004 | `docs/dev/common/004_custom-builder-phase3-logic-connector.md` | Logic connector/formula builder, line items, cycle detection |
| 005 | `docs/dev/common/005_custom-builder-phase4-inventory-effect.md` | Inventory effect executor, dry-run, idempotency, lock ordering |
| 006 | `docs/dev/common/006_custom-builder-phase5-ai-builder-copilot.md` | AI copilot trong builder, diff review, prompt-injection guardrail |
| 007 | `docs/dev/common/007_custom-builder-phase6-ai-custom-query.md` | AI query custom metadata/data, read-only |
| 008 | `docs/dev/common/008_custom-builder-phase7-ai-custom-draft.md` | AI tao draft custom record, Harness tool, user review |

---

## 3. Cach Dung

- Khi lap Tech Spec tong the, doc `001` truoc roi doc phase lien quan.
- Khi implement theo phase, chi nap SRS cua phase do va cac SRS phu thuoc truoc no.
- Khi lam AI Agentic, bat buoc doc `001`, `006`, `007`, `008` va giu dung rule: LangGraph orchestrates, Harness executes/validates, Spring commits.
- Khi lam inventory, bat buoc doc `004` va `005` cung voi code ton kho hien co.

SRS handoff state: `READY_FOR_PHASED_TECH_SPEC`.
