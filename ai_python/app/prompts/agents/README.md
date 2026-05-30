# Runtime agent playbooks (LangGraph)

Each `.md` file = **system prompt** for one LLM node in the graph. Loaded via `app.prompts.load.load_agent_prompt(<id>)`.

## Global language policy (chatbot output)

- Nội dung trả về cho người dùng cuối phải là **tiếng Việt thuần**.
- Không trộn tiếng Anh trong câu trả lời, trừ tên riêng hoặc mã định danh dữ liệu bắt buộc hiển thị.
- Thuật ngữ kỹ thuật phải được diễn đạt bằng tiếng Việt dễ hiểu theo ngữ cảnh nghiệp vụ ERP.

| File | Graph node | Registry key (LLM) |
|------|------------|-------------------|
| `intent.md` | `classify_intent` | `intent` |
| `planner.md` | `agent_planner` | `planner` |
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
| `catalog_entity_pick.md` | (legacy; see `catalog_draft_slots`) | — |
| `catalog_draft_slots.md` | `classify_catalog_entity`, `resolve_catalog_draft` | `intent` |
| `catalog_draft.md` | `generate_catalog_draft` (base) | `catalog_draft` |
| `catalog_draft_product.md` | (playbook, appended at runtime) | — |
| `catalog_draft_category.md` | (playbook, appended at runtime) | — |
| `catalog_draft_supplier.md` | (playbook, appended at runtime) | — |
| `catalog_draft_customer.md` | (playbook, appended at runtime) | — |

**Catalog draft:** the `generate_catalog_draft` node does **not** call `load_agent_prompt("catalog_draft")` directly — it uses `load_catalog_draft_system_prompt(entity_type)` to concatenate the base prompt + the entity-specific playbook.

| `inventory_entity_pick.md` | (legacy; see `inventory_draft_slots`) | — |
| `inventory_draft_slots.md` | `classify_inventory_doc`, `resolve_inventory_draft` | `intent` |
| `inventory_draft.md` | `generate_inventory_draft` (base) | — |
| `inventory_draft_stock_receipt.md` | (playbook, appended at runtime) | — |

**Inventory draft:** use `load_inventory_draft_system_prompt(doc_type)`; SSE event `inventory_draft`. Commit creates one `stock_receipt` (Draft/Pending only in v1).

Everything after the `## JSON output contract` heading = JSON constraints (kept in the same file; `catalog_draft.md` / `inventory_draft.md` for JSON contracts).

**Deterministic** rules (allowlists, enum casing, CTEs, retries) remain in the Python code — not duplicated at length in MD.
