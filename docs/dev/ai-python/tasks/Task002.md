# Task002 — LangGraph foundation + SQL subgraph (PRD FINAL)

**SRS:** `docs/ai-python/srs/SRS_AI_Task002_langgraph-gemma4-task2.md`  
**PRD:** `docs/ai-python/prd/PRD_langgraph-gemma4-task2.md`  
**ADR:** `docs/ai-python/adr/ADR-002-langgraph-gemma4-task2-graph.md`  
**Artifact folder:** `docs/ai-python/task002/`

## Definition of Done

- [x] BA✓ — SRS Approved  
- [x] TL✓ — ADR ghi NFR 5 mục  
- [x] DEV✓ — Code + pytest pass  
- [x] CR✓ — `docs/task002/05-code-review/CODE_REVIEW_Task002.md` verdict PASS  

**Tuỳ chọn pre-release:** AI_TESTER / AI_BRIDGE.

## Checklist triển khai

- [x] LG-01…03 — deps, package `app/graph`, `AgentState`  
- [x] LG-04…07 — main graph + registry + routing  
- [x] LG-08…11 — SQL subgraph + retry + fail_max  
- [x] LG-12…14 — checkpointer factory, stream hook, mask SQL + correlation context  
- [x] SqlExecutor Option C + env `.env.example`  
- [x] Tests routing + retry cap + validate_sql  
