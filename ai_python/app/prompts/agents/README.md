# Runtime agent playbooks (LangGraph)

Mỗi file `.md` = **system prompt** cho một node LLM trong graph. Code load qua `app.prompts.load.load_agent_prompt(<id>)`.

| File | Node graph | Registry key (LLM) |
|------|------------|-------------------|
| `intent.md` | `classify_intent` | `intent` |
| `chat_normal.md` | `chat_normal` | `chat` |
| `summarize.md` | `summarize_answer` | `summarize` |
| `idea.md` | `agent_idea` | `idea` |
| `gen_sql.md` | `gen_sql` | `sql_gen` |
| `sql_review.md` | `sql_review` | `sql_review` |
| `schema_explore.md` | `schema_explore` | (schema planner) |
| `sql_table_pick.md` | (table selection) | `sql_table_pick` |
| `chart_readiness.md` | `chart_readiness` | `chart_critic` |
| `chart.md` | `agent_chart` | `chart` |
| `chart_review.md` | `agent_review` | `review` |
| `catalog_entity_pick.md` | `classify_catalog_entity` | `catalog_entity` |
| `catalog_draft.md` | `generate_catalog_draft` (base) | `catalog_draft` |
| `catalog_draft_product.md` | (playbook, nối runtime) | — |
| `catalog_draft_category.md` | (playbook, nối runtime) | — |
| `catalog_draft_supplier.md` | (playbook, nối runtime) | — |
| `catalog_draft_customer.md` | (playbook, nối runtime) | — |

**Catalog draft:** node `generate_catalog_draft` **không** gọi `load_agent_prompt("catalog_draft")` trực tiếp — dùng `load_catalog_draft_system_prompt(entity_type)` để ghép base + playbook entity.

Phần sau tiêu đề `## JSON output contract` = ràng buộc JSON (giữ trong cùng file; chỉ `catalog_draft.md` cho nhánh catalog).

Quy tắc **deterministic** (allowlist, enum case, CTE, retry) vẫn nằm trong code Python — không duplicate dài trong MD.
