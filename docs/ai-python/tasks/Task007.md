# Task007 — Agent SQL Factory (SQL-Factory–Lite Upgrade)

**SRS:** `d:\do_an_tot_nghiep\project\ai_python\docs\srs\SRS_AI_Task007_agent-sql-factory-upgrade.md`  
**Artifact folder:** `d:\do_an_tot_nghiep\project\ai_python\docs\task007\`

## Goal

- Nâng nhánh SQL theo kiểu **SQL-Factory–lite (Option B)**: chọn subset bảng có giới hạn (heuristic-first, tuỳ chọn LLM structured), nhánh prompt **explore / exploit**, **hybrid similarity** (SimTok + SimAST; SimEmb tuỳ chọn) trên pool SQL cục bộ có cap, và làm giàu schema với **PK, FK**, **`TableMeta.description`** khi có — toàn bộ **tuỳ chọn** qua `GraphSettings` / env, **parity Task006** khi tắt flag; **HTTP-first** merge mô tả bảng (consumer Python; contract Spring/handoff **TBD**).

## Definition of Done

- [x] BA✓ — SRS Task007 approved for PM (`Approved for PM`); scope, Option B locked, acceptance §7 và traceability khớp PRD.
- [x] TL✓ — ADR-006; graph/state/settings/similarity; HTTP merge consumer **TBD** (handoff Spring).
- [x] DEV✓ — Code `ai_python/` + `.env.example`; pytest Task007 + regression graph/agents.
- [x] CR✓ — `docs/task007/05-code-review/CODE_REVIEW_Task007.md` (PASS).

**Tuỳ chọn pre-release:** AI_TESTER / AI_BRIDGE khi cần kiểm tra release hoặc chốt contract HTTP Spring/handoff.

## Checklist triển khai (aligned SRS Task007)

### Phase 1 — Schema text, PK/FK, descriptions merge (consumer)

- [ ] FR-SRS-001 — Khối schema trong SQL generation gồm PK/FK và `TableMeta.description` khi đã populate; không fail chỉ vì thiếu descriptions.
- [ ] FR-SRS-009 + §4 Integration — Bounded merge **`table → description`** (YAML baseline + conceptual Spring HTTP refresh); không embed connection strings; lỗi HTTP/source missing non-fatal (kèm NFR-SRS-104).

### Phase 2 — Bounded table selection & fallbacks

- [ ] FR-SRS-002, FR-SRS-003 — `selected_tables` cap (mặc định ≤8 configurable); heuristic-first; optional structured LLM khi gate rules cho phép và tuân NFR-SRS-102.
- [ ] FR-SRS-004 — Fallback full schema / Task006 khi selection fail, tắt, hoặc artifact nhỏ; không orphan references trong prompts.

### Phase 3 — Explore / exploit prompting & deterministic policy

- [ ] FR-SRS-005 — Attempt 1 exploration; retries hợp lệ → exploitation có seed SQL length-capped + allowlist chỉ **`selected_tables`**.
- [ ] FR-SRS-007, FR-SRS-008 — Hook redundancy sau `gen_sql`; state machine không vượt `can_regen_sql` / max attempts Task006; không management LLM riêng.

### Phase 4 — Hybrid similarity & local pool

- [ ] FR-SRS-006 — Pool per-turn/thread cap (mặc định ≤32); hybrid SimTok + SimAST (`sqlparse`); optional SimEmb + weights (FR-SRS-010) behind flag.

### Phase 5 — Configuration, subgraph order, AgentState extensions

- [ ] FR-SRS-010 + §5.2 `GraphSettings` / env — Toggles selection, similarity, exploit, descriptions HTTP/YAML, optional `select_tables` vs monolithic `gen_sql`; roles LLM map thiếu → **`default`**.
- [ ] FR-SRS-012 — Thứ tự subgraph: `gen_sql → sql_review → validate_sql → execute_sql → validate_result`; chỉ chèn **linear** `select_tables` trước `gen_sql` nếu bật.
- [ ] FR-SRS-013 — Mở rộng `AgentState` keys optional `total=False` (`selected_tables`, `sql_gen_mode`, `sql_attempt_history` hoặc tương đương); checkpoint cũ không `KeyError`.

### Phase 6 — Parity, tests, NFR & acceptance gate

- [ ] FR-SRS-011 + NFR-SRS-101 — Mọi flag mới default **off**: latency incremental “negligible”, hành vi ≈ Task006 (stub baseline theo cấu hình).
- [ ] FR8 / `general_chat` — Không đụng SQL similarity/selection paths (SRS §2.3, acceptance §7.1).
- [ ] NFR-SRS-102..106 — Cap budget, no crash trên missing metadata/HTTP, không log secrets, diagnostic trace an toàn.
- [ ] NFR-SRS-107 + SRS §7.1 — Pytest: similarity golden pairs, policy 1→2, allowlist, regression flags-off, checkpoint merge, description present/absent; CI green.
