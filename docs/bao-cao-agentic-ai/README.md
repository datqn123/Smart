# Báo cáo kỹ thuật: Kỹ nghệ ngữ cảnh (Context Engineering) trong hệ Agentic AI cho ERP

Bộ tài liệu trình bày quá trình phát hiện — chẩn đoán — khắc phục các lớp lỗi
của trợ lý AI truy vấn dữ liệu ERP (module `ai_python`), và đối chiếu phương
pháp với cách các phòng lab lớn (Anthropic, OpenAI) vận hành hệ thống LLM
trong sản xuất.

## Mục lục

| # | Tài liệu | Nội dung chính |
|---|----------|----------------|
| 1 | [01-kien-truc-he-thong.md](01-kien-truc-he-thong.md) | Kiến trúc pipeline agent, vai trò từng thành phần |
| 2 | [02-cac-ca-loi-va-nguyen-nhan-goc.md](02-cac-ca-loi-va-nguyen-nhan-goc.md) | 4 ca lỗi thực tế: hiện tượng → chẩn đoán → nguyên nhân gốc → bài học |
| 3 | [03-phuong-phap-khac-phuc.md](03-phuong-phap-khac-phuc.md) | Nguyên tắc sửa tại nguồn, phân tầng code/prompt, self-check, thinking log |
| 4 | [04-doi-chieu-cach-lam-cua-cac-lab-lon.md](04-doi-chieu-cach-lam-cua-cac-lab-lon.md) | Vá prompt có bền không? Anthropic/OpenAI làm gì khác? |
| 5 | [05-entity-grounding-va-bai-toan-quy-mo.md](05-entity-grounding-va-bai-toan-quy-mo.md) | Grounding theo DB; xử lý khi bảng master có hàng triệu bản ghi |
| 6 | [06-lo-trinh-de-xuat.md](06-lo-trinh-de-xuat.md) | Bộ eval câu hỏi vàng, unaccent, policy rows=0, nâng cấp model |

## Cách dùng khi trình bày

- Trình tự 2 → 3 → 4 kể được câu chuyện hoàn chỉnh: *lỗi thực tế → cách hệ
  thống được sửa → vì sao cách sửa đó khớp (và chưa khớp) chuẩn công nghiệp*.
- Tài liệu 5 trả lời câu phản biện dễ gặp nhất: "cách này có chạy nổi với dữ
  liệu lớn không?"
- Mọi số liệu (số dòng DB, SQL, log) đều lấy từ hệ thống thật của đồ án,
  có thể demo lại trực tiếp.

*Cập nhật: 2026-06-11 — nhánh `feat/agentic-ai-rebuild`.*
