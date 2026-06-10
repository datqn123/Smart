# Agentic Tools Reference Design

**Date**: 2026-06-10
**Status**: Approved
**Scope**: Tạo tài liệu reference cho tất cả tools trong ai_python agentic system + cơ chế auto-update qua opencode instructions

---

## 1. Mục tiêu

- Document đầy đủ 10 tools đang hoạt động trong hệ thống agentic
- Mỗi tool có 1 file riêng tại `docs/reference/ai-knowledge/tools/`
- Tạo file `index.md` tổng hợp tất cả tools
- Cập nhật `.opencode/instructions.md` với rule: mọi thay đổi code → phải cập nhật reference

## 2. Scope

### Included
- **Tool registry**: 10 tools với capabilities, side effects, HITL flags
- **Tool ↔ Harness integration**: cách tools làm việc với orchestrator, plan executor, observation contract
- **Tool ↔ LangGraph integration**: tools/subgraphs nào dùng ở node nào
- **Prompt files**: mapping tool → prompt file (nếu có)
- **Input/Output schemas**: Pydantic models, ObservationEnvelope structure
- **Error handling**: retry, degrade, HITL pause mechanisms

### Excluded
- LangGraph nodes không phải tool (intent, planner, domain_guard, context_compact, chat_normal, summarize)
- Subagent internals (IntentSubagent, PlannerSubagent, CompactSubagent) — chỉ document khi liên quan đến tool invocation
- Legacy code không còn sử dụng

## 3. File Structure

```
docs/reference/ai-knowledge/tools/
├── index.md                    # Tổng hợp: bảng tất cả tools + metadata nhanh
├── sql_query.md                # SqlQueryTool + SelfCorrectingSqlRunner
├── schema_explore.md           # SchemaExploreTool
├── catalog_draft.md            # CatalogDraftTool
├── inventory_draft.md          # InventoryDraftTool
├── answer_composer.md          # AnswerComposerTool
├── build_chart.md              # BuildChartTool
├── data_table_builder.md       # DataTableBuilderTool
├── data_validator.md           # DataValidatorTool
└── erp_guide.md                # ErpGuideTool (RAG over ERP docs)
```

### index.md Content

**Bảng tổng hợp 10 tools**:

| Tool | Capability | Side Effect | HITL | Source | Prompt |
|------|-----------|-------------|------|--------|--------|
| sql_query | data_read | read_only | No | `tools/sql_query.py` | — |
| schema_explore | data_read | read_only | No | `tools/schema_explore.py` | — |
| catalog_draft | data_write | non_idempotent_write | Yes | `tools/catalog_draft.py` | `agents/catalog_draft.md` |
| inventory_draft | data_write | non_idempotent_write | Yes | `tools/inventory_draft.py` | `agents/inventory_draft.md` |
| answer_composer | answer | read_only | No | `tools/answer_composer.py` | — |
| build_chart | visualization | read_only | No | `tools/build_chart.py` | `agents/chart.md` |
| data_table_builder | visualization | read_only | No | `tools/data_table_builder.py` | — |
| data_validator | validation | read_only | No | `tools/data_validator.py` | — |
| erp_guide | knowledge | read_only | No | `tools/erp_guide.py` | — |

**Runtime mapping**:
- **Harness tools**: sql_query, schema_explore, catalog_draft, inventory_draft, answer_composer, build_chart, data_table_builder, data_validator, erp_guide (tất cả 9 tools đều đăng ký trong ToolRegistry)
- **LangGraph tools**: sql_query (dùng trong sql_subgraph nodes), catalog_draft (dùng trong catalog_draft_subgraph), inventory_draft (dùng trong inventory_draft_subgraph)

## 4. Tool File Template

Mỗi file tool sẽ có cấu trúc:

