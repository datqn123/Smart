# ErpGuideTool

> Source: `ai_python/app/graph/tools/erp_guide.py`
> Prompt: —

## Tổng quan
Cung cấp nội dung hướng dẫn ERP tiếng Việt dựa trên so khớp từ khóa chủ đề. Logic routing đơn giản, không gọi LLM — trả về hướng dẫn định sẵn cho chủ đề kho, tài chính, hoặc chung.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `erp_guide` |
| capability | `erp_guide` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("guidance",)` |
| consumes | — |
| result_ref_policy | — |
| examples | — |

## Schema đầu vào
```json
{
  "topic": "string"
}
```

## Đầu ra / Quan sát
```json
{
  "topic": "inventory",
  "guide": "Hướng dẫn quản lý kho: Nhập kho, xuất kho, kiểm kê..."
}
```
Quan sát: Nội dung hướng dẫn ERP tiếng Việt (so khớp từ khóa: inventory/kho, finance/doanh thu, hoặc chung).

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Tra cứu kiến thức cho hướng dẫn ERP

### LangGraph (Legacy)
- Không dùng trong legacy graph

## Xử lý lỗi
- Luôn trả về `ok=True`
- Routing từ khóa đơn giản — không có kịch bản lỗi

## Ví dụ
**Đầu vào:**
```json
{
  "topic": "kho"
}
```
**Đầu ra:**
```json
{
  "topic": "inventory",
  "guide": "Hướng dẫn quản lý kho: Nhập kho, xuất kho, kiểm kê, điều chuyển kho. Các chứng từ cần thiết: phiếu nhập kho, phiếu xuất kho, biên bản kiểm kê."
}
```
Quan sát: `"Hướng dẫn quản lý kho: Nhập kho, xuất kho, kiểm kê..."`
