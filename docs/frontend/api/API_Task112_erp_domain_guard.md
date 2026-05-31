# API Task112 — ERP Domain Guard (scope & terminology)

## Flow

Every chat turn: `domain_guard` → (clarify | reject | proceed) → `classify_intent` → …

## SSE event `clarify`

Emitted when domain guard needs user confirmation before SQL/draft/chart.

```json
{
  "questions": ["Bạn có muốn nói đến phiếu xuất kho (Stock Dispatch) không?"],
  "issues": [
    {
      "type": "term_mismatch",
      "user_text": "phiếu xuất khẩu",
      "canonical_vi": "phiếu xuất kho",
      "canonical_en": "Stock Dispatch",
      "severity": "block"
    }
  ],
  "guideRefs": ["§5"],
  "originalQuestion": "Vẽ biểu đồ đơn hàng nhập khẩu từng tháng...",
  "suggestedRewrite": "Vẽ biểu đồ thể hiện phiếu nhập kho từng tháng từ đầu năm 2026 tới hiện tại",
  "suggestedNormalized": "(same as suggestedRewrite)"
  "matchedModules": ["inventory"]
}
```

Then `delta` streams `assistant_message` text.

## Configuration (Python)

| Env / setting | Default | Description |
|---------------|---------|-------------|
| `erp_domain_guard_enabled` | `true` | Toggle guard node |
| `erp_guide_retrieve_max_chunks` | `3` | RAG chunks per turn |
| `erp_guide_data_dir` | package `app/data/erp` | Index + chunks path |

## Rebuild index from GUID

```bash
cd ai_python
python scripts/build_erp_domain_index.py
```

Source: repo root `GUID_ERP.md`.
