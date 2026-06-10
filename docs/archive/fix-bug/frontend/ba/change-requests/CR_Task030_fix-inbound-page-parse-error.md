# 📑 CHANGE REQUEST ANALYSIS (CR) - Task030

> **Mã CR:** `CR_Task030_fix-inbound-page-parse-error`
> **Trạng thái:** 🟡 Pending Approval (Chờ duyệt)
> **Loại thay đổi:** Bug Fix (Sửa lỗi kỹ thuật)
> **Mức độ ưu tiên:** 🔥 High (Chặn build hệ thống)

---

## 1. Mô tả yêu cầu (Request Description)
Hệ thống báo lỗi biên dịch tại trang **Phiếu nhập kho (InboundPage)**. Trình biên dịch Vite/oxc không thể phân tích cú pháp (parse) tệp tin `InboundPage.tsx`, dẫn đến việc không thể khởi động ứng dụng trong môi trường phát triển (Dev) và lỗi khi đóng gói (Build).

- **Symptom:** `[PARSE_ERROR] Error: Unexpected token. Did you mean {'}'} or &rbrace;?` tại dòng 206.
- **Source:** `src/features/inventory/pages/InboundPage.tsx`.

## 2. Phân tích nguyên nhân gốc rễ (Root Cause Analysis - RCA)
Dựa trên việc rà soát cấu trúc JSX trong file `InboundPage.tsx`:
- **Lỗi:** Thiếu 01 thẻ đóng `</div>` cho container chính (mở tại dòng 89).
- **Phân tích luồng thẻ div:**
  1. `<div className="h-full ...">` (Dòng 89) -> **Chưa đóng**.
  2. `<div className="flex-1 ...">` (Dòng 147) -> Đã đóng tại dòng 204.
  3. `<div data-testid="...">` (Dòng 156) -> Đã đóng tại dòng 203.
- Do thiếu thẻ đóng này, parser hiểu nhầm dấu `}` (đóng function) là nội dung văn bản bên trong JSX, gây ra lỗi `Unexpected token`.

## 3. Phân tích tác động (Impact Analysis)
- **Kiến trúc (Architecture):** Không ảnh hưởng.
- **Dữ liệu (Database):** Không ảnh hưởng.
- **Giao diện (UI/UX):** Khắc phục lỗi hiển thị trắng trang (WSOD) và lỗi biên dịch. Sau khi sửa, cấu trúc Layout sẽ trở lại đúng thiết kế Mobile-first và Responsive.
- **Rủi ro (Risks):** Rất thấp. Cần đảm bảo việc bổ sung thẻ đóng không làm sai lệch thứ tự lồng nhau của các thành phần UI khác.

## 4. Giải pháp đề xuất (Proposed Solution)
Bổ sung thẻ đóng `</div>` còn thiếu vào cuối khối `return` của component.

### Thay đổi chi tiết:
**File:** `src/features/inventory/pages/InboundPage.tsx`
```tsx
// ... (từ dòng 202)
        />
      </div> {/* Đóng div dòng 156 */}
    </div> {/* Đóng div dòng 147 */}
  </div> {/* BỔ SUNG: Đóng div dòng 89 */}
  )
}
```

## 5. Tiêu chí nghiệm thu (Acceptance Criteria - BDD)
- **Scenario: Khắc phục lỗi biên dịch trang Nhập kho**
  - **Given:** Ứng dụng đang gặp lỗi `PARSE_ERROR` tại `InboundPage.tsx`.
  - **When:** Lập trình viên bổ sung thẻ `</div>` bị thiếu và lưu file.
  - **Then:** Vite phải biên dịch thành công mà không có lỗi `Unexpected token`.
  - **And:** Trang "Phiếu nhập kho" phải hiển thị đầy đủ Header, Filter, và Table khi truy cập trên trình duyệt.
  - **And:** Layout phải đảm bảo tính Responsive (kiểm tra trên mobile viewport).

## 6. QA Checklist (BA Gate)
- [x] Đã xác định đúng nguyên nhân gốc rễ (RCA).
- [x] Giải pháp bám sát quy tắc `No Hallucination` (không thêm logic dư thừa).
- [x] Đã đối chiếu với `RULES_BUG_FIX.md` (tránh lỗi WSOD).
- [x] Tài liệu sử dụng 100% Tiếng Việt chuyên nghiệp.

---
**Người lập báo cáo:** Agent BA
**Ngày:** 17/04/2026
