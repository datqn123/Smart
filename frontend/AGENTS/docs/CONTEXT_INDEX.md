# CONTEXT INDEX — Đọc tối thiểu theo loại task

> **Vị trí**: `AGENTS/docs/CONTEXT_INDEX.md` — bộ nhớ ngoài cửa sổ cho Agent / dev (tiết kiệm token).  
> **Tài liệu sản phẩm** (UC, DB, SRS, hợp đồng API): vẫn nằm dưới [`docs/`](../docs/README.md).

**Tham chiếu triết lý**: write / select (context engineering) — đồng bộ với kế hoạch context/token của dự án.

---

## 1. Bảng ánh xạ: loại task → tài liệu tối thiểu

| Loại task | Đọc bắt buộc (thứ tự gợi ý) | Chỉ đọc thêm khi… |
| :---------- | :---------------------------- | :---------------- |
| **Sửa UI / feature trong app** | [`mini-erp/src/features/FEATURES_UI_INDEX.md`](../../mini-erp/src/features/FEATURES_UI_INDEX.md) **trước** (route → file), rồi [`RULES.md`](../../RULES.md), [`RULES_BUG_FIX.md`](../../RULES_BUG_FIX.md), **chỉ** file `pages`/`components` đã index | Layout hệ thống lạ → [`FUNCTIONAL_SUMMARY.md`](../../FUNCTIONAL_SUMMARY.md) hoặc `mini-erp` README nếu có |
| **Task DEV theo `TASKS/TaskXXX.md`** | File `TASKS/TaskXXX.md`, RULES + RULES_BUG_FIX | Task trỏ tới SRS/PRD → mở đúng path trong task |
| **Thiết kế / sửa tài liệu API** | [`../API_AGENT_INSTRUCTIONS.md`](../API_AGENT_INSTRUCTIONS.md), [`../../docs/api/API_PROJECT_DESIGN.md`](../../docs/api/API_PROJECT_DESIGN.md), `docs/api/API_TaskXXX_*.md` liên quan | Trường DB/constraint → **chỉ** mục bảng liên quan trong [`../../docs/UC/schema.sql`](../../docs/UC/schema.sql) hoặc `Database_Specification` (không đọc full nếu không cần) |
| **Agent Planner — brief mới** | [`../PLANNER_AGENT_INSTRUCTIONS.md`](../PLANNER_AGENT_INSTRUCTIONS.md), [`templates/planner/PLANNER_BRIEF_TEMPLATE.md`](templates/planner/PLANNER_BRIEF_TEMPLATE.md) | Map UC → [`../../docs/api/API_PROJECT_DESIGN.md`](../../docs/api/API_PROJECT_DESIGN.md) §5 |
| **Agent BA (không qua Planner)** | [`../BA_AGENT_INSTRUCTIONS.md`](../BA_AGENT_INSTRUCTIONS.md), [`../WORKFLOW_RULE.md`](../WORKFLOW_RULE.md) | Trụ tương ứng + template trong [`templates/ba/`](templates/ba/) |
| **Agent BA từ Planner Approved** | `AGENTS/docs/planner/PLANNER_BRIEF_TaskXXX_*.md` + cột “DEV/UI” tùy trụ | Như trên |
| **Backend Spring Boot** | [`BACKEND_SPRING_BOOT.md`](BACKEND_SPRING_BOOT.md) + `docs/api/` + `docs/UC/schema.sql` + [`backend/AGENTS/WORKFLOW_RULE.md`](../../../backend/AGENTS/WORKFLOW_RULE.md) + [`backend/AGENTS/AGENT_REGISTRY.md`](../../../backend/AGENTS/AGENT_REGISTRY.md) | Hướng dẫn từng vai: `backend/AGENTS/*_AGENT_INSTRUCTIONS.md` |
| **API_BRIDGE (nối FE ↔ BE)** | [`FE_API_CONNECTION_GUIDE.md`](FE_API_CONNECTION_GUIDE.md) **trước**, rồi [`backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md`](../../../backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md) + **một** `docs/api/API_TaskXXX_*.md` | Chỉ `grep`/`read` thêm file trong `mini-erp/src` hoặc BE theo agent; output `docs/api/bridge/BRIDGE_*.md` |
| **PM / PM_RUN** | [`../PM_AGENT_INSTRUCTIONS.md`](../PM_AGENT_INSTRUCTIONS.md), `docs/srs/SRS_TaskXXX_*.md` đã Approved | — |
| **Điều phối agent (meta)** | [`../AGENT_REGISTRY.md`](../AGENT_REGISTRY.md) | Chi tiết → [`../FLOW_GUIDE.md`](../FLOW_GUIDE.md) |
| **Activity diagram (Mermaid)** | [`../ACTIVITY_DIAGRAM_AGENT_INSTRUCTIONS.md`](../ACTIVITY_DIAGRAM_AGENT_INSTRUCTIONS.md) | Có `@file` / code → chỉ đọc hàm & nhánh liên quan; lệnh Cursor `/activity-diagram` |
| **Bug investigation (RCA, không code)** | [`backend/AGENTS/BUG_INVESTIGATOR_AGENT_INSTRUCTIONS.md`](../../../backend/AGENTS/BUG_INVESTIGATOR_AGENT_INSTRUCTIONS.md) **§4.1** — output `backend/docs/bugs/Bug_TaskNNN.md` | Trần: ≤5 `read` × ≤120 dòng, ≤3 `grep` có path hẹp, cấm explore/Glob root; index: [`FEATURES_UI_INDEX.md`](../../mini-erp/src/features/FEATURES_UI_INDEX.md) hoặc CONTEXT (một); Context7 ≤1 câu; sau Owner chốt → [`DEVELOPER_AGENT_INSTRUCTIONS.md`](../../../backend/AGENTS/DEVELOPER_AGENT_INSTRUCTIONS.md) |

