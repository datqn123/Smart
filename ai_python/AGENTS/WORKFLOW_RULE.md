# WORKFLOW_RULE — chuỗi Agent `ai_python` (FastAPI / AI service)

> **Source of truth** cho điều phối trong thư mục **`ai_python/`** — đọc cùng [`AGENT_REGISTRY.md`](AGENT_REGISTRY.md).
>
> **Lệnh Cursor**: `/.cursor/commands/orchestrate.md` — **chuỗi mặc định (lean)** không gồm Tester / Bridge / Doc Sync / Orchestrator final.

---

## §0 Phạm vi & ranh giới

| Quy tắc | Nội dung |
| :-- | :-- |
| Code & doc artifact | Chỉ dưới **`ai_python/`** — không sửa `backend/` hay `frontend/` trừ khi Owner / contract rõ ràng yêu cầu (handoff tách biệt). |
| Driver `/orchestrate` | Không dùng git; không branch/commit; chỉ Task tool + file artifact. |
| HITL Planner | Chỉ tại **AI_PLANNER**: chọn option **A / B / C** hoặc **`pick optimal`** sau khi có PRD draft — không HITL ở gate khác trong lean. |

---

## §0.1 Chuỗi mặc định (lean) — `/orchestrate`

Thứ tự **bắt buộc** cho một task feature trong `ai_python`:

```
AI_PLANNER → AI_BA → AI_PM → AI_TECH_LEAD → AI_DEVELOPER → AI_CODE_REVIEWER
```

| Gate | Agent | Artifact chính |
| :-- | :-- | :-- |
| G-AI-PLAN | `AI_PLANNER` | `docs/ai-python/prd/PRD_<slug>.md` |
| G-AI-BA | `AI_BA` | `docs/ai-python/srs/SRS_AI_<task>_<slug>.md` (hoặc quy ước tương đương trong SRS instruction) |
| G-AI-PM | `AI_PM` | `docs/ai-python/tasks/Task<XXX>.md` + `docs/ai-python/task<XXX>/` |
| G-AI-TL | `AI_TECH_LEAD` | `docs/ai-python/adr/ADR-<NNN>-<slug>.md` |
| G-AI-DEV | `AI_DEVELOPER` | `ai_python/app/**` (hoặc cấu trúc app hiện có) + tests |
| G-AI-CR | `AI_CODE_REVIEWER` | `docs/ai-python/task<XXX>/05-code-review/CODE_REVIEW_<task>.md` |

**Kết thúc lean**: báo cáo Code Review verdict **PASS**.

---

## §0.2 Vòng lặp duy nhất (DEV ↔ CR)

- Nếu **CODE_REVIEWER** verdict **BLOCK** (hoặc tương đương): relaunch **AI_DEVELOPER** với `LOOP_FEEDBACK` = path báo cáo CR — tối đa **3** vòng (đếm `loop_count.cr`), sau đó **STOP** escalate Owner.

---

## §0.3 Chuỗi mở rộng (không chạy trong `/orchestrate` lean)

Chạy **chủ động** khi task đòi hỏi hoặc trước release — **không** gắn mặc định vào lean để tránh eval/test kéo dài.

| Agent | Khi nào |
| :-- | :-- |
| `AI_BRIDGE` | Đổi contract SSE/OpenAPI/MCP giữa `ai_python` ↔ Spring/FE — verify drift; có thể handoff ngoài `ai_python/`. |
| `AI_TESTER` | Eval tự động / red-team / scenario — **tốn thời gian**; định kỳ hoặc pre-merge. |
| `AI_DOC_SYNC` | Đồng bộ SRS/PRD/README sau khi code ổn định. |
| `AI_ORCHESTRATOR` | Audit tổng hợp task — WARN/FAIL xử lý theo instruction. |

Chi tiết từng role: file `*_AGENT_INSTRUCTIONS.md` trong thư mục này.

---

## §1 Prompt mẫu cho Owner

```text
/orchestrate Brief="..." 
```

```text
WORKFLOW_RULE ai_python — đọc @ai_python/AGENTS/WORKFLOW_RULE.md — tiếp tục từ PM với SRS path ...
```

---

## §2 Đồng bộ với repo gốc

- **AI_PLANNER** toàn repo (methodology PRD): có thể tham chiếu [`../../AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md`](../../AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md); output **task ai_python** vẫn tuân path trong `docs/ai-python/prd/`.
