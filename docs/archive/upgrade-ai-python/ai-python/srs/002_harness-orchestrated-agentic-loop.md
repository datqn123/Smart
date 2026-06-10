# SRS-002 (upgrade/ai-python): Harness-Orchestrated Agentic Loop

- **Status**: DRAFT — SRS_WRITER stage
- **Author**: AI workflow (SRS_WRITER)
- **Date**: 2026-06-07
- **Scope tier**: Architecture re-design (ai_python)
- **Related**: `docs/upgrade/ai-python/srs/SRS_AI_Task007_agent-sql-factory-upgrade.md`, AGENTS.md (LangGraph orchestrator / Harness boundary / tools separation)

---

## 1. Mục tiêu & Tầm nhìn

Chuyển mô hình điều phối của `ai_python` từ **graph tuyến tính có router** (intent phân loại một lần rồi đi đường gần như cố định) sang **vòng lặp agentic do Harness điều phối**:

- **LangGraph** chuyển vai: từ *orchestrator tuyến tính* → *thư viện capabilities (tools)*. Mỗi subgraph hiện hữu (sql, schema_explore, catalog draft, inventory draft, chart, erp_guide) trở thành một **tool** có contract đầu vào/đầu ra rõ ràng, gọi được độc lập.
- **Harness** chuyển vai: từ *audit wrapper tượng trưng* → **bộ điều phối vòng lặp (orchestrator)** chạy chu trình "LLM suy luận → chọn tool → thực thi qua boundary → quan sát kết quả → lặp → trả lời cuối", đồng thời ép buộc budget bước, permission, retry, audit, HITL, và điều kiện dừng.

### 1.1 Vì sao
Kiến trúc hiện tại (`app/graph/main_graph.py`) là một DAG cố định: `domain_guard → context_compact → agent_planner → classify_intent → {chat_normal | sql_branch | catalog_draft | inventory_draft} → summarize`. Quyết định "agentic" thực chất chỉ là **một** lần phân loại intent ở đầu; sau đó luồng gần như tất định. Hệ quả:

- Không thể chuỗi tool tổ hợp (vd `schema_explore → sql_query → build_chart`) nếu chưa có edge hardcode.
- Vai trò "Harness = execution/validation boundary" mà AGENTS.md tuyên bố **chưa thành hiện thực**: chỉ 4 node gọi `deps.harness.run_tool` (`sql_pipeline.py`, `schema_explore.py`, `inventory_draft.py`, `catalog_draft.py`), các lời gọi LLM/HTTP khác bỏ qua harness; deny dựa trên **substring** tên tool (`harness/runtime.py:88-91`) trùng vai với `sql_safety.enforce_read_only_sql`.

---

## 2. Hiện trạng (Current State)

| Thành phần | File | Vấn đề |
| :-- | :-- | :-- |
| Orchestration tuyến tính | `app/graph/main_graph.py` | Router 1 lần, không có vòng lặp suy luận đa bước |
| Harness tượng trưng | `app/harness/runtime.py` (107 dòng) | Chỉ wrap 4 node; deny bằng substring; không bao trọn side-effect |
| God state phẳng | `app/graph/state.py` (~70 keys) | Mọi subgraph share 1 TypedDict; coupling cao |
| Reset state thủ công | `app/api/runtime.py:88-168` | Null tay ~60 keys, nhân bản schema → nguy cơ "checkpoint bleed" |
| Toàn bộ sync | `llm/openai_compatible.py:32`, `sql_executor.py:107`, `api/runtime.py:63,80` | Không fan-out song song; nghẽn ở threadpool |
| God file | `app/graph/nodes/sql_pipeline.py` (1297 dòng) | gen/review/validate/execute + heuristic trộn lẫn |
| Checkpoint SQLite chia sẻ | `app/graph/checkpointing.py:16` | 1 connection `check_same_thread=False` dùng chung dưới đa luồng |

