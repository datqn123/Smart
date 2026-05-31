# Cách thêm intent mới (REG-03)

> Track: `ai_python` — đồng bộ Task 2 LG-07 + Task 3 REG-hardening.

## Checklist

1. Thêm literal vào enum `IntentLabel` trong `ai_python/app/llm/schemas.py` (ví dụ: `chart_report`).
2. Cập nhật `INTENT_HANDLERS_V1` trong `ai_python/app/graph/registry.py` map intent → tên node trong main graph.
3. Cập nhật `normalize_intent` để route literal mới (nếu cần fallback đặc biệt).
4. Implement node mới trong `ai_python/app/graph/nodes/` và `add_node` ở `main_graph.py`.
5. Cập nhật `route_after_intent` nếu cần literal mới (đồng bộ tên node).
6. Thêm test trong `ai_python/tests/` cho intent + route + node mới.
7. Cập nhật prompt `intent` (`ai_python/app/graph/nodes/intent.py`) nếu cần few-shot mới.

## Quy tắc unknown intent

- Mặc định fallback `general_chat` (D5 trong PRD Task 3).
- KHÔNG raise — luôn route được.

## Cập nhật doc/PRD

- Thêm vào DESIGN nếu intent thuộc roadmap (`ai_python/TASKS/DESIGN/`).
- Cập nhật registry table trong `intent_registry_howto.md` này.
- **FR-CTX-01:** bảng state vs `config["configurable"]` — xem [`task003/01-scope/CTX_state_vs_configurable.md`](task003/01-scope/CTX_state_vs_configurable.md).