```markdown
# <Tool Name>

> Source: `ai_python/app/graph/tools/<file>.py`
> Prompt: `ai_python/app/prompts/agents/<file>.md` (nếu có)

## Overview
Mô tả ngắn 2-3 dòng: tool làm gì, khi nào được gọi.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `sql_query` |
| capability | `data_read` |
| side_effect | `read_only` |
| hitl_required | `false` |
| idempotent | `true` |
| timeout_s | `30` |
| max_retries | `0` |
| ... | ... |

## Input Schema
Pydantic model hoặc JSON Schema — các field tool nhận vào.

## Output / Observation
ObservationEnvelope structure — tool trả về gì cho Planner/Graph.

## Runtime Integration

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Replan trigger: khi nào tool fail → Planner quyết định replan/stop/degrade

### LangGraph (Legacy)
- Subgraph: `sql_subgraph` / `catalog_draft_subgraph` / `inventory_draft_subgraph`
- Node: `gen_sql`, `sql_review`, `validate_sql`, `execute_sql` (ví dụ)
- Conditional routing: khi nào graph rẽ nhánh vào tool này

## Error Handling
Các lỗi có thể xảy ra + cách xử lý (retry, degrade, HITL pause).

## Example
Input/output example ngắn gọn.
```

## 5. Auto-Update Mechanism

### Rule trong `.opencode/instructions.md`

Thêm section mới:

```markdown
## Quy tắc cập nhật reference khi code thay đổi

Khi bạn thay đổi code trong `ai_python/`:

1. **Tool thay đổi** (thêm/sửa/xóa tool trong `app/graph/tools/` hoặc `app/harness/tool_registry.py`):
   - Cập nhật file tương ứng trong `docs/reference/ai-knowledge/tools/`
   - Nếu thêm tool mới: tạo file mới + cập nhật `index.md`
   - Nếu xóa tool: xóa file + cập nhật `index.md`

2. **Prompt thay đổi** (sửa file trong `app/prompts/agents/`):
   - Cập nhật section "Prompt" trong file tool tương ứng

3. **Graph structure thay đổi** (sửa `app/graph/main_graph.py`, `app/graph/sql_subgraph.py`, v.v.):
   - Cập nhật section "LangGraph (Legacy)" trong file tool tương ứng

4. **Harness integration thay đổi** (sửa `app/harness/orchestrator.py`, `app/harness/plan_graph.py`):
   - Cập nhật section "Harness (v3.0)" trong file tool tương ứng

Mọi conversation đều PHẢI tuân thủ rule này. Không được bỏ qua.
```

### Enforcement

- Rule nằm trong `.opencode/instructions.md` → tất cả agents (opencode, Claude Code, Codex) đều đọc và tuân thủ
- Không cần git hook hay CI/CD — rule được enforce bởi agent khi làm việc
- User có thể review changes trong PR để đảm bảo compliance

## 6. Implementation Steps

1. **Tạo thư mục** `docs/reference/ai-knowledge/tools/`
2. **Đọc source code** từng tool để extract thông tin:
   - `app/harness/tool_registry.py` → ToolManifest definitions
   - `app/graph/tools/*.py` → Tool implementations (input/output schemas, error handling)
   - `app/prompts/load.py` → Prompt file mapping
   - `app/graph/main_graph.py`, `app/graph/sql_subgraph.py`, v.v. → LangGraph node mapping
   - `app/harness/orchestrator.py`, `app/harness/plan_graph.py` → Harness integration
3. **Viết 10 file tool** theo template
4. **Viết index.md** với bảng tổng hợp + runtime mapping
5. **Cập nhật `.opencode/instructions.md`** với rule auto-update
6. **Commit tất cả**

## 7. Success Criteria

- [ ] 10 file tool đầy đủ thông tin theo template
- [ ] index.md có bảng tổng hợp + runtime mapping
- [ ] `.opencode/instructions.md` có rule auto-update
- [ ] Tất cả files được commit
- [ ] Agent có thể đọc reference để hiểu tool mà không cần đọc source code

## 8. Out of Scope

- Tự động generate docs từ source code (script) — không làm trong task này
- Document LangGraph nodes không phải tool
- Document subagent internals (IntentSubagent, PlannerSubagent, CompactSubagent)
- Migration docs cũ từ `docs/dev/` hoặc `docs/archive/`

---

**End of Spec**
