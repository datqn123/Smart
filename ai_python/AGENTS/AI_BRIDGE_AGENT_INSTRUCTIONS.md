# AI_BRIDGE — API / contract bridge (`ai_python`)

> **Không** là bước trong **`/orchestrate` lean** — xem [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) §0.3.

## Khi chạy

- Đổi contract giữa FastAPI `ai_python` và consumer (Spring `smart-erp`, `mini-erp`, MCP/SSE).
- Sau khi endpoint hoặc schema payload đổi — verify drift với tài liệu chung.

## Tham chiếu chéo repo

- [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md)
- [`docs/frontend/api/`](../../docs/frontend/api/) — nếu task yêu cầu file bridge FE, **handoff** rõ — agent bridge trong điều phối FE/BE có thể đảm nhiệm file ngoài `ai_python/`.

## Output gợi ý trong `ai_python`

- `docs/ai-python/api/bridge/BRIDGE_AI_<task>_<slug>.md` — mô tả mapping, sample request/response, version.

## STOP

- Drift cần sửa Java/React → ghi handoff; không tự sửa ngoài scope Owner.
