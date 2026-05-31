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

1. Sửa `test_config.json` với email/password thật của bạn
2. Chạy lệnh test (xem bảng lệnh bên dưới)
3. Kết quả tự động ghi vào từng file `.md`
4. Xem tổng hợp tại `SUMMARY.md`

## Lệnh chạy test

### Chạy theo phạm vi

| Lệnh | Mô tả |
|------|--------|
| `python run_test.py --all` | Chạy toàn bộ 88 câu hỏi |
| `python run_test.py --group 01_general_chat` | Chạy nhóm hội thoại thông thường (7 câu) |
| `python run_test.py --group 02_inventory` | Chạy nhóm tồn kho (7 câu) |
| `python run_test.py --group 03_stock_receipts` | Chạy nhóm phiếu nhập kho (7 câu) |
| `python run_test.py --group 04_sales_orders` | Chạy nhóm đơn hàng bán (11 câu) |
| `python run_test.py --group 05_finance_ledger` | Chạy nhóm sổ cái tài chính (8 câu) |
| `python run_test.py --group 06_stock_dispatches` | Chạy nhóm xuất kho (4 câu) |
| `python run_test.py --group 07_customers_debts` | Chạy nhóm khách hàng & công nợ (5 câu) |
| `python run_test.py --group 08_products_categories` | Chạy nhóm sản phẩm & danh mục (4 câu) |
| `python run_test.py --group 09_suppliers` | Chạy nhóm nhà cung cấp (3 câu) |
| `python run_test.py --group 10_inventory_audit` | Chạy nhóm kiểm kê kho (3 câu) |
| `python run_test.py --group 11_vouchers` | Chạy nhóm voucher (3 câu) |
| `python run_test.py --group 12_charts` | Chạy nhóm biểu đồ (10 câu) |
| `python run_test.py --group 13_multi_turn` | Chạy nhóm đa luồng (10 câu) |
| `python run_test.py --group 14_edge_cases` | Chạy nhóm edge cases (6 câu) |

### Chạy từng câu hỏi

| Lệnh | Mô tả |
|------|--------|
| `python run_test.py --q 1` | Chạy câu Q1 — Chào hỏi |
| `python run_test.py --q 8` | Chạy câu Q8 — Low stock |
| `python run_test.py --q 15` | Chạy câu Q15 — Phiếu pending |
| `python run_test.py --q 22` | Chạy câu Q22 — Đơn bán sỉ |
| `python run_test.py --q 33` | Chạy câu Q33 — SalesRevenue |
| `python run_test.py --q 41` | Chạy câu Q41 — Delivered |
| `python run_test.py --q 45` | Chạy câu Q45 — Khách nhiều đơn |
| `python run_test.py --q 50` | Chạy câu Q50 — SP đồ uống |
| `python run_test.py --q 54` | Chạy câu Q54 — Nhập gần nhất |
| `python run_test.py --q 57` | Chạy câu Q57 — In Progress |
| `python run_test.py --q 60` | Chạy câu Q60 — Voucher active |
| `python run_test.py --q 63` | Chạy câu Q63 — Biểu đồ doanh thu |
| `python run_test.py --q 64` | Chạy câu Q64 — Biểu đồ so sánh kênh |
| `python run_test.py --q 65` | Chạy câu Q65 — Biểu đồ tròn chi phí |
| `python run_test.py --q 66` | Chạy câu Q66 — Biểu đồ tồn kho |
| `python run_test.py --q 67` | Chạy câu Q67 — Biểu đồ DT vs CP |
| `python run_test.py --q 68` | Chạy câu Q68 — Biểu đồ phiếu nhập |
| `python run_test.py --q 69` | Chạy câu Q69 — Biểu đồ công nợ |
| `python run_test.py --q 70` | Chạy câu Q70 — Biểu đồ đơn theo kênh |
| `python run_test.py --q 71` | Chạy câu Q71 — Biểu đồ trạng thái tồn |
| `python run_test.py --q 72` | Chạy câu Q72 — Biểu đồ doanh thu quỹ |
| `python run_test.py --q 73a` | Chạy câu Q73a — Doanh thu tháng 3 |
| `python run_test.py --q 73b` | Chạy câu Q73b — Tháng 4 (tiếp) |
| `python run_test.py --q 78` | Chạy câu Q78 — Bảng không tồn tại |
| `python run_test.py --q 81` | Chạy câu Q81 — SQL injection |

### Lệnh tiện ích

| Lệnh | Mô tả |
|------|--------|
| `python run_test.py --dry-run --all` | Xem danh sách 88 câu hỏi, không gọi API |
| `python run_test.py --dry-run --group 12_charts` | Xem câu hỏi nhóm biểu đồ |
| `python run_test.py --help` | Xem hướng dẫn sử dụng |
| `python run_test.py --config path/to/config.json` | Dùng file config tùy chỉnh |

## Cấu hình

Sửa `test_config.json` trước khi chạy:

```json
{
  "spring_base_url": "http://127.0.0.1:8080",
  "python_base_url": "http://127.0.0.1:9000",
  "login_email": "admin@smartinventory.vn",
  "login_password": "admin123",
  "test_ai_dir": "D:\\do_an_tot_nghiep\\project\\TEST_AI",
  "timeout_per_question_seconds": 120,
  "save_response_to_file": true
}
```

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
               → Parse: delta, done, error, chart, draft, data_table
               → Ghi kết quả vào file .md
```

## Chế độ tương tác (Task111)

Trên UI chat Mini ERP, chọn chip trước khi gửi câu hỏi:

| Chip | `interactionMode` | Kỳ vọng |
|------|-------------------|---------|
| Tự động | `auto` | AI tự phân loại |
| Hỏi dữ liệu | `data_query` | Text tóm tắt SQL |
| Bảng kết quả | `data_table` | Text ngắn + SSE `data_table` |
| Biểu đồ | `chart` | SSE `chart` |
| Tạo bảng nhập | `catalog_draft` | SSE `draft` |

Ví dụ thủ công: chọn **Bảng kết quả**, gửi *"Hiển thị danh sách sản phẩm gần hết hạn"* — phải thấy bảng read-only dưới bubble assistant (không chỉ bullet text).

API: `frontend/docs/api/API_Task111_ai_chat_interaction_mode.md`

**Domain guard (Task112):** Mọi câu qua `domain_guard` trước intent. Ví dụ: *"phiếu xuất khẩu"* → SSE `clarify` + gợi ý *phiếu xuất kho*. Doc: `frontend/docs/api/API_Task112_erp_domain_guard.md`

## Kết quả test

- Mỗi file `.md` trong thư mục con được cập nhật tự động với:
  - **Response từ AI** (trả lời + chart_spec nếu có)
  - **Thời gian phản hồi** (ms)
  - **Trạng thái** (✅ Pass / ❌ Fail / ⚠️ Partial)
- `SUMMARY.md` được cập nhật thống kê tổng hợp
