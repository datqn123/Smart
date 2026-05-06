# Design_Agent

Thư mục chung chứa tài liệu thiết kế AI Agent cho dự án Mini-ERP (Spring + React + Python sidecar / LangGraph).

## Tài liệu trong thư mục

| File | Mô tả |
|------|--------|
| [CHAT_AGENT_DESIGN.md](CHAT_AGENT_DESIGN.md) | Thiết kế Chat Agent: topology, 4 năng lực (bảng / chart / nhập-xuất kho / Excel), SSE events, tools, acceptance, rủi ro. |

## Bản plan Cursor (đồng bộ IDE)

Các bản plan đầy đủ MUST / SHOULD còn nằm trong workspace Cursor (có YAML todos cho tracking):

- `ai-agent-deepseek-mini-erp_d72a55d7.plan.md` — **MUST** (M-01 … M-09)
- `ai-agent-should-mini-erp_a1b2c3d4.plan.md` — **SHOULD + DREAM**

Khi cần đưa vào repo, có thể copy nội dung (bỏ frontmatter YAML) vào thư mục này với tên `AI_AGENT_MUST_PLAN.md` / `AI_AGENT_SHOULD_PLAN.md`.

## Nguyên tắc chung

- Chat Agent là **router + renderer + gateway**; mutation luôn qua Write sub-agent + **human-in-the-loop** (`interrupt()`).
- Generative UI: `TableSpec`, `ChartSpec`, `FileDownloadSpec`, `ExcelPreviewSpec` — FE render, không eval HTML từ LLM.
