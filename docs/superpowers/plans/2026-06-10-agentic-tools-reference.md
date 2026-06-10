# Agentic Tools Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tạo tài liệu reference đầy đủ cho 10 tools trong ai_python agentic system + cơ chế auto-update qua opencode instructions

**Architecture:** Mỗi tool có 1 file markdown riêng tại `docs/reference/ai-knowledge/tools/` theo template chuẩn. File `index.md` tổng hợp tất cả tools với bảng metadata + runtime mapping. Rule trong `.opencode/instructions.md` enforce auto-update khi code thay đổi.

**Tech Stack:** Markdown documentation, Python source code reading, Git

---

## File Structure

```
docs/reference/ai-knowledge/tools/
├── index.md                    # Tổng hợp: bảng tất cả tools + metadata
├── sql_query.md                # SqlQueryTool + SelfCorrectingSqlRunner
├── schema_explore.md           # SchemaExploreTool
├── catalog_draft.md            # CatalogDraftTool
├── inventory_draft.md          # InventoryDraftTool
├── answer_composer.md          # AnswerComposerTool
├── build_chart.md              # BuildChartTool
├── data_table_builder.md       # DataTableBuilderTool
├── data_validator.md           # DataValidatorTool
└── erp_guide.md                # ErpGuideTool (RAG over ERP docs)

.opencode/instructions.md       # Thêm section: Quy tắc cập nhật reference khi code thay đổi
```

---

### Task 1: Setup & Read Tool Registry

**Files:**
- Create: `docs/reference/ai-knowledge/tools/` (directory)
- Read: `ai_python/app/harness/tool_registry.py`

- [ ] **Step 1: Create tools directory**

```bash
mkdir docs/reference/ai-knowledge/tools
```

- [ ] **Step 2: Read tool_registry.py to understand ToolManifest structure**

Read file: `ai_python/app/harness/tool_registry.py`

Extract:
- ToolManifest dataclass fields (name, capability, side_effect, hitl_required, idempotent, timeout_s, max_retries, etc.)
- ToolRegistry class methods
- How tools are registered

- [ ] **Step 3: Read all tool source files to understand structure**

Read files:
- `ai_python/app/graph/tools/sql_query.py`
- `ai_python/app/graph/tools/schema_explore.py`
- `ai_python/app/graph/tools/catalog_draft.py`
- `ai_python/app/graph/tools/inventory_draft.py`
- `ai_python/app/graph/tools/answer_composer.py`
- `ai_python/app/graph/tools/build_chart.py`
- `ai_python/app/graph/tools/data_table_builder.py`
- `ai_python/app/graph/tools/data_validator.py`
- `ai_python/app/graph/tools/erp_guide.py`

For each tool, note:
- Tool class name and function signature
- Input schema (Pydantic model)
- Output/Observation structure
- Error handling logic
- Prompt file reference (if any)

- [ ] **Step 4: Read LangGraph integration points**

Read files:
- `ai_python/app/graph/main_graph.py` (main graph structure)
- `ai_python/app/graph/sql_subgraph.py` (SQL pipeline nodes)
- `ai_python/app/graph/catalog_draft_subgraph.py` (catalog draft nodes)
- `ai_python/app/graph/inventory_draft_subgraph.py` (inventory draft nodes)

For each subgraph, note which tools are called in which nodes.

- [ ] **Step 5: Read Harness integration points**

Read files:
- `ai_python/app/harness/orchestrator.py` (HarnessOrchestrator)
- `ai_python/app/harness/plan_graph.py` (PlanExecutor, PlanGraph)

Note how PlanExecutor calls tools via ToolRegistry and how ObservationEnvelope wraps results.

- [ ] **Step 6: Read prompt loader**

Read file: `ai_python/app/prompts/load.py`

Understand how prompts are loaded and which tools have associated prompt files.

- [ ] **Step 7: Commit setup notes**

```bash
git add docs/reference/ai-knowledge/tools/
git commit -m "docs: create tools reference directory"
```

---

### Task 2: Write sql_query.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/sql_query.md`

- [ ] **Step 1: Extract sql_query tool information**

