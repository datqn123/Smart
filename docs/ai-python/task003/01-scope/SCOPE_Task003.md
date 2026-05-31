# Scope — Task003 (Agents v1 / LangGraph + Gemma 4)

**Tham chiếu:** `ai_python/docs/srs/SRS_AI_Task003_langgraph-gemma4-task3-agents.md` (Approved) · PRD: `ai_python/docs/prd/PRD_langgraph-gemma4-task3-agents.md`

Tài liệu này tóm tắt phạm vi và phụ thuộc; chi tiết FR/NFR/acceptance xem SRS.

---

## In-scope

- Thay stub nodes **Task002** bằng hành vi Agent v1: `intent`, `chat_normal`, `gen_sql`, `sql_review`, `validate_sql`, `execute_sql`, `validate_result`, `summarize_answer`.
- **Option C (đã khóa):** fixture YAML + `SchemaLoader` Protocol; feedback bucket structured (`intent_review`, `policy`, `exec`, `result`, `attempts`, `extras?`); `execute_sql` chỉ qua **stub** (`SqlExecutor`).
- **DBM:** artifact schema YAML, `FileSchemaLoader`, allowlist dùng chung cho prompt `gen_sql` và kiểm `validate_sql` (không drift nguồn).
- **Registry:** unknown intent → `general_chat`; bổ sung tài liệu how-to thêm intent (theo SRS).
- **CTX:** bảng cite vị trí đọc field từ `state` vs `config["configurable"]` (tham chiếu Task002 `LG-03.4`), không đổi topology.
- **Kiểm thử:** fake LLM theo node, retry cap 3, empty result không retry, unknown intent, coverage node mới ≥ 85% (theo NFR SRS).

---

## Out-of-scope

- FastAPI route Task 3, HTTP/SSE, JWT / gateway Spring.
- QA E2E Task 4, multimodal LM-05, distributed checkpointer, CLI scanner.
- Thực thi `python_ro` / `http_spring` cho `SqlExecutor`.
- Sửa `backend/` hoặc `frontend/` (drift contract → handoff bridge nếu phát sinh).

---

## Phụ thuộc Task001 + Task002

| Nguồn | Task003 tái sử dụng / mở rộng |
| :-- | :-- |
| **Task001** | Port LLM: chỉ gọi qua `get_llm_client(role)`; không tạo client trực tiếp ngoài `app/llm/*`. |
| **Task002** | Graph SQL subgraph, retry/fail_max, `AgentState`, checkpointer hook, `SqlExecutor` (stub), correlation/logging patterns (`LG-03.4`). Task003 migrate cẩn trọng `validation_feedback` sang shape structured nếu scaffold hiện là `list[str]`. |

---

## API / tích hợp (trong Python — §4 SRS)

- Contract LLM: `invoke` / `stream` / structured output tương đương scaffold hiện có; nodes dùng `get_llm_client`.
- Contract executor: `SqlExecutor.execute` — chỉ **stub** trong Task003.
- Schema: `SchemaLoader.load(schema_version) -> SchemaArtifact`; YAML khuyến nghị `app/data/schema/<schema_version>.yaml`.
- Config/state: `schema_version`, `locale` (mặc định `vi-VN`), `correlation_id`, `tenant_id`, `thread_id` theo bảng CTX trong SRS §5.

---

## File / module dự kiến (DEV)

| Khu vực | Ghi chú |
| :-- | :-- |
| `app/graph/nodes/*.py` | Thay stub bằng logic Agent; routing/registry hardening. |
| `app/graph/dbmeta.py` hoặc module tương đương | Meta schema / loader wiring (tên chốt khi implement). |
| `app/data/schema/*.yaml` | Fixture artifact theo FR-DBM-01. |
| `app/graph/sql_executor.py` (hoặc đã có Task002) | Giữ port; chỉ dùng mode stub. |
| `tests/*` | Unit per node (fake LLM), graph retry/empty/unknown intent, coverage `app.graph.nodes`. |
| `ai_python/docs/intent_registry_howto.md` | Checklist thêm intent (FR-REG). |

---

*Tóm tắt có chủ đích; traceability đầy đủ: SRS §8.*