---

## 2. Thói quen tiết kiệm token (áp dụng mỗi phiên)

1. **Một phiên — một mục tiêu**; milestone xong → thread mới + handoff (mục 6 trong [`templates/planner/PLANNER_BRIEF_TEMPLATE.md`](templates/planner/PLANNER_BRIEF_TEMPLATE.md) hoặc [`templates/tasks/TASK_SESSION_HANDOFF.md`](templates/tasks/TASK_SESSION_HANDOFF.md)).
2. **Ưu tiên `@file` / `@folder` / symbol**; log chỉ phần lỗi liên quan.
3. **Tắt MCP / skill không dùng** cho task hiện tại.
4. **Plan trước khi implement** (thay đổi lớn).
5. **Không đọc full** `Database_Specification` / `schema.sql` nếu chỉ cần vài cột — grep hoặc offset/limit.
6. **IMAD / latent agents (thực hành Cursor)**: tránh nhiều vòng subagent khi không cần; kết luận hoặc hướng sửa trước, chi tiết sau — chi tiết và ranh giới train-model xem [`.cursor/rules/project-common.mdc`](../../../.cursor/rules/project-common.mdc) mục *Tiết kiệm token — ánh xạ thực hành*.

---

## 3. Liên kết nhanh

| Tài liệu | Vai trò |
| :------- | :------ |
| [API_PROJECT_DESIGN.md](../../docs/api/API_PROJECT_DESIGN.md) | Catalog endpoint `/api/v1` (hợp đồng FE + BE) |
| [API_BRIDGE_PROMPTS_Task029-033_categories.md](./API_BRIDGE_PROMPTS_Task029-033_categories.md) | Bộ prompt API_BRIDGE (verify + wire-fe) Task029–033 danh mục — copy theo phiên |
| [API_BRIDGE_PROMPTS_Task034-041_products.md](./API_BRIDGE_PROMPTS_Task034-041_products.md) | Bộ prompt Task034–039, 041 sản phẩm |
| [API_BRIDGE_PROMPTS_Task042-047_suppliers.md](./API_BRIDGE_PROMPTS_Task042-047_suppliers.md) | Bộ prompt Task042–047 nhà cung cấp — PM handoff [`backend/docs/task042-047/01-pm/README.md`](../../../backend/docs/task042-047/01-pm/README.md) |
| [API_BRIDGE_PROMPTS_Task048-053_customers.md](./API_BRIDGE_PROMPTS_Task048-053_customers.md) | Bộ prompt Task048–053 khách hàng — SRS [`backend/docs/srs/SRS_Task048-053_customers-management.md`](../../../backend/docs/srs/SRS_Task048-053_customers-management.md) |
| [API_BRIDGE_PROMPTS_Task054-060_sales-orders-pos-retail-checkout.md](./API_BRIDGE_PROMPTS_Task054-060_sales-orders-pos-retail-checkout.md) | Bộ prompt Task054–060 đơn bán / POS / checkout bán lẻ — SRS [`backend/docs/srs/SRS_Task054-060_sales-orders-pos-and-retail-checkout.md`](../../../backend/docs/srs/SRS_Task054-060_sales-orders-pos-and-retail-checkout.md) |
| [API_BRIDGE_PROMPTS_Task090_uc9-retail-checkout-stock-deduction.md](./API_BRIDGE_PROMPTS_Task090_uc9-retail-checkout-stock-deduction.md) | Bộ prompt Task090 — trừ tồn khi POS checkout + hoàn kho khi hủy Retail (bridge qua Task060 + Task058) — SRS [`backend/docs/srs/SRS_Task090_uc9-retail-checkout-stock-deduction.md`](../../../backend/docs/srs/SRS_Task090_uc9-retail-checkout-stock-deduction.md) |
| [API_BRIDGE_PROMPTS_Task064-068_cash-transactions-api.md](./API_BRIDGE_PROMPTS_Task064-068_cash-transactions-api.md) | Bộ prompt Task064–068 thu chi — SRS [`backend/docs/srs/SRS_Task064-068_cash-transactions-api.md`](../../../backend/docs/srs/SRS_Task064-068_cash-transactions-api.md) |
| [WORKFLOW_RULE.md](../WORKFLOW_RULE.md) | Gate BA → PM → … |
| [PLANNER_AGENT_INSTRUCTIONS.md](../PLANNER_AGENT_INSTRUCTIONS.md) | Intake + Q&A + brief |
| [arXiv:2604.24881](https://arxiv.org/abs/2604.24881) (*Latent Agents* / IMAD) + [latent_agents (code)](https://github.com/johnsk95/latent_agents) | Nghiên cứu / pipeline SFT+RL để nội suy debate trong một LLM, giảm token **suy luận** ở tầm model — **chỉ khi** bạn tự host hoặc fine-tune; không thay rule đọc tối thiểu ở trên |

---

## 4. Ghi chú cho Agent tự động

Khi bắt đầu task, in một dòng: *“Theo `AGENTS/docs/CONTEXT_INDEX.md`, loại task = …; chỉ đọc: …”* rồi tuân thủ; chỉ mở rộng khi thiếu dữ liệu.
