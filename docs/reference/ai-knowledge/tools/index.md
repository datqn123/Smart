# Agentic Tools Reference

> Thư mục này chứa tài liệu tham khảo cho tất cả tools trong hệ thống agentic ai_python.

## Bảng tổng hợp Tools

| Tool | Capability | Side Effect | HITL | Source | Prompt |
|------|-----------|-------------|------|--------|--------|
| [sql_query](sql_query.md) | data_read | read_only | Không | `tools/sql_query.py` | gen_sql.md, sql_review.md, verify_sql_intent.md, analyze_empty_result.md, schema_explore.md |
| [schema_explore](schema_explore.md) | data_read | read_only | Không | `tools/schema_explore.py` | schema_explore.md |
| [catalog_draft](catalog_draft.md) | draft_create | non_idempotent_write | Có | `tools/catalog_draft.py` | catalog_draft.md + 6 entity playbooks |
| [inventory_draft](inventory_draft.md) | draft_create | non_idempotent_write | Có | `tools/inventory_draft.py` | inventory_draft.md + 4 doc playbooks |
| [answer_composer](answer_composer.md) | answer_compose | read_only | Không | `tools/answer_composer.py` | — |
| [build_chart](build_chart.md) | chart_build | read_only | Không | `tools/build_chart.py` | — |
| [data_table_builder](data_table_builder.md) | data_table_build | read_only | Không | `tools/data_table_builder.py` | — |
| [data_validator](data_validator.md) | data_validate | read_only | Không | `tools/data_validator.py` | — |
| [erp_guide](erp_guide.md) | erp_guide | read_only | Không | `tools/erp_guide.py` | — |

## Runtime Mapping

### Harness (v3.0)
Cả 9 tools đều được đăng ký trong `ToolRegistry` và gọi bởi `PlanExecutor` qua agentic loop:
- sql_query, schema_explore, catalog_draft, inventory_draft, answer_composer, build_chart, data_table_builder, data_validator, erp_guide

### LangGraph (Legacy)
Tools dùng trong deterministic graph nodes:
- **sql_subgraph**: sql_query (các node gen_sql, sql_review, validate_sql, execute_sql), schema_explore
- **catalog_draft_subgraph**: catalog_draft
- **inventory_draft_subgraph**: inventory_draft

## Quy tắc Auto-Update

Khi bạn thay đổi code trong `ai_python/`, bạn PHẢI cập nhật file tool reference tương ứng. Xem `.opencode/instructions.md` để biết chi tiết.
