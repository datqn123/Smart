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

Phần sau tiêu đề `## JSON output contract` = ràng buộc JSON (giữ trong cùng file).

Quy tắc **deterministic** (allowlist, enum case, CTE, retry) vẫn nằm trong code Python — không duplicate dài trong MD.
