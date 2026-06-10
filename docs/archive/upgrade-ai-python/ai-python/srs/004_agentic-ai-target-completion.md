# SRS-004 (upgrade/ai-python): Hoàn thiện Agentic AI theo Target Design (phân pha cho codex)

- **Status**: DRAFT — SRS_WRITER stage
- **Author**: AI workflow (SRS_WRITER)
- **Date**: 2026-06-07
- **Scope tier**: Architecture completion (ai_python) — nối tiếp SRS-002 / SRS-003
- **Nguồn yêu cầu (Input)**:
  - `docs/dev/requires/Design Agentic AI.md` (target design, §1–§17)
  - SRS-002 `docs/upgrade/ai-python/srs/002_harness-orchestrated-agentic-loop.md` (loop nền — DONE)
  - SRS-003 `docs/upgrade/ai-python/srs/003_hitl-resume-flow.md` (HITL resume — DONE)
  - Yêu cầu vận hành tự động của codex (cách chạy + điều kiện tự động tốt) — nhúng ở §3
  - Knowledge assets `docs/ai-python/agentic-ai-supporting-assets/002..016` (K1–K15)
- **CodeGraph**: status (876 files / 14623 nodes) + context("Harness orchestrator...") + explore(harness/*) — đã chạy trước khi viết
- **Superpowers**: brainstorming (làm rõ mục tiêu, options, owner-decision trước khi chốt requirement)

---

## 0. Cách đọc tài liệu này (dành cho codex)

Đây là SRS **phân pha (phase-based)**. Mỗi phase trong §5 là một đơn vị triển khai độc lập có đủ: **Mục tiêu · Phụ thuộc · File/module ưu tiên · Đập-đi-xây-lại vs Giữ-tương-thích · FR · Test data · Expected output · Cách chạy test · Acceptance Criteria**. Codex chạy theo đúng thứ tự phase, giữ trạng thái giữa các phase, và sau mỗi phase chạy test tương ứng trước khi sang phase kế.

> ⚠️ Ràng buộc AGENTS.md: SRS/Tech/QA là **docs-only** — không sửa runtime `ai_python` ở giai đoạn này. Việc sửa code chỉ thực hiện ở `CODING_AGENT` (sau khi Tech Spec + QA Spec duyệt). Khi code, **giữ tách biệt LangGraph / Harness / tools** (AGENTS.md §134).

---

## 1. Mục tiêu & Tầm nhìn

SRS-002 đã biến Harness thành **bộ điều phối vòng lặp** (LLM decide → tool → observe → lặp → final_answer/clarify/HITL); SRS-003 đã đóng vòng **HITL resume**. SRS-004 hoàn thiện **phần còn lại của Target Design** để đạt một agent ERP đạt hiệu suất cao:

1. **Intent định lượng** — Intent Object + confidence score điều khiển HITL/tự suy luận/chạy thẳng (Design §5).
2. **Planner DAG + song song hóa** — plan tường minh, fan-out nhánh độc lập, replan (Design §4 P4, §7).
3. **SQL tự sửa + Data Validator tách rời** — regen/retry có budget, dedup, degrade; validator ngữ nghĩa nghiệp vụ (Design §8.1–8.2).
4. **Answer Composer + chart/erp_guide tool** — câu trả lời giàu thông tin, gợi ý tiếp theo, tiếng Việt (Design §8.3, §8 v2 tools).
5. **Memory 3 tầng + compact + persistence** (Design §9).
6. **Guardrail nâng cấp** — capability/RBAC, ẩn cột nhạy cảm, chống prompt-injection, idempotency (Design §11).
7. **Budget đa tầng + async + tiered model routing + semantic cache + observability/eval** (Design §6.2, §12, §13).

### 1.1 Vì sao (gap hiện tại)
Vòng lặp hiện tại quyết định bằng **một** LLM `DecisionSchema` (call_tool/final_answer/clarify) tuần tự, không có Intent Object định lượng, không có Plan DAG/song song, không có data_validator/answer_composer/memory tầng, guard vẫn deny bằng **substring** (`harness/runtime.py:88-91`), token/cost chưa đo, chưa có tiered routing/cache/eval. Đây chính là khoảng cách so với Target Design.

---

## 2. Hiện trạng (Current State) — evidence

| Hạng mục | Đã có (file:dòng) | Trạng thái |
| :-- | :-- | :-- |
| Vòng lặp agentic + max_steps + dedup tool-call | `app/harness/orchestrator.py:80-174` | ✅ DONE (002) |
| Decision schema (call_tool/final_answer/clarify) | `app/harness/tool_registry.py:84-100` | ✅ DONE |
| ToolResult / TurnContext / ToolRegistry | `app/harness/tool_registry.py:11-81` | ✅ DONE |
| Scratchpad + observation summary | `app/harness/scratchpad.py:21-79` | ✅ DONE |
| Policy guard (capability check skeleton) | `app/harness/policy.py:34` | ✅ một phần |
| HITL pending/resume (catalog/inventory) | `orchestrator.py:160-188`, `api/runtime.py:156-188` | ✅ DONE (003) |
| Strangler routing | `api/runtime.py:_should_use_harness_loop`, `_quick_classify_harness_intent` | ✅ DONE |
| Tools: sql_query, schema_explore, catalog_draft, inventory_draft | `app/graph/tools/*.py`, `app/graph/nodes/*.py` | ✅ DONE |
| SQL self-correct (review/regen/retry) trong graph cũ | `app/graph/nodes/sql_pipeline.py` (~1297 dòng) | ⚠️ chưa thành tool harness chuẩn |
| Harness boundary `run_tool` | `app/harness/runtime.py:34-51` (sync) | ⚠️ sync + deny bằng substring |
| Async LLM/HTTP/checkpointer | `app/llm/openai_compatible.py`, `app/api/runtime.py:357-392` (event-loop bridge) | ❌ chưa async toàn trình |
| Token/cost per step | `InvokeUsage()` rỗng (NFR-3 của 002) | ❌ chưa đo |
| Intent Object + confidence thresholds | — | ❌ chưa có |
| Planner DAG + song song + replan | `app/graph/nodes/planner.py` (single-shot intent) | ❌ chưa có |
| data_validator (tách khỏi SQL) | — | ❌ chưa có |
| answer_composer | final_answer = LLM text trực tiếp | ❌ chưa có |
| chart / erp_guide là harness tool | còn ở graph cũ | ❌ (v2 của 002) |
| Memory 3 tầng + compact + pgvector | `app/graph/nodes` context_compact (graph cũ) | ❌ chưa lên harness |
| Guard RBAC/cột nhạy cảm/anti-injection/idempotency | — | ❌ chưa có |
| Tiered model routing + semantic cache | `llm_registry` đa model nhưng route tĩnh | ❌ chưa có routing động/cache |
| Observability metrics + eval golden set | audit jsonl cơ bản | ❌ chưa có metrics/eval |
| Knowledge assets K1–K15 (docs) | `docs/ai-python/agentic-ai-supporting-assets/002..016` | ✅ docs có; ⚠️ chưa wire hết vào tool |

---

## 3. Quy ước vận hành tự động (Automation Contract cho codex)

> Phần này nhúng trực tiếp **cách codex chạy** và **điều kiện để tự động tốt** đã thống nhất, để mỗi phase không lặp lại.

### 3.1 Vòng chạy của codex (mỗi phase)
1. Đọc phase hiện tại trong §5 (mục tiêu, scope, AC).
2. Xác định file/module cần sửa + dependency với phase trước.
3. Triển khai phase đó.
4. Chạy test tương ứng của phase (xem §3.3); phase sau phụ thuộc phase trước thì giữ trạng thái và tiếp tục.
5. Báo lại: **file đã sửa · test đã chạy · lỗi còn lại · phần chưa verify được nếu thiếu môi trường**.
6. Sau phase cuối: chạy **E2E flow toàn design** (§6).

### 3.2 Đập-đi-xây-lại vs Giữ tương thích (toàn cục)
- ✅ **Được phép viết lại (rebuild)**: nội bộ `app/harness/**` (loop, scratchpad, policy, budget), `app/graph/nodes/sql_pipeline.py` (tách thành tool), event-loop bridge `_iter_harness_stream`, reset state thủ công trong `api/runtime.py`, prompt nội bộ subagent.
- 🔒 **PHẢI giữ tương thích (đông cứng)**:
  - **SSE event contract** với FE/Spring: `progress | delta | delta_full | chart | draft | inventory_draft | data_table | clarify | error | done` (NFR-5 của 002). FE hiện tại chạy không sửa.
  - **HTTP API contract** của `app/api/routes.py` (request/response shape, harness chunk double-nest dưới key `harness` — xem ghi nhớ dự án).
  - **Strangler fallback**: tắt cờ `harness_loop_enabled` → 100% graph tuyến tính, không deploy lại.
  - **Spring backend API + schema DB**: không đổi (ngoài scope).
- Mọi thay đổi rebuild phải có **fallback path** (cờ cấu hình) để rollback ngay.

### 3.3 Cách chạy test & môi trường
| Lớp | Lệnh | Ghi chú determinism |
| :-- | :-- | :-- |
| AI unit/integration | `cd ai_python && python -m pytest tests -q` | `conftest.py` đặt `SQL_EXECUTOR_MODE=stub`; dùng `tests/fake_llm.py::FakeLlmClient` (LLM tất định) + fixture `patch_pg_schema_v1` (schema YAML offline). **Không cần Spring/Postgres/model thật.** |
| AI một phase | `python -m pytest tests/test_<phase>*.py -q` | Mỗi phase có file test riêng (đặt tên ở AC từng phase). |
| Frontend unit | `cd frontend/mini-erp && npm test` (vitest) | Chỉ chạy khi phase chạm FE (SRS-004 hầu như không). |
| Frontend e2e | `cd frontend/mini-erp && npm run test:e2e` (Playwright) | Dùng cho E2E khói nếu có harness server chạy. |
| Backend | `cd backend/smart-erp && mvn test` | Chỉ khi phase đụng Spring (SRS-004 không đổi Spring). |

### 3.4 Fallback mock bắt buộc (determinism)
- **LLM**: mọi subagent mới (intent, planner DAG, data_validator, answer_composer, compact, model_router) phải có nhánh test bằng `FakeLlmClient` mở rộng — thêm schema giả định cho `IntentObjectOutput`, `PlanGraphOutput`, `DataValidatorOutput`, `AnswerComposerOutput`, `CompactOutput`. Không gọi model thật trong unit test.
- **SQL/Spring**: dùng `SQL_EXECUTOR_MODE=stub`; rows giả định khai báo trong test.
- **pgvector / embeddings** (Memory semantic, K4 catalog): phải có **in-memory fake store** (cosine trên list) làm mặc định test; chỉ kết nối pgvector thật khi `SEMANTIC_STORE_MODE=pg`.
- **Semantic cache**: dùng dict in-memory trong test; backend thật là tùy chọn.
- Mọi external (model/embeddings/cache/Spring) đều phải **fallback mock** để test tất định — đây là điều kiện chấp nhận phase.

### 3.5 Quy ước cờ cấu hình
Mọi phase thêm cờ trong `app/config/graph_settings.py`, **mặc định OFF/an toàn**, bật dần theo intent (Strangler). Đặt tên `agentic_<feature>_enabled` + tham số ngưỡng cấu hình được (kế thừa D1–D11 của design §15).

---

## 4. Phạm vi & Lớp ảnh hưởng

**Trong phạm vi (toàn SRS-004)**: `ai_python/app/harness/**`, `ai_python/app/graph/tools/**`, một phần `ai_python/app/graph/nodes/**` (tách sql_pipeline), `app/api/runtime.py`, `app/api/routes.py` (giữ contract), `app/config/graph_settings.py`, `app/llm/**` (async + routing), `app/graph/checkpointing.py` (async/persist), `ai_python/tests/**`, `ai_python/scripts/**` (eval). Đọc (không sửa) `docs/ai-python/agentic-ai-supporting-assets/**` (K1–K15) làm tri thức.

**Ngoài phạm vi**: Spring backend & schema DB; đổi LLM provider; sửa FE (chỉ đảm bảo SSE không đổi); các K-asset cần biên soạn tay mới (nếu thiếu → ghi GAP/OQ).

---

## 5. Phân rã theo Phase

> Thứ tự khuyến nghị: **P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8**. P5/P6/P7 có thể chạy song song sau P0 nếu giữ trạng thái sạch. Mỗi phase đều có cờ riêng và test riêng.

---

### Phase P0 — Async boundary + Budget đa tầng + Token/Cost capture

- **Mục tiêu**: Nền tảng để các phase sau đo được chi phí và song song hóa. Async hóa LLM/HTTP/tool boundary; thêm budget đa tầng; điền token/cost mỗi bước.
- **Phụ thuộc**: SRS-002 (DONE).
- **File/module ưu tiên**:
  - `app/harness/runtime.py` — `AgentHarness.run_tool` → thêm `arun_tool` async; giữ sync làm wrapper tương thích.
  - `app/harness/orchestrator.py` — loop dùng async boundary thực sự (bỏ event-loop bridge khi có thể).
  - `app/api/runtime.py:357-392` — `_iter_harness_stream` rebuild sang async generator gốc (FastAPI `StreamingResponse`), **giữ thứ tự SSE**.
  - `app/llm/openai_compatible.py` — `ainvoke`/`astream`, điền `InvokeUsage(tokens, cost)`.
  - `app/graph/sql_executor.py` — `httpx.AsyncClient`.
  - **MỚI** `app/harness/budget.py` — `TurnBudget`: max_steps, token_budget, cost_budget_usd, wall_clock_timeout_s (Design §6.2, D9).
- **Đập-đi-xây-lại**: event-loop bridge `_iter_harness_stream`. **Giữ tương thích**: thứ tự & tên SSE events.
- **FR**:
  - FR-P0.1: Mọi tool-call đi qua boundary async không chặn event loop.
  - FR-P0.2: Loop dừng khi chạm bất kỳ budget (step/token/cost/wall-clock); hành vi = trả `final_answer` best-effort từ observation + ghi audit lý do (`*_budget_exhausted`).
  - FR-P0.3: Mỗi bước ghi `tokens`, `cost_usd`, `latency_ms` vào audit.
- **Test data**: FakeLlmClient trả usage giả định (vd 100 tokens/step, cost 0.001$); test ép `cost_budget_usd=0.002` để loop dừng ở bước 2.
- **Expected output**: audit jsonl có trường tokens/cost/latency mỗi bước; loop dừng đúng budget; không có blocking call (test bằng `asyncio` không deadlock).
- **Cách chạy test**: `python -m pytest tests/test_harness_async_contracts.py tests/test_harness_budget.py -q`.
- **Acceptance Criteria**:
  - AC-P0.1: Test async không có blocking call trên event loop.
  - AC-P0.2: Với `cost_budget_usd` nhỏ → loop dừng đúng bước, trả best-effort, audit ghi `cost_budget_exhausted`.
  - AC-P0.3: Tắt cờ async (`agentic_async_enabled=False`) → hành vi cũ giữ nguyên (regression `test_harness_orchestrator.py` pass).

---

### Phase P1 — Intent Object + Confidence định lượng + Entity resolution

- **Mục tiêu**: Thay quyết định mơ hồ bằng **Intent Object** có `confidence` định lượng điều khiển HITL/tự suy luận/chạy thẳng (Design §5).
- **Phụ thuộc**: P0.
- **File/module ưu tiên**:
  - **MỚI** `app/harness/intent.py` — `IntentObject` (goal, intent_type, required_data, resolved_entities[{raw,matched,score}], confidence, ambiguities, missing_required) + `IntentSubagent` đọc K1 (data dictionary), K2 (synonym), K4 (catalog embeddings).
  - `app/harness/orchestrator.py` — chạy intent trước loop; áp ngưỡng D1/D2.
  - `app/harness/scratchpad.py` — đính kèm IntentObject vào prompt decide.
  - Đọc: `docs/ai-python/agentic-ai-supporting-assets/002_K1_*`, `003_K2_*`, `005_K4_*`.
- **Đập-đi-xây-lại**: `_quick_classify_harness_intent` (heuristic) → thay bằng IntentSubagent (giữ heuristic làm fallback khi LLM lỗi). **Giữ tương thích**: SSE `clarify` event (đã có).
- **Ngưỡng (cấu hình, default theo D1/D2)**:
  - `missing_required` ≠ rỗng → **HITL bắt buộc** (clarify).
  - `confidence < 0.75` **hoặc** entity score < 0.6 → **HITL** kèm option đề xuất.
  - `0.75 ≤ confidence < 0.9` → tự chọn entity điểm cao nhất, ghi giả định.
  - `confidence ≥ 0.9` → vào loop ngay.
- **FR**:
  - FR-P1.1: IntentSubagent trả IntentObject hợp lệ cho mọi require.
  - FR-P1.2: Entity được chấm điểm bằng fuzzy + embedding với danh mục thực (K4); fallback fuzzy-only nếu store mock.
  - FR-P1.3: Áp ngưỡng → đúng nhánh HITL/auto/run; clarify question kèm 1–3 option đề xuất + lý do.
- **Test data**: require "doanh thu tháng này" (confidence 0.95 → run); "báo cáo bán hàng" thiếu time period (missing_required → clarify); "áo" mơ hồ nhiều SKU (entity score 0.5 → clarify với options). Embeddings dùng fake in-memory store.
- **Expected output**: IntentObject đúng cho từng ca; ca thiếu param phát `clarify` SSE; ca rõ ràng vào loop.
- **Cách chạy test**: `python -m pytest tests/test_intent_object.py tests/test_intent_confidence_thresholds.py -q`.
- **Acceptance Criteria**:
  - AC-P1.1: 3 ca test (run/auto/clarify) đúng nhánh theo ngưỡng cấu hình.
  - AC-P1.2: clarify question luôn kèm ≥1 option + lý do, bằng tiếng Việt.
  - AC-P1.3: LLM lỗi → fallback heuristic, không crash turn.

---

### Phase P2 — Planner DAG + Song song hóa + Replan

- **Mục tiêu**: Plan tường minh dạng **Plan Graph (DAG)**; nhánh độc lập chạy song song (P4); replan khi tool báo sai (Design §7).
- **Phụ thuộc**: P0 (async), P1 (IntentObject).
- **File/module ưu tiên**:
  - **MỚI** `app/harness/plan_graph.py` — `PlanGraph` (nodes[{id,tool,needs,input_spec,output_expect}]) + `PlanExecutor` chạy DAG async (fan-out node không `needs` chung), tổng hợp observation.
  - **MỚI** `PlannerSubagent` (trong `plan_graph.py` hoặc `app/harness/planner.py`) — sinh PlanGraph từ IntentObject (đọc K1).
  - `app/harness/orchestrator.py` — chế độ "plan-driven" (cờ `agentic_plan_dag_enabled`) bên cạnh chế độ reactive (loop step-by-step hiện tại) làm fallback.
- **Đập-đi-xây-lại**: được phép thêm executor mới; **giữ** loop reactive cũ làm fallback (mặc định khi cờ OFF).
- **FR**:
  - FR-P2.1: Node không phụ thuộc chung chạy song song (đo bằng concurrency, không tuần tự).
  - FR-P2.2: Mỗi node khai báo input_spec + output_expect; executor validate output_expect.
  - FR-P2.3: Khi data_validator (P3) hoặc tool báo phủ định → replan: sửa node lỗi hoặc thêm node clarify; nếu mơ hồ vượt ngưỡng → quay lại HITL.
  - FR-P2.4: Chuỗi tổ hợp `schema_explore → sql_query → (chart|answer)` chạy không cần hardcode edge (kế thừa AC-1 của 002).
- **Test data**: require cần 2 SQL độc lập (doanh thu + tồn kho) → PlanGraph 2 node song song + 1 node composer; FakeLlmClient trả PlanGraphOutput tất định.
- **Expected output**: 2 node SQL chạy song song; observation tổng hợp đúng; replan kích hoạt khi validator fail (test ở P3).
- **Cách chạy test**: `python -m pytest tests/test_plan_graph.py tests/test_plan_parallel.py -q`.
- **Acceptance Criteria**:
  - AC-P2.1: 2 node độc lập chạy đồng thời (test đo bằng cờ thời gian/đếm concurrency mock).
  - AC-P2.2: output_expect không đạt → executor đánh dấu node fail → trigger replan.
  - AC-P2.3: Cờ OFF → dùng loop reactive cũ, regression pass.

---

### Phase P3 — SQL Subagent self-correcting (tool hoá) + Data Validator

- **Mục tiêu**: Đưa pipeline SQL self-correct thành **tool harness chuẩn** với budget regen/retry, dedup, degrade; tách **data_validator** đánh giá ngữ nghĩa nghiệp vụ (Design §8.1–8.2).
- **Phụ thuộc**: P2 (replan), P1 (required_data).
- **File/module ưu tiên**:
  - `app/graph/nodes/sql_pipeline.py` (~1297 dòng) → tách thành: `sql_raw`, `sql_review`, `execute` + adapter `app/graph/tools/sql_query.py` (đã có vỏ tool).
  - **MỚI** `app/graph/tools/data_validator.py` — `DataValidatorTool`: kiểm tra số liệu vô lý (âm/vượt trần), thiếu cột vs `required_data`, lệch thời gian; đọc K8 (công thức nghiệp vụ), K3 (enum).
  - Đọc: K1, K2, K3, K5 (allowlist), K7 (few-shot), K8.
- **Budget (cấu hình, D11)**: review-fail regen ≤ 3; empty-result retry ≤ 2; **dedup** theo SQL fingerprint + lý do lỗi (dừng nếu trùng); **degrade** trả kết quả gần nhất hợp lệ + cảnh báo thay vì fail cứng.
- **Đập-đi-xây-lại**: tái cấu trúc `sql_pipeline.py` (god file). **Giữ tương thích**: read-only enforcement (`enforce_read_only_sql`), `data_table` SSE.
- **FR**:
  - FR-P3.1: sql_review phủ định → regen ≤3; execute rỗng → retry ≤2 rồi review lại.
  - FR-P3.2: Fingerprint SQL + lý do lỗi trùng → short-circuit (không tốn bước).
  - FR-P3.3: data_validator pass → answer_composer; fail → feedback về sql node (replan P2).
  - FR-P3.4: Không đạt trong budget → degrade: trả rows gần nhất + cảnh báo, không raise.
- **Test data**: `FakeLlmClient(sql_review_failures=2)` (đã hỗ trợ) → regen 2 lần rồi pass; rows âm để validator fail; rows hợp lệ để validator pass.
- **Expected output**: regen đúng số lần; validator phân loại pass/fail kèm lý do; degrade trả cảnh báo tiếng Việt.
- **Cách chạy test**: `python -m pytest tests/test_sql_query_domain.py tests/test_data_validator.py tests/test_sql_self_correct_budget.py -q`.
- **Acceptance Criteria**:
  - AC-P3.1: SQL ghi (INSERT/UPDATE/DELETE/DROP...) bị chặn 100% kể cả LLM cố sinh.
  - AC-P3.2: regen ≤3 / retry ≤2 đúng budget; dedup chặn lặp.
  - AC-P3.3: data_validator fail (số âm) → trigger replan; pass → chuyển composer.
  - AC-P3.4: degrade trả kết quả từng phần + cảnh báo, không crash.

---

### Phase P4 — Answer Composer + chart tool + erp_guide tool

- **Mục tiêu**: Câu trả lời giàu thông tin, nêu giả định, kèm 1–3 gợi ý tiếp theo, tiếng Việt; đưa chart & erp_guide lên harness tool (v2 của 002) (Design §8.3).
- **Phụ thuộc**: P3 (rows + validator).
- **File/module ưu tiên**:
  - **MỚI** `app/graph/tools/answer_composer.py` — `AnswerComposerTool`: format bảng/số liệu/điểm nhấn, nêu giả định (từ P1), 1–3 follow-up; đọc K10 (answer templates), K14 (định dạng VND/ngày).
  - **MỚI** `app/graph/tools/build_chart.py` — adapter chart hiện hữu thành tool (đọc K9 chart-spec catalog).
  - **MỚI** `app/graph/tools/erp_guide.py` — adapter erp_guide thành tool (đọc K13).
  - Đăng ký vào `app/harness/tool_registry.py`.
- **Đập-đi-xây-lại**: prompt composer nội bộ. **Giữ tương thích**: `chart` SSE payload, `delta_full` final answer.
- **FR**:
  - FR-P4.1: answer_composer luôn trả tiếng Việt, nêu giả định nếu có, kèm 1–3 câu hỏi gợi ý.
  - FR-P4.2: Khi rỗng/lỗi → đề nghị user nhập chi tiết hơn kèm ví dụ.
  - FR-P4.3: chart tool chọn loại biểu đồ theo shape dữ liệu (time_series→line, phân bổ→bar/pie) theo K9.
- **Test data**: rows doanh thu theo tháng → composer ra bảng + 2 gợi ý; rows rỗng → thông điệp hướng dẫn; rows time-series → chart line.
- **Expected output**: final answer có điểm nhấn + gợi ý; chart SSE đúng type; thông điệp lỗi thân thiện tiếng Việt.
- **Cách chạy test**: `python -m pytest tests/test_answer_composer.py tests/test_chart_pipeline.py -q`.
- **Acceptance Criteria**:
  - AC-P4.1: answer_composer output luôn có ≥1 gợi ý tiếp theo, tiếng Việt.
  - AC-P4.2: chart type đúng theo shape dữ liệu; SSE `chart` không đổi contract.
  - AC-P4.3: Ca rỗng → thông điệp hướng dẫn, không trả lời cụt.

---

### Phase P5 — Memory 3 tầng + Compact + Persistence

- **Mục tiêu**: working / episodic / semantic memory + compact tự động + checkpoint bền theo `thread_id` (Design §9).
- **Phụ thuộc**: P0.
- **File/module ưu tiên**:
  - **MỚI** `app/harness/memory.py` — `WorkingMemory` (N=6 cặp, D3), `EpisodicMemory` (summary phiên), `SemanticMemory` (pgvector, D5; fake in-memory mặc định test).
  - **MỚI** `app/harness/compact.py` — `CompactSubagent`: nén khi context ≥ 70% (D4), gắn nhãn `[COMPACT]`, giữ mốc thời gian/ràng buộc/kết quả quan trọng; compact theo tầng (working→episodic).
  - `app/graph/checkpointing.py:16` — async/persist (AsyncSqliteSaver hoặc Postgres — OD-6 của 002, chốt ở Tech Spec).
  - `app/api/runtime.py` — nạp working memory mỗi require; xoá reset thủ công → `fresh_turn()`.
- **Đập-đi-xây-lại**: reset state thủ công (`api/runtime.py`), checkpoint SQLite chia sẻ 1 connection. **Giữ tương thích**: thread_id contract; SSE.
- **FR**:
  - FR-P5.1: Mỗi require đính kèm N=6 cặp gần nhất.
  - FR-P5.2: Context ≥70% → gọi compact, sinh `[COMPACT]` block, không nén nội dung đang dở.
  - FR-P5.3: Semantic memory recall theo độ liên quan; không lưu PII thô (D6), expire 90 ngày (D5).
  - FR-P5.4: Checkpoint persist qua restart cho HITL resume (nâng cấp `_pending_hitl` in-memory của 003 → bền).
- **Test data**: phiên 10 lượt vượt ngưỡng token (ép ngưỡng thấp) → compact kích hoạt; semantic store fake với 3 preference.
- **Expected output**: `[COMPACT]` message xuất hiện; working memory đúng 6 cặp; recall trả preference liên quan.
- **Cách chạy test**: `python -m pytest tests/test_context_compact.py tests/test_memory_tiers.py tests/test_checkpoint_persist.py -q`.
- **Acceptance Criteria**:
  - AC-P5.1: Vượt 70% → compact tạo `[COMPACT]`, giữ mốc/ràng buộc.
  - AC-P5.2: Working memory giữ đúng N cặp cấu hình.
  - AC-P5.3: Semantic store fallback in-memory chạy không cần pgvector; PII thô không được lưu.
  - AC-P5.4: HITL resume sống sót qua restart (với store bền) hoặc trả lỗi `HITL_EXPIRED` rõ ràng (in-memory).

---

### Phase P6 — Guardrail nâng cấp: Capability/RBAC + cột nhạy cảm + anti-injection + idempotency

- **Mục tiêu**: Guard theo **capability** thay substring; enforce tenant/role; ẩn cột nhạy cảm theo role; chống prompt-injection; idempotency mutation (Design §11).
- **Phụ thuộc**: SRS-002 policy skeleton.
- **File/module ưu tiên**:
  - `app/harness/policy.py` — capability-based check (đọc K5 allowlist, K6 RBAC matrix); thay deny-substring ở `app/harness/runtime.py:88-91`.
  - **MỚI** `app/harness/capability.py` — `CapabilityMatrix` (role × hành động/cột); ẩn cột nhạy cảm (D7: `staff` ẩn `products.cost_price`, `finance_ledger`, margin).
  - `app/harness/scratchpad.py` / intent — tách "dữ liệu user" khỏi "chỉ thị hệ thống" (anti-injection G4), whitelist hành động.
  - draft tools — khóa idempotency cho mutation (G6).
  - Đọc: `006_K5_*`, `007_K6_*`.
- **Đập-đi-xây-lại**: deny-substring trong `runtime.py`. **Giữ tương thích**: read-only enforcement vẫn còn (defense-in-depth).
- **FR**:
  - FR-P6.1: Guard quyết định theo capability + tenant + role, không theo substring tên tool.
  - FR-P6.2: `staff` truy vấn cột nhạy cảm → bị ẩn/từ chối theo D7; `owner` full.
  - FR-P6.3: Chỉ thị nhúng trong dữ liệu (vd cell chứa "ignore previous...") bị bỏ qua.
  - FR-P6.4: Mutation có idempotency key → retry không nhân đôi.
- **Test data**: role=staff hỏi giá vốn → ẩn; SQL có `; DROP` → chặn; rows chứa injection text → bỏ qua; double-submit draft cùng key → 1 bản ghi.
- **Expected output**: 403-ngữ-nghĩa tiếng Việt khi vượt quyền ("Bạn không có quyền..."); cột nhạy cảm bị ẩn; injection vô hiệu.
- **Cách chạy test**: `python -m pytest tests/test_harness_policy.py tests/test_capability_rbac.py tests/test_anti_injection.py -q`.
- **Acceptance Criteria**:
  - AC-P6.1: SQL ghi bị chặn 100% qua capability guard (không chỉ substring).
  - AC-P6.2: staff không thấy cột nhạy cảm (D7); owner thấy đủ.
  - AC-P6.3: Prompt-injection trong dữ liệu không đổi hành vi.
  - AC-P6.4: Idempotency chặn nhân đôi mutation.

---

### Phase P7 — Tiered model routing + Semantic cache

- **Mục tiêu**: Model rẻ cho việc nhẹ, mạnh cho việc khó; cache kết quả tất định (Design §13 N1/N3, D10).
- **Phụ thuộc**: P0 (đo cost), P1/P2/P3 (các subagent đã có).
- **File/module ưu tiên**:
  - **MỚI** `app/harness/model_router.py` — route theo loại việc: intent/compact → Haiku; planner/sql/compose → Sonnet; leo Opus khi replan ≥ 2 (D10). Cấu hình map việc→model.
  - **MỚI** `app/harness/cache.py` — semantic cache cho kết quả tất định (schema explore, SQL theo fingerprint+tenant); dict in-memory mặc định; backend tùy chọn.
  - `app/llm/llm_registry` — cấp client theo model id router chọn.
- **Đập-đi-xây-lại**: route model tĩnh. **Giữ tương thích**: không đổi provider/model id (chỉ chọn trong registry sẵn có).
- **FR**:
  - FR-P7.1: Mỗi loại subagent gọi đúng tier model theo bảng cấu hình; replan ≥2 leo Opus.
  - FR-P7.2: Cache hit cho schema explore / SQL fingerprint+tenant trùng → bỏ qua gọi lại, ghi audit `cache_hit`.
- **Test data**: 2 lượt cùng SQL fingerprint+tenant → lượt 2 cache hit; replan 2 lần → router chọn Opus (mock registry ghi nhận model id yêu cầu).
- **Expected output**: audit ghi model id theo tier; cache hit giảm số gọi.
- **Cách chạy test**: `python -m pytest tests/test_model_router.py tests/test_semantic_cache.py -q`.
- **Acceptance Criteria**:
  - AC-P7.1: Router chọn đúng model theo loại việc + leo Opus khi replan≥2.
  - AC-P7.2: Cache hit cho input tất định trùng; tenant khác không dùng chung cache.

---

### Phase P8 — Observability + Eval golden set

- **Mục tiêu**: Trace/metrics đầy đủ + bộ eval golden chạy regression khi đổi prompt/model (Design §12).
- **Phụ thuộc**: tất cả phase trên.
- **File/module ưu tiên**:
  - `app/harness/runtime.py` / **MỚI** `app/harness/observability.py` — trace cây node, correlation_id, tenant, thread, latency/token/cost/retry; metrics p50/p95 theo intent, tỉ lệ HITL/replan/chạm budget.
  - **MỚI** `ai_python/scripts/eval_golden.py` — chạy K12 golden set (`013_K12_golden_eval_set.md`) cho intent/SQL/answer; báo pass/fail regression.
  - Đọc: `013_K12_*`.
- **Đập-đi-xây-lại**: format audit. **Giữ tương thích**: SSE.
- **FR**:
  - FR-P8.1: Mỗi turn có trace đầy đủ (node tree + cost/latency/retry).
  - FR-P8.2: `eval_golden.py` chạy được offline (FakeLlmClient/stub) và báo tỉ lệ pass.
  - FR-P8.3: Audit cảnh báo khi chạm step/cost budget, guard chặn, HITL hết hạn.
- **Test data**: golden set tối thiểu 10 câu (subset K12) với expected intent/answer-shape.
- **Expected output**: report eval pass/fail; metrics có mặt trong audit.
- **Cách chạy test**: `python -m pytest tests/test_observability.py -q` và `python scripts/eval_golden.py --offline`.
- **Acceptance Criteria**:
  - AC-P8.1: Trace mỗi turn có cost/latency/retry; metrics tính được theo intent.
  - AC-P8.2: eval_golden offline chạy xanh trên subset; regression phát hiện khi đổi prompt mock.

---

## 6. E2E flow cuối (sau P8)

Chạy toàn bộ design end-to-end (offline, mock determinism):

```
request "Doanh thu và tồn kho tháng này, vẽ biểu đồ"
 → IntentSubagent (P1): confidence 0.95, required_data=[revenue, inventory], intent=chart_report
 → PlannerSubagent (P2): PlanGraph 2 SQL node song song → data_validator → chart → answer_composer
 → Harness loop (P0 budget/async) điều phối qua boundary (P6 guard: read-only + tenant + role)
 → sql_query x2 self-correct (P3) → data_validator pass
 → build_chart (P4) → SSE "chart"
 → answer_composer (P4) → SSE "delta_full" + 2 gợi ý → "done"
 → Memory (P5): lưu working/episodic; Observability (P8): trace cost/latency
```

**HITL e2e**: "tạo sản phẩm Áo thun" → catalog_draft pending_hitl → SSE `draft` → resume (003) → confirm Spring (stub) → final_answer.

- **Cách chạy E2E**: `python -m pytest tests/test_e2e_agentic_flow.py -q` (mock LLM/SQL/embeddings). Nếu có server harness chạy → `cd frontend/mini-erp && npm run test:e2e` cho khói FE↔SSE.
- **Báo cáo cuối (codex)**: liệt kê file đã sửa theo phase, test đã chạy + kết quả, lỗi còn lại, phần chưa verify do thiếu môi trường (vd pgvector/model thật).

---

## 7. Yêu cầu phi chức năng (NFR tổng)

- **NFR-1 (Chi phí/độ trễ)**: SLO p95 — data_query ≤ 8s, chart_report ≤ 12s, chat ≤ 3s (D8); budget/turn step 10, cost ≤ $0.05, timeout 30s (D9).
- **NFR-2 (Async/throughput)**: không blocking call trên event loop; fan-out DAG song song (P2).
- **NFR-3 (Quan sát được)**: token/cost/latency mỗi bước (P0); metrics + eval (P8).
- **NFR-4 (An toàn)**: guard bất biến ở Harness mọi tool-call; loop không vô hạn (P0 budget).
- **NFR-5 (Tương thích)**: SSE event contract + HTTP API + Strangler fallback không đổi.
- **NFR-6 (Determinism test)**: mọi external có fallback mock (§3.4).

---

## 8. Guardrail bất biến (xuyên suốt mọi phase)

- Chỉ SELECT cho data_query; chặn DDL/DML + multi-statement (giữ từ 002, củng cố P6).
- Enforce tenant/role ở Harness + RLS Backend; AI không bypass auth.
- Mọi mutation qua HITL draft → confirm → audit (003 + P6 idempotency).
- Tách dữ liệu user khỏi chỉ thị hệ thống; bỏ qua injection nhúng (P6).
- Không log PII thô (D6).

---

## 9. Owner Decisions

Kế thừa **D1–D11** của Design §15 (ngưỡng confidence, ambiguity, N memory, compact 70%, pgvector 90 ngày, PII, cột nhạy cảm, SLO, budget, tiered routing, SQL budget) và **OD-1..OD-4** của SRS-002 (Harness-native loop, Strangler, async, tool scope). Tất cả **cấu hình được**.

### 9.1 Quyết định còn mở (chốt ở Tech Spec)
- **OD-5** (từ 002): provider cho "decision" — function-calling native vs structured JSON.
- **OD-6** (từ 002): checkpointer async — AsyncSqliteSaver vs Postgres (ảnh hưởng P5).
- **OD-7** (từ 002): trần loop mặc định + hành vi chạm trần (đã định hướng best-effort ở P0).
- **OD-8** (mới): Plan-driven (P2) là chế độ mặc định hay reactive-loop là mặc định, cờ bật theo intent nào?
- **OD-9** (mới): semantic store thật — pgvector chung DB hay store riêng? (Tận dụng D5: pgvector.)
- **OD-10** (mới): Spring endpoint confirm cho catalog/inventory draft (kế thừa OQ-1/OQ-2 của 003 — vẫn mở).

---

## 10. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
| :-- | :-- | :-- |
| Loop nhiều subagent tăng chi phí/độ trễ | Cao | Budget đa tầng (P0), tiered routing + cache (P7), fast-path chat |
| Rewrite async chạm nhiều file | Cao | Làm theo lát cắt, cờ `agentic_async_enabled`, fallback sync |
| Guard rò khi đổi sang capability | Cao | Read-only enforcement giữ lại (defense-in-depth); test P6 |
| Tách `sql_pipeline.py` (1297 dòng) gây regression | Cao | Tách dần, giữ adapter tool tương thích, regression `test_sql_*` |
| Vỡ SSE/HITL khi async hoá stream | Cao | Strangler giữ luồng cũ; test contract SSE trước khi route |
| Thiếu K-asset biên soạn tay (K7/K8/K10...) | Trung bình | Ghi OQ; degrade chạy với asset tối thiểu |
| pgvector chưa sẵn → semantic memory | Trung bình | Fallback in-memory mock mặc định (§3.4) |

---

## 11. Open Questions

- **OQ-1**: Spring endpoint POST confirm catalog draft? (kế thừa 003 OQ-1 — blocker cho P4/HITL confirm thật).
- **OQ-2**: Spring endpoint POST confirm inventory draft? (kế thừa 003 OQ-2).
- **OQ-3**: pgvector đã bật trên Postgres hiện tại chưa? Nếu chưa → P5 semantic chỉ chạy mock (không blocker, ghi nhận).
- **OQ-4**: K7 (few-shot SQL), K8 (công thức nghiệp vụ), K10 (answer templates) đã đủ nội dung để wire chưa, hay cần biên soạn thêm? (ảnh hưởng chất lượng P3/P4, không blocker chạy.)
- **OQ-5**: Có cần "tool retry budget" riêng từng tool, hay budget turn toàn cục (P0) đủ? (kế thừa 002.)
- **OQ-6**: Biểu diễn observation kết quả lớn (bảng SQL nhiều dòng) trong scratchpad — tóm tắt hay tham chiếu? (đang truncate 800 ký tự ở `scratchpad.py:11`.)

---

## 12. Acceptance Criteria tổng (Definition of Done SRS-004)

- **AC-T1**: Mỗi phase P0–P8 pass test riêng (§5) bằng mock determinism, không cần model/Spring/pgvector thật.
- **AC-T2**: E2E flow (§6) chạy xanh offline: request → intent → plan DAG → tools → validator → chart → composer → SSE → done; cộng HITL draft resume.
- **AC-T3**: Tắt mọi cờ agentic (`agentic_*_enabled=False`) → hành vi = graph tuyến tính/loop 002 hiện tại (regression toàn bộ `tests/` pass).
- **AC-T4**: SSE event contract + HTTP API + harness chunk nesting không đổi; FE chạy không sửa.
- **AC-T5**: Guard chặn 100% SQL ghi + vượt quyền role; loop không vượt budget; mỗi bước có token/cost/latency.

---

## 13. Handoff

- **Next stage**: `TECH_SPEC_WRITER` — thiết kế contract chi tiết từng subagent mới (IntentObject, PlanGraph, DataValidator, AnswerComposer, Compact, ModelRouter, Cache, Capability), async wiring, lát cắt triển khai bite-sized theo từng phase, chốt OD-5..OD-10.
- **Readiness**: READY_FOR_TECH_SPEC. Các OQ blocker (OQ-1/OQ-2 Spring confirm endpoint) chỉ chặn nhánh **confirm thật** của HITL; toàn bộ phase còn lại lập Tech Spec được ngay với mock.
- **Thứ tự ưu tiên đề xuất cho codex**: P0 → P1 → P3 → P2 → P4 → P6 → P5 → P7 → P8 (đưa SQL/validator sớm vì giá trị nghiệp vụ cao nhất; P2 plan-DAG có thể sau P3 nếu reactive-loop tạm đủ).
