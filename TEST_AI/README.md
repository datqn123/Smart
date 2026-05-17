# TEST_AI — Bộ Test Tự Động AI Chat (Smart ERP)

## Cấu trúc

| Thư mục | Số câu | Mô tả |
|---------|-------:|-------|
| `01_general_chat/` | 7 | Hội thoại thông thường |
| `02_inventory/` | 7 | Truy vấn tồn kho |
| `03_stock_receipts/` | 7 | Phiếu nhập kho |
| `04_sales_orders/` | 11 | Đơn hàng bán |
| `05_finance_ledger/` | 8 | Sổ cái tài chính |
| `06_stock_dispatches/` | 4 | Phiếu xuất kho |
| `07_customers_debts/` | 5 | Khách hàng & công nợ |
| `08_products_categories/` | 4 | Sản phẩm & danh mục |
| `09_suppliers/` | 3 | Nhà cung cấp |
| `10_inventory_audit/` | 3 | Kiểm kê kho |
| `11_vouchers/` | 3 | Voucher & khuyến mãi |
| `12_charts/` | 10 | Yêu cầu biểu đồ |
| `13_multi_turn/` | 10 | Đa luồng hội thoại (5 cặp) |
| `14_edge_cases/` | 6 | Lỗi & edge cases |
| **Tổng** | **88** | |

## Cách sử dụng

1. Mỗi file `.md` là một test case độc lập
2. Điền kết quả vào phần **Response từ AI** sau khi chạy
3. Tick các mục trong phần **Kiểm tra**
4. Cập nhật trạng thái: ⬜ Chưa / ✅ Pass / ❌ Fail / ⚠️ Partial
5. Xem tổng hợp tại `SUMMARY.md`

## Yêu cầu trước khi test

- PostgreSQL đang chạy
- Spring Boot (`smart-erp`) trên `http://127.0.0.1:8080`
- Python FastAPI (`ai_python`) trên `http://127.0.0.1:9000`
- Tài khoản login có quyền `can_use_ai`

## Kiến trúc luồng test

```
Browser/Script → POST /api/v1/auth/login (Spring 8080)
               → JWT Bearer token
               → POST /api/v1/ai/chat/stream (Spring 8080)
               → SSE relay → Python FastAPI (9000)
               → LangGraph → SSE response
               → Parse: delta, done, error, chart
```