From source code reading, extract:
- **Overview**: SqlQueryTool executes SQL queries with self-correction. SelfCorrectingSqlRunner wraps it with retry logic.
- **Manifest**: capability=data_read, side_effect=read_only, hitl_required=false, idempotent=true
- **Input Schema**: SQL query string, optional parameters
- **Output**: ObservationEnvelope with query results (bounded sample + result_ref)
- **Harness Integration**: Called by PlanExecutor as tool node in PlanGraph
- **LangGraph Integration**: Used in sql_subgraph nodes: gen_sql, sql_review, validate_sql, execute_sql
- **Error Handling**: Self-correction loop (max 3 attempts), SQL validation, safety checks
- **Prompt**: None (tool doesn't use prompt file)

- [ ] **Step 2: Write sql_query.md**

```markdown
# SqlQueryTool

> Source: `ai_python/app/graph/tools/sql_query.py`
> Prompt: — (tool doesn't use prompt file)

## Overview
SqlQueryTool executes SQL queries against the ERP database with safety validation. SelfCorrectingSqlRunner wraps it with automatic retry logic for SQL generation/review/execution loops.

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

## Input Schema
```python
class SqlQueryInput(BaseModel):
    query: str  # SQL query string
    # ... other fields from source
```

## Output / Observation
Returns ObservationEnvelope with:
- `sample`: First N rows (bounded)
- `row_count`: Total row count
- `columns`: Column names
- `result_ref`: Opaque handle to full result set

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Replan trigger: SQL execution failure → Planner decides replan/stop/degrade

### LangGraph (Legacy)
- Subgraph: `sql_subgraph`
- Nodes: `gen_sql`, `sql_review`, `validate_sql`, `execute_sql`
- Self-correction loop: gen_sql ↔ sql_review ↔ validate_sql (max 3 attempts)

## Error Handling
- SQL validation errors: Return error observation, trigger replan
- Execution timeout: Raise TimeoutError, caught by harness
- Safety policy violations: Blocked by K5 allowlist check

## Example
Input:
```json
{
  "query": "SELECT * FROM products LIMIT 10"
}
```

Output:
```json
{
  "sample": [{"id": 1, "name": "Product A"}, ...],
  "row_count": 10,
  "columns": ["id", "name", ...],
  "result_ref": "ref_abc123"
}
```
```

- [ ] **Step 3: Commit sql_query.md**

```bash
git add docs/reference/ai-knowledge/tools/sql_query.md
git commit -m "docs: add sql_query tool reference"
```

---

### Task 3: Write schema_explore.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/schema_explore.md`

- [ ] **Step 1: Extract schema_explore tool information**

From source code, extract:
- **Overview**: SchemaExploreTool explores database schema (tables, columns, relationships)
- **Manifest**: capability=data_read, side_effect=read_only, hitl_required=false
- **Input Schema**: Table name or pattern to explore
- **Output**: Schema information (columns, types, foreign keys)
- **Harness Integration**: Called by PlanExecutor for schema discovery
- **LangGraph Integration**: Used in sql_subgraph node: schema_explore
- **Error Handling**: Table not found, permission denied
- **Prompt**: None

- [ ] **Step 2: Write schema_explore.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/schema_explore.md
git commit -m "docs: add schema_explore tool reference"
```

---

### Task 4: Write catalog_draft.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/catalog_draft.md`

- [ ] **Step 1: Extract catalog_draft tool information**

From source code, extract:
- **Overview**: CatalogDraftTool generates master data drafts (products, categories, suppliers, customers)
- **Manifest**: capability=data_write, side_effect=non_idempotent_write, hitl_required=true
- **Input Schema**: Draft type, entity data
- **Output**: Draft ID, validation status
- **Harness Integration**: HITL pause before persist
- **LangGraph Integration**: Used in catalog_draft_subgraph nodes
- **Error Handling**: Validation errors, duplicate detection
- **Prompt**: `agents/catalog_draft.md`

- [ ] **Step 2: Write catalog_draft.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/catalog_draft.md
git commit -m "docs: add catalog_draft tool reference"
```

---

### Task 5: Write inventory_draft.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/inventory_draft.md`

- [ ] **Step 1: Extract inventory_draft tool information**

From source code, extract:
- **Overview**: InventoryDraftTool generates transaction document drafts (stock receipts, dispatches)
- **Manifest**: capability=data_write, side_effect=non_idempotent_write, hitl_required=true
- **Input Schema**: Document type, item data
- **Output**: Draft ID, validation status
- **Harness Integration**: HITL pause before persist
- **LangGraph Integration**: Used in inventory_draft_subgraph nodes
- **Error Handling**: Validation errors, insufficient stock
- **Prompt**: `agents/inventory_draft.md`

- [ ] **Step 2: Write inventory_draft.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/inventory_draft.md
git commit -m "docs: add inventory_draft tool reference"
```

---

### Task 6: Write answer_composer.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/answer_composer.md`

- [ ] **Step 1: Extract answer_composer tool information**

From source code, extract:
- **Overview**: AnswerComposerTool composes final answer from observations
- **Manifest**: capability=answer, side_effect=read_only, hitl_required=false
- **Input Schema**: Observations, context
- **Output**: Composed answer text
- **Harness Integration**: Final answer generation
- **LangGraph Integration**: Used in summarize node
- **Error Handling**: Missing observations
- **Prompt**: None (uses internal template)

- [ ] **Step 2: Write answer_composer.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/answer_composer.md
git commit -m "docs: add answer_composer tool reference"
```

---

### Task 7: Write build_chart.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/build_chart.md`

- [ ] **Step 1: Extract build_chart tool information**

From source code, extract:
- **Overview**: BuildChartTool generates chart specifications from data
- **Manifest**: capability=visualization, side_effect=read_only, hitl_required=false
- **Input Schema**: Data, chart type, configuration
- **Output**: Chart specification (JSON)
- **Harness Integration**: Called by PlanExecutor for visualization
- **LangGraph Integration**: Used in chart_report node
- **Error Handling**: Invalid chart type, data format errors
- **Prompt**: `agents/chart.md`

- [ ] **Step 2: Write build_chart.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/build_chart.md
git commit -m "docs: add build_chart tool reference"
```

---

### Task 8: Write data_table_builder.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/data_table_builder.md`

- [ ] **Step 1: Extract data_table_builder tool information**

From source code, extract:
- **Overview**: DataTableBuilderTool builds data tables for display
- **Manifest**: capability=visualization, side_effect=read_only, hitl_required=false
- **Input Schema**: Data, column configuration
- **Output**: Table specification
- **Harness Integration**: Called by PlanExecutor for tabular display
- **LangGraph Integration**: Used in query_table node
- **Error Handling**: Data format errors
- **Prompt**: None

- [ ] **Step 2: Write data_table_builder.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/data_table_builder.md
git commit -m "docs: add data_table_builder tool reference"
```

---

### Task 9: Write data_validator.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/data_validator.md`

- [ ] **Step 1: Extract data_validator tool information**

From source code, extract:
- **Overview**: DataValidatorTool validates data against business rules
- **Manifest**: capability=validation, side_effect=read_only, hitl_required=false
- **Input Schema**: Data to validate, validation rules
- **Output**: Validation results (pass/fail, errors)
- **Harness Integration**: Pre-write validation
- **LangGraph Integration**: Used in validate_result node
- **Error Handling**: Validation failures
- **Prompt**: None

- [ ] **Step 2: Write data_validator.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/data_validator.md
git commit -m "docs: add data_validator tool reference"
```

---

### Task 10: Write erp_guide.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/erp_guide.md`

- [ ] **Step 1: Extract erp_guide tool information**

From source code, extract:
- **Overview**: ErpGuideTool provides RAG-based ERP knowledge retrieval
- **Manifest**: capability=knowledge, side_effect=read_only, hitl_required=false
- **Input Schema**: Query string
- **Output**: Relevant guide chunks
- **Harness Integration**: Knowledge retrieval
- **LangGraph Integration**: Not used in legacy graph
- **Error Handling**: No relevant chunks found
- **Prompt**: None (uses RAG pipeline)

- [ ] **Step 2: Write erp_guide.md**

Follow template structure from Task 2.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/ai-knowledge/tools/erp_guide.md
git commit -m "docs: add erp_guide tool reference"
```

---

### Task 11: Write index.md

**Files:**
- Create: `docs/reference/ai-knowledge/tools/index.md`

- [ ] **Step 1: Write index.md with tool summary table**

```markdown
# Agentic Tools Reference

> This directory contains reference documentation for all tools in the ai_python agentic system.

## Tool Summary

| Tool | Capability | Side Effect | HITL | Source | Prompt |
|------|-----------|-------------|------|--------|--------|
| [sql_query](sql_query.md) | data_read | read_only | No | `tools/sql_query.py` | — |
| [schema_explore](schema_explore.md) | data_read | read_only | No | `tools/schema_explore.py` | — |
| [catalog_draft](catalog_draft.md) | data_write | non_idempotent_write | Yes | `tools/catalog_draft.py` | `agents/catalog_draft.md` |
| [inventory_draft](inventory_draft.md) | data_write | non_idempotent_write | Yes | `tools/inventory_draft.py` | `agents/inventory_draft.md` |
| [answer_composer](answer_composer.md) | answer | read_only | No | `tools/answer_composer.py` | — |
| [build_chart](build_chart.md) | visualization | read_only | No | `tools/build_chart.py` | `agents/chart.md` |
| [data_table_builder](data_table_builder.md) | visualization | read_only | No | `tools/data_table_builder.py` | — |
| [data_validator](data_validator.md) | validation | read_only | No | `tools/data_validator.py` | — |
| [erp_guide](erp_guide.md) | knowledge | read_only | No | `tools/erp_guide.py` | — |

## Runtime Mapping

### Harness (v3.0)
All 9 tools are registered in `ToolRegistry` and called by `PlanExecutor` via the agentic loop:
- sql_query, schema_explore, catalog_draft, inventory_draft, answer_composer, build_chart, data_table_builder, data_validator, erp_guide

### LangGraph (Legacy)
Tools used in deterministic graph nodes:
- **sql_subgraph**: sql_query (gen_sql, sql_review, validate_sql, execute_sql nodes), schema_explore
- **catalog_draft_subgraph**: catalog_draft
- **inventory_draft_subgraph**: inventory_draft

## Auto-Update Rule

When you change code in `ai_python/`, you MUST update the corresponding tool reference file. See `.opencode/instructions.md` for details.
```

- [ ] **Step 2: Commit index.md**

```bash
git add docs/reference/ai-knowledge/tools/index.md
git commit -m "docs: add tools reference index"
```

---

### Task 12: Update .opencode/instructions.md

**Files:**
- Modify: `.opencode/instructions.md`

- [ ] **Step 1: Add auto-update rule section**

Add the following section to `.opencode/instructions.md` after the existing "Khi bạn thay đổi codebase" section:

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

- [ ] **Step 2: Commit instructions update**

```bash
git add .opencode/instructions.md
git commit -m "docs: add auto-update rule for tool references"
```

---

### Task 13: Final Review & Commit

- [ ] **Step 1: Verify all files created**

```bash
ls docs/reference/ai-knowledge/tools/
```

Expected output:
```
index.md
sql_query.md
schema_explore.md
catalog_draft.md
inventory_draft.md
answer_composer.md
build_chart.md
data_table_builder.md
data_validator.md
erp_guide.md
```

- [ ] **Step 2: Verify .opencode/instructions.md updated**

```bash
grep -A 5 "Quy tắc cập nhật reference" .opencode/instructions.md
```

Expected: Should show the new auto-update rule section.

- [ ] **Step 3: Final commit (if any remaining changes)**

```bash
git status
git add .
git commit -m "docs: complete agentic tools reference documentation"
```

---

## Success Criteria

- [ ] 10 tool files created with complete information
- [ ] index.md has summary table + runtime mapping
- [ ] .opencode/instructions.md has auto-update rule
- [ ] All files committed to git
- [ ] Agent can read reference to understand tools without reading source code

---

**End of Plan**
