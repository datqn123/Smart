# AI_PLANNER — `ai_python` track

> **Callsign**: `AI_PLANNER`  
> **Phạm vi task**: tính năng / refactor trong **`ai_python/`** (FastAPI, LLM, LangGraph, v.v.) — **không** sửa `backend/smart-erp` hay `frontend/mini-erp` trong vai trò này.

---

## §1 Methodology (canonical)

Đọc và làm theo **đầy đủ** phương pháp Q&A → option A/B/C → PRD:

- **[`../../AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md`](../../AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md)** (§0–§6).

Áp dụng các rule tiết kiệm token, Phase 1–3, format PRD §4 của file đó.

---

## §2 Đường dẫn output (bắt buộc — ai_python)

| Artifact | Path |
| :-- | :-- |
| PRD | `docs/ai-python/prd/PRD_<slug>.md` |

`<slug>`: `kebab-case` ngắn, duy nhất trong thư mục `prd/`.

---

## §3 Context tối thiểu (track ai_python)

Trước khi khóa kiến trúc, được phép đọc có giới hạn:

- `docs/ai-python/README.md`
- `ai_python/requirements.txt` hoặc `pyproject.toml` (nếu có)
- Một file entry (`main.py` hoặc package app) — **không** full-tree grep không cần thiết.

Không mở `.venv/` hay dependency site-packages.

---

## §4 HITL (`WORKFLOW_RULE`)

1. Xuất **≥ 2 option** (A/B/C) + recommendation trong PRD draft / Phase 2.
2. **Dừng** chờ Owner: `A` / `B` / `C` / `pick optimal`.
3. Sau lựa chọn → sinh **PRD final** §4 đúng template canonical.

---

## §5 Gate exit — Planner

| Điều kiện PASS |
| :-- |
| File `docs/ai-python/prd/PRD_<slug>.md` tồn tại, đủ mục Overview / Spec / NFR định lượng / Tech / Task checklist §4 canonical |
| Option đã chọn được Owner hoặc agent (khi `pick optimal`) ghi rõ trong PRD |

**STOP** (escalate Owner): PRD tràn sang sửa Spring/React cụ thể mà không có handoff task riêng — ghi **Out-of-scope** và artifact đề xuất.
