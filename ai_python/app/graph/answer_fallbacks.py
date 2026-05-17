"""Hardcoded final_answer templates when LLM enrich is unavailable."""

from __future__ import annotations

SQL_EMPTY_VI = """\
Chưa tìm thấy dữ liệu phù hợp với câu hỏi của bạn.

Nguyên nhân thường gặp:
- Bộ lọc (tên, mã hàng, khoảng thời gian) quá hẹp hoặc chưa khớp chính tả.
- Dữ liệu chưa được ghi nhận cho kỳ hoặc danh mục bạn đang hỏi.

Bạn có thể thử hỏi lại, ví dụ:
- Liệt kê 10 sản phẩm đang bán kèm mã hàng.
- Doanh thu đơn bán lẻ trong tháng này (tổng hoặc theo ngày).
- Tồn kho hiện tại của một mã hàng cụ thể.
"""

SQL_ERROR_VI = """\
Xin lỗi, mình chưa tra cứu được dữ liệu cho câu hỏi này.

Có thể do điều kiện lọc chưa rõ, thuật ngữ chưa khớp nghiệp vụ ERP, hoặc lỗi tạm thời.

Gợi ý:
- Nêu rõ khoảng thời gian (ví dụ: tháng 5/2026, từ đầu năm đến nay).
- Dùng thuật ngữ chuẩn: đơn bán lẻ, phiếu nhập kho, sản phẩm, danh mục.
- Thử câu hỏi đơn giản hơn trước, ví dụ: «Có bao nhiêu đơn bán lẻ hôm nay?».
"""

CHART_FAIL_VI = """\
Không tạo được biểu đồ từ dữ liệu hiện tại.

Thường do thiếu cột thời gian hoặc số liệu để vẽ trục, hoặc câu hỏi chưa nêu rõ loại biểu đồ và kỳ báo cáo.

Bạn có thể:
- Hỏi lại kèm kỳ (tháng/quý/năm) và chỉ số cần xem (doanh thu, số đơn, tồn kho).
- Yêu cầu bảng số liệu thay vì biểu đồ, ví dụ: «Liệt kê doanh thu theo ngày tháng này».
- Ví dụ biểu đồ: «Vẽ biểu đồ cột doanh thu đơn bán lẻ từng ngày trong tháng 5/2026».
"""

DOMAIN_REJECT_STUB_VI = """\
Yêu cầu này nằm ngoài phạm vi Mini ERP hiện tại.

Hệ thống hỗ trợ các nhóm nghiệp vụ: kho & tồn, sản phẩm & danh mục, đơn bán / POS, nhà cung cấp & khách hàng, tài chính (sổ cái), và trợ lý AI nội bộ.

Ví dụ câu hỏi phù hợp:
- «Tồn kho mã SKU ABC hiện tại?»
- «Tổng doanh thu đơn bán lẻ tháng này?»
- «Tạo phiếu nhập kho 10 laptop từ NCC X».
"""

_TEMPLATES: dict[str, str] = {
    "sql_empty_vi": SQL_EMPTY_VI,
    "sql_error_vi": SQL_ERROR_VI,
    "chart_fail_vi": CHART_FAIL_VI,
    "domain_reject_stub_vi": DOMAIN_REJECT_STUB_VI,
}


def get_fallback_template(template_id: str | None) -> str | None:
    if not template_id:
        return None
    return _TEMPLATES.get(template_id)
