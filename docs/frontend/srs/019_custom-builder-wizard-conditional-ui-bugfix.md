# SRS-014 — Custom Builder: Wizard Step Label, Dry-run Misleading State & Conditional Logic Input

## 1. Overview

Sau khi review giao diện trực tiếp từ screenshot, phát hiện 3 vấn đề UI trong Custom Builder Settings:
1. Label bước trong Connector wizard không khớp với nội dung thực tế
2. Dry-run preview hiển thị "trước = sau" gây hiểu nhầm với operation "set"
3. Input "Giá trị" trong conditional visibility thiếu Label và wrapper — bị lệch layout

**Phạm vi:** frontend-only, CustomBuilderPage.tsx + customBuilderMockAdapter.ts  
**Không đụng:** backend, ai_python, runtime page, các feature khác.

---

## 2. Bugs cần sửa

### BUG-A — Connector wizard: step description sai số lượng bước

**File:** `CustomBuilderPage.tsx` line 1015  
**Hiện tại:** `"Đi theo 5 bước: trigger, source, operation, target, review."`  
**Vấn đề:** Table chỉ hiển thị 4 cột có số thứ tự (1. Trigger, 2. Source, 3. Operation, 4. Target) và 1 cột không đánh số "Giá trị set / hệ số". Panel "5. Review dry-run mock" nằm tách biệt bên dưới bảng. Description "5 bước: ... review" khiến người dùng tìm step review trong bảng nhưng không thấy, gây nhầm lẫn.  
**Yêu cầu:** Sửa subtitle thành mô tả chính xác: 4 cột trong bảng là 4 bước cấu hình, review là panel riêng bên dưới. Ví dụ: `"Đi theo 4 bước cấu hình — xem kết quả ở Review bên dưới."` hoặc tương đương.

---

### BUG-B — Dry-run "set": trước = sau, không thấy thay đổi

**File:** `customBuilderMockAdapter.ts` line 458  
**Hiện tại:** `handling_status: "Chờ xử lý"` trong sampleRecord  
**Rule demo:** `operation: "set"`, `targetFieldKey: "handling_status"`, `value: "Chờ xử lý"`  
**Vấn đề:** `previewMockLogicConnectorRule` tính `beforeValue = sampleValues["handling_status"] = "Chờ xử lý"` và `afterValue = rule.value = "Chờ xử lý"`. Kết quả là Target trước = Target sau = "Chờ xử lý" — người dùng không thấy rule có tác dụng gì.  
**Yêu cầu:** Đổi `handling_status` trong sampleRecord sang giá trị ban đầu khác, ví dụ `"Nháp"` (thuộc options hợp lệ: `["Nháp", "Chờ xử lý", "Đã xử lý"]`). Dry-run sẽ hiển thị rõ ràng: Target trước = "Nháp", Target sau = "Chờ xử lý".

---

### BUG-C — Conditional logic: "Giá trị" input vô hình khi disabled

**File:** `CustomBuilderPage.tsx` line 640  
**Hiện tại:** `<Input className="mt-1.5 bg-white" ... disabled={!conditional || ...} />`  
**Root cause:** ShadCN Input component mặc định dùng `bg-transparent` và `disabled:opacity-50`. Class `bg-white` được thêm ở CustomBuilderPage ghi đè `bg-transparent`. Khi input bị disabled: `bg-white + opacity-50` trên nền card `bg-white` = viền và text gần như vô hình (white-on-white).  
**Vấn đề:** Khi "Điều kiện theo field" = "Không dùng" (`!conditional`), input "Giá trị" bị disabled và biến mất khỏi giao diện. Ô "Giá trị" trong grid hiển thị như khoảng trống, người dùng không biết ô đó tồn tại để chứa giá trị so sánh.  
**Yêu cầu:** Xóa class `bg-white` khỏi Input này — để `bg-transparent` mặc định hoạt động. Khi disabled, viền input ở 50% opacity vẫn hiển thị rõ ràng hơn là white-on-white. Không thêm placeholder mới, không thay đổi logic.

---

## 3. Out of scope

- Không thay đổi logic conditional visibility (operators, effects, sourceField linking)
- Không thay đổi logic dry-run calculation
- Không thay đổi kiểu dữ liệu hay field options
- Không sửa checkbox styling (visual artifact trong screenshot, component code đúng)

---

## 4. Acceptance criteria tổng quát

- Subtitle wizard mô tả đúng: 4 bước trong bảng, review ở panel riêng
- Dry-run panel "set" rule hiển thị Target trước ≠ Target sau (ví dụ: "Nháp" → "Chờ xử lý")
- Conditional logic row có label "Giá trị" hiển thị đúng vị trí, input căn thẳng hàng với Toán tử và Hành động
- Không có lỗi TypeScript / ESLint sau fix