Tham chiếu phân tích đầy đủ: hội thoại audit ngày 2026-06-07 (P0 #1–3, P1 #4–8).

---

## 3. Kiến trúc đề xuất (Target Architecture)

### 3.1 Sơ đồ khái niệm

```text
HTTP /stream (async)
   │
   ▼
HarnessOrchestrator.run(turn)        ← OWNS THE LOOP
   │  ┌─────────────────────────────────────────────┐
   │  │ while not done and step < budget:            │
   │  │   decision = planner_llm.decide(             │
   │  │       tools_manifest, scratchpad)            │  ← 1 LLM "next-action" call
   │  │   if decision.is_final: break                │
   │  │   guard.check(decision.tool, args)           │  ← permission/invariants
   │  │   result = await tool.invoke(args, ctx)      │  ← LangGraph subgraph as tool
   │  │   scratchpad.append(observation(result))     │
   │  │   emit_progress_sse(...)                      │
   │  └─────────────────────────────────────────────┘
   │
   ▼
final_answer  (+ chart_spec / draft_sse / data_table_sse giữ nguyên contract FE)
```

### 3.2 Quyết định kiến trúc (đã chốt với Owner — xem §7)

- **OD-1 Mô hình loop = Harness-native**: Harness chạy vòng lặp bằng Python thuần (async), gọi các subgraph LangGraph đã compile như tool. LangGraph **không** còn điều phối top-level; nó là tool implementation.
- **OD-2 Migration = Strangler**: dựng loop mới song song; route một tập intent sang loop; giữ graph tuyến tính hiện tại làm fallback + rollback path. Cờ cấu hình bật/tắt theo intent.
- **OD-3 Async = có, ngay đợt này**: LLM (`ainvoke`/`astream`), HTTP (`httpx.AsyncClient`), tool invoke, checkpointer async — làm cùng lúc để tránh rewrite 2 lần.
- **OD-4 Tool scope v1**: `sql_query`, `schema_explore`, `catalog_draft` (HITL), `inventory_draft` (HITL). `build_chart` và `erp_guide` lên tool ở v2; `chat_normal` giữ làm fast-path.

### 3.3 Thành phần mới

1. **`app/harness/orchestrator.py`** — `HarnessOrchestrator`: vòng lặp agentic async, step budget, tool-call cap, điều kiện dừng (`final_answer` tool hoặc max steps), phát SSE progress.
2. **`app/harness/tool_registry.py`** — manifest tool: tên, mô tả, JSON schema args, capability tag, có/không HITL. Là nguồn để LLM "decide".
3. **`app/harness/policy.py`** — guard theo **capability** (không phải substring): read-only enforcement, tenant scoping, denylist, budget. Thay thế/đứng trước `sql_safety` thay vì trùng lặp.
4. **`app/harness/scratchpad.py`** — working memory của 1 lượt: messages + tool observations + plan. Tách khỏi god-state.
5. **Tool adapters** — bọc subgraph LangGraph hiện hữu thành tool contract đồng nhất: `ToolResult { ok, output, observation_text, sse_payload?, pending_hitl? }`.

### 3.4 Tái cấu trúc đi kèm (bắt buộc để loop hoạt động sạch)

- **State**: tách `AgentState` god-TypedDict thành `TurnScratchpad` (transient, do orchestrator sở hữu) + per-tool input/output models. Xóa reset thủ công ở `api/runtime.py` → một `fresh_turn()` duy nhất.
- **HITL**: mô hình hóa lại draft catalog/inventory thành tool trả `pending_hitl` → orchestrator dừng loop, phát `draft`/`inventory_draft` SSE, chờ `clarification_response` lượt sau (thay cho interrupt+checkpointer của LangGraph). **Contract SSE với FE không đổi.**

---

## 4. Yêu cầu chức năng (Functional Requirements)

- **FR-1**: Harness chạy vòng lặp đa bước; mỗi bước gọi đúng 1 "next-action" LLM decision dựa trên tool manifest + scratchpad.
- **FR-2**: Mỗi tool có contract đồng nhất; orchestrator gọi tool qua boundary có permission + audit + timeout + retry tập trung.
- **FR-3**: Loop dừng khi (a) LLM phát `final_answer`, hoặc (b) đạt `max_steps`/`max_tool_calls`, hoặc (c) một tool trả `pending_hitl`.
- **FR-4**: Chuỗi tool tổ hợp hoạt động không cần hardcode edge (vd `schema_explore → sql_query`).
- **FR-5**: Strangler routing — cờ cấu hình quyết định intent nào đi loop mới vs graph cũ; mặc định an toàn (graph cũ) cho intent chưa hỗ trợ.
- **FR-6**: HITL draft (catalog/inventory) giữ nguyên hành vi FE: phát SSE `draft`/`inventory_draft`, nhận lại `clarification_response`.
- **FR-7**: Fast-path: `chat_normal` và `domain_guard` reject chạy trực tiếp, không vào loop (tiết kiệm token/độ trễ).
- **FR-8**: Mọi SQL vẫn bị ép read-only; mọi tool-call bị guard kiểm tra capability + tenant trước khi thực thi.

## 5. Yêu cầu phi chức năng (Non-Functional)

- **NFR-1 (Chi phí/độ trễ)**: số LLM decision/lượt phải có trần (`max_steps`, mặc định ví dụ 6); ca hiển nhiên đi fast-path 0 thêm bước.
- **NFR-2 (Async/throughput)**: không còn blocking call trên event loop; tool I/O dùng async client; checkpointer async hoặc Postgres.
- **NFR-3 (Quan sát được)**: audit mọi tool-call (đã có khung) + ghi token/cost mỗi bước (hiện `InvokeUsage()` rỗng — phải điền).
- **NFR-4 (An toàn)**: guard là bất biến ở Harness, không phụ thuộc vị trí trong graph; loop không thể chạy vô hạn.
- **NFR-5 (Tương thích)**: SSE event contract (`progress|delta|delta_full|chart|draft|inventory_draft|data_table|clarify|error|done`) giữ nguyên cho FE/Spring relay.
- **NFR-6 (Rollback)**: tắt cờ Strangler → trở về 100% graph tuyến tính, không cần deploy lại.

---

## 6. Phạm vi & Lớp ảnh hưởng (Scope / Affected Layers)

**Trong phạm vi (v1):**
- `app/harness/**` (mới: orchestrator, tool_registry, policy, scratchpad)
- Tool adapters cho: `sql_query`, `schema_explore`, `catalog_draft`, `inventory_draft`
- `app/api/runtime.py`, `app/api/routes.py` — wiring loop + async + SSE giữ contract
- `app/graph/state.py` — tách state; `app/graph/checkpointing.py` — async/PG
- `app/llm/openai_compatible.py`, `app/graph/sql_executor.py` — async client
- Cấu hình mới trong `app/config/graph_settings.py` (cờ Strangler, budget)

**Ngoài phạm vi (v1):**
- `build_chart`, `erp_guide` lên tool (để v2)
- Thay LLM provider / model
- Thay đổi Spring backend hay schema DB
- Sửa frontend (chỉ phải đảm bảo SSE không đổi)

**Ràng buộc AGENTS.md**: giai đoạn SRS/Tech/QA là docs-only — **không sửa runtime `ai_python`**. Việc sửa code chỉ thực hiện ở CODING_AGENT sau khi docs duyệt, và vì đây đúng là "production AI code", scope agent được phép theo điều 131 AGENTS.md (giữ tách biệt LangGraph/Harness/tools).

---

## 7. Owner Decisions (đã chốt)

| ID | Quyết định | Lựa chọn | Ghi chú |
| :-- | :-- | :-- | :-- |
| OD-1 | Mô hình loop | **Harness-native loop** | LangGraph = tool implementation |
| OD-2 | Migration | **Strangler** | Graph cũ làm fallback, cờ cấu hình |
| OD-3 | Async | **Async ngay đợt này** | Tránh rework 2 lần |
| OD-4 | Tool v1 | **sql_query, schema_explore, catalog_draft, inventory_draft** | chart/erp_guide để v2; chat = fast-path |

### 7.1 Quyết định còn mở (cần chốt ở Tech Spec)
- **OD-5**: Provider cho "next-action decision" — dùng tool-calling/function-calling native của model hiện tại, hay JSON-structured decision qua `structured_invoke`? (ảnh hưởng độ tin cậy parse.)
- **OD-6**: Checkpointer async — `AsyncSqliteSaver` hay chuyển sang Postgres checkpointer (DB đã có sẵn)?
- **OD-7**: `max_steps`/`max_tool_calls` mặc định cụ thể + hành vi khi chạm trần (trả lời best-effort hay báo lỗi).

---

## 8. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
| :-- | :-- | :-- |
| Loop tăng chi phí/độ trễ LLM | Cao | `max_steps`, fast-path, cache decision khi ca hiển nhiên |
| Guardrail rò khi đổi từ vị trí-graph sang harness | Cao | Guard bắt buộc trên mọi tool-call; test P0 cho read-only + tenant |
| Vỡ HITL/SSE khi rời interrupt LangGraph | Cao | Strangler giữ luồng cũ; test contract SSE trước khi route sang loop |
| Rewrite async chạm nhiều file | Trung bình | Làm theo lát cắt; tool adapter trước, async sau, có fallback |
| God-state refactor gây regression | Trung bình | Tách dần, giữ adapter tương thích checkpoint cũ |

---

## 9. Acceptance Criteria

- **AC-1**: Với cờ Strangler bật cho intent data-query, một câu hỏi cần `schema_explore` rồi `sql_query` được giải bằng chuỗi tool tự động, không hardcode edge, trả `final_answer` đúng.
- **AC-2**: Tắt cờ Strangler → hành vi giống hệt graph tuyến tính hiện tại (regression pass).
- **AC-3**: Mọi tool-call đi qua Harness guard; SQL ghi (DELETE/UPDATE/INSERT) bị chặn 100% kể cả khi LLM cố gọi.
- **AC-4**: HITL catalog/inventory phát đúng SSE `draft`/`inventory_draft` và nhận lại `clarification_response`, kết quả giống luồng cũ.
- **AC-5**: Loop không vượt `max_steps`; có log token/cost mỗi bước; không có blocking call trên event loop (đo bằng test async).
- **AC-6**: SSE event contract không đổi — FE hiện tại chạy không sửa.

---

## 10. Open Questions
- Decision provider (OD-5), checkpointer async (OD-6), trần loop (OD-7) — chuyển sang Tech Spec.
- Có cần "tool retry budget" riêng từng tool không, hay budget toàn cục đủ?
- Cách biểu diễn observation của tool kết quả lớn (bảng SQL nhiều dòng) trong scratchpad để không nổ context — tóm tắt hay tham chiếu?

---

## 11. Handoff
- **Next stage**: `TECH_SPEC_WRITER` — thiết kế contract tool, `HarnessOrchestrator`, policy/guard, async wiring, lát cắt Strangler, chốt OD-5/6/7.
- **Readiness**: READY_FOR_TECH_SPEC (4 Owner Decisions cốt lõi đã chốt; 3 quyết định kỹ thuật còn mở không chặn việc lập Tech Spec).
