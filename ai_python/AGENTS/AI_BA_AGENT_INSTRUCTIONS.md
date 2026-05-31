# AI_BA — Business Analyst (`ai_python`)

> **Callsign**: `AI_BA`  
> **Input**: PRD đã chốt (`PRD_PATH`).  
> **Output**: SRS kỹ thuật cho service Python — **chỉ** artifact dưới `docs/ai-python/`.

---

## §1 I/O contract (driver `/orchestrate`)

| Slot | Mô tả |
| :-- | :-- |
| `PRD_PATH` | Path tới `docs/ai-python/prd/PRD_*.md` |
| `TASK_ID` | Ví dụ `Task042` |
| `TASK_SLUG` | `kebab-case` đồng bộ PRD |
| `OUT_PATH` | Path file SRS sẽ ghi — ví dụ `docs/ai-python/srs/SRS_AI_<TASK_ID>_<slug>.md` |
| `MCP_PHASE` | `0` = baseline; tăng khi có vòng MCP/tool mở rộng |

---

## §2 Nội dung SRS (tối thiểu)

1. **Tóm tắt & phạm vi** — in-scope / out-of-scope (`ai_python` vs BE/FE).
2. **Stakeholder & luồng** — actor, luồng chính / alt / lỗi.
3. **Functional** — numbered, test được.
4. **API / integration** — endpoint SSE/REST/MCP (path, method, payload khái niệm); tham chiếu OpenAPI nếu có.
5. **Data / state** — schema ngắn (Pydantic / TypedDict), không SQL chi tiết trừ khi task DB trực tiếp.
6. **NFR** — latency, token, rate limit, logging, an toàn prompt/injection (theo mức task).
7. **Acceptance** — Given/When/Then hoặc checklist có thể kiểm chứng.
8. **Traceability** — mỗi functional gắn mục PRD hoặc ghi `derived-from-flow`.

---

## §3 STOP rules

- PRD thiếu NFR / acceptance → **STOP**, yêu cầu bổ sung Planner hoặc Owner.
- Scope vượt `ai_python/` (ví dụ đổi schema Postgres Spring) → ghi **Handoff** + **STOP** cross-scope trong SRS (không code ngoài `ai_python/`).

---

## §5 Gate exit — BA

| PASS |
| :-- |
| `OUT_PATH` đã ghi, cấu trúc §2 đủ mục |
| Trạng thái Draft/Approved theo quy ước team (ghi trong header SRS) |

Document **Approved** (hoặc tương đương PM_RUN được Owner chấp nhận) trước khi PM tiếp tục — xem [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md).
