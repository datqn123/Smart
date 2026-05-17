# CODE_REVIEW — Task003 (LangGraph Gemma4 Task3 Agents)

**Iteration:** 2  
**Reviewer role:** `AI_CODE_REVIEWER`  
**Scope:** `ai_python/` only  
**Inputs:** SRS Task003, ADR-003, `ai_python/TASKS/Task003.md`  
**Tiền trình:** Iteration 1 verdict **BLOCK** (B1 thiếu allowlist cột; B2 gen_sql vẫn LLM khi schema load fail; M1/m1/…). Iteration 2 DEV sửa — CR re-verify.

**Verifier:** `pytest -q tests/` từ `ai_python/` (`.venv`) — **38 passed** (2026-05-10).

---

## 1. Verdict

**PASS**

---

## 2. Tóm tắt (3–7 bullet)

- **B1 ✓:** `validate_sql_deterministic` nhận `table_columns: dict[str, set[str]] | None`; sqlparse + `_collect_column_identifiers` / alias map; `SchemaArtifact.allowlist_columns_map()` trong `dbmeta.py`; `make_validate_sql_node` truyền map từ artifact. Tests: `test_validate_sql_blocks_unknown_column`, `allows_known_column`, `allows_star_select`, `qualified_column` (gồm `SELECT customers.id FROM customers`).
- **B2 ✓:** `gen_sql` return sớm với `error_payload.error == "schema_load_failed"` **trước** `invoke_text` sql_gen; `sql_subgraph` dùng `route_after_gen_sql` → `fail_max_attempts`; `test_gen_sql_early_fails_on_schema_load_error` assert `sql_gen.invoke_count == 0`.
- **M1 ✓:** `setup_correlation_logging()` gắn `CorrelationFilter` lên **handlers** của root logger; các node graph có `logger.info("node=… action=start")`; `test_node_logs_include_correlation_id` + `correlation_scope` pass.
- **m1 ✓:** `docs/task003/01-scope/CTX_state_vs_configurable.md` có bảng field vs state/config, tham chiếu Task 2 **LG-03.4**; `Task003.md` tick CTX cite `[x]`.
- **m2 ✓:** `test_graph.py` parametrize `UPDATE` / `DELETE` / `ALTER` / `TRUNCATE` → `validate_sql_deterministic` fail.
- **n1 ✓:** `summarize.py` empty branch dùng wording **"Không có dữ liệu phù hợp với câu hỏi của bạn."** (align SRS hơn iter 1).
- **Caveat (MINOR, không chặn PASS):** heuristic cột/alias như DEV ghi — acceptable cho acceptance “common case”; `validate_sql` nếu `load` artifact lỗi **tại node validate** thì fallback `table_columns=None` (lỏng hơn một bước) — hiếm khi xảy ra sau gen_sql thành công.

---

## 3. Findings

### BLOCK

*(Không có.)*

### MAJOR

*(Không có.)*

### MINOR

| ID | Mô tả | File:line (tham chiếu) |
| :-- | :-- | :-- |
| m1 | `make_validate_sql_node`: nếu `schema_loader.load` raise trong validate, `table_columns`/`allowlist` = `None` — validation lỏng hơn so với khi có artifact (đường hạnh phúc sau B2 vẫn an toàn). | `sql_pipeline.py` ~148–155 |
| m2 | `setup_correlation_logging()` chỉ attach cho handlers **đã** gắn root tại lúc gọi — môi trường không qua `main.py` lifespan cần tự gọi (như test); đồng bộ với caveat DEV. | `correlation.py` 46–55; `main.py` 12–16 |
| m3 | FR-CTX doc: nêu LG-03.4; có thể bổ sung link path file Task 2 SRS nếu muốn traceability tuyệt đối. | `CTX_state_vs_configurable.md` |

### NIT

| ID | Mô tả |
| :-- | :-- |
| n1 | `gen_sql` gọi `bump_attempts(state)` trước khi load schema; trên nhánh `schema_load_failed` giá trị `bumped` không dùng — vô hại, hơi thừa một bước. |
| n2 | `Task003.md` DoD dòng TL✓ vẫn `[ ]` — tiến trình PM/TL, không phải defect code CR. |

---

## 4. Khớp SRS / ADR — checklist (post iter 2)

| Mục | Trạng thái | Ghi chú |
| :-- | :-- | :-- |
| FR-AG-01..08 | Pass | 8 node; intent/chat/sql path + tests. |
| FR-AG-05 (cột) | Pass | `table_columns` + tests qualified/unqualified/`*`. |
| FR-DBM-02 (fail không LLM) | Pass | Early-fail gen_sql + route + `invoke_count == 0`. |
| FR-DBM-03 | Pass | Cùng artifact → map bảng/cột cho validate + gen prompt. |
| FR-CTX-01 | Pass | Doc CTX + checklist tick. |
| NFR-OBS-01 | Pass | Filter trên handlers + `logger.info` node + test caplog. |
| NFR-SEC-01 / SEC-02 | Pass | Topology giữ; `ChatOpenAI` không có trong `app/graph/`. |
| NFR-REL-01/02, FR-SUM-01, FR-REG-01, NFR-INJ-01 | Pass | Tests iter 1 + iter 2; không regression (38 tests). |
| ADR-003 §3 | Pass | Giữ sqlparse, LIMIT hybrid, SCHEMA_DIR, extras, layout. |

---

## 5. Hành động (BLOCK)

*(Không áp dụng — verdict PASS.)*

Tùy chọn sau merge: xử lý nit `bump_attempts` ordering; siết fallback `validate_sql` khi load artifact fail (m1).

---

**Kết thúc §2 theo `AI_CODE_REVIEWER_AGENT_INSTRUCTIONS.md` (iteration 2).**
