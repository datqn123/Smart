# QA Spec 018 — Custom Builder: Wizard Step Label, Dry-run State & Conditional Input

**SRS ref:** `docs/frontend/srs/014_custom-builder-wizard-conditional-ui-bugfix.md`  
**Tech Spec ref:** `docs/frontend/tech_lead/017_custom-builder-wizard-conditional-ui-bugfix.md`  
**Test scope:** frontend only — CustomBuilderPage + customBuilderMockAdapter

---

## Setup

```
npm run dev   (tại frontend/mini-erp/)
Đăng nhập → /settings/custom-builder
Chọn "Hàng hỏng" (có sẵn logic connector mock + conditional field mock)
```

---

## TC-A1 — Wizard subtitle không còn đề cập "5 bước"

**Bug ref:** BUG-A / FIX-A

**Steps:**
1. Mở Edit Settings của "Hàng hỏng"
2. Chọn tab "Nâng cao"
3. Mở accordion Logic Connector Builder
4. Quan sát dòng subtitle bên dưới tiêu đề "Connector wizard"

**Expected:**
- Subtitle không chứa "5 bước"
- Subtitle đề cập rõ 4 bước trong bảng và review ở panel riêng bên dưới
- Ví dụ: "Đi theo 4 bước: trigger, source, operation, target — xem kết quả ở Review bên dưới."

**Fail condition (trước fix):** Subtitle hiển thị "Đi theo 5 bước: trigger, source, operation, target, review."

---

## TC-A2 — Số lượng cột trong bảng khớp với mô tả

**Bug ref:** BUG-A / FIX-A

**Steps:**
1. Cùng màn hình Connector wizard
2. Đếm số cột có đánh số thứ tự (1., 2., 3., 4.)
3. So sánh với text trong subtitle

**Expected:**
- Có đúng 4 cột đánh số (1. Trigger, 2. Source, 3. Operation, 4. Target)
- Cột "Giá trị set / hệ số" không được đánh số theo bước
- Subtitle mô tả đúng số bước hiển thị trong bảng

---

## TC-B1 — Dry-run "set" hiển thị Target trước ≠ Target sau

**Bug ref:** BUG-B / FIX-B

**Steps:**
1. Mở Logic Connector Builder
2. Chọn rule có operation = "Set giá trị cố định" (rule "Đặt trạng thái khi có số lượng hỏng")
3. Quan sát panel "5. Review dry-run mock"

**Expected:**
- Target trước = "Nháp" (giá trị ban đầu trong fixture)
- Target sau = "Chờ xử lý" (giá trị được set bởi rule)
- Rõ ràng thấy thay đổi trước → sau

**Fail condition (trước fix):** Target trước = Target sau = "Chờ xử lý" — không thấy thay đổi

---

## TC-B2 — Preview table trong Display tab cập nhật theo sampleRecord

**Bug ref:** BUG-B / FIX-B (regression)

**Steps:**
1. Chuyển sang tab "Hiển thị"
2. Quan sát bảng xem thử (Lightweight Preview)
3. Tìm cột "Trạng thái xử lý" (handling_status) trong bảng

**Expected:**
- Cột "Trạng thái xử lý" hiển thị giá trị "Nháp" (do đã đổi sampleRecord)
- Bảng vẫn render đúng, không có lỗi

---

## TC-C1 — Conditional "Giá trị" input visible khi condition = "Không dùng"

**Bug ref:** BUG-C / FIX-C

**Steps:**
1. Mở Edit Settings → tab "Dữ liệu"
2. Chọn bất kỳ field nào
3. Trong section "Logic cơ bản", quan sát hàng conditional logic
4. "Điều kiện theo field" đang chọn "Không dùng"
5. Quan sát ô "Giá trị"

**Expected:**
- Ô "Giá trị" hiển thị input box có viền nhìn thấy được (dù mờ, ở trạng thái disabled)
- Label "Giá trị" hiển thị phía trên input
- Không có khoảng trắng trống tại vị trí ô đó

**Fail condition (trước fix):** Ô "Giá trị" hoàn toàn trống/vô hình — input không thể phân biệt với background card

---

## TC-C2 — Conditional "Giá trị" input active khi chọn condition field

**Bug ref:** BUG-C / FIX-C (functional check)

**Steps:**
1. Ở hàng conditional logic, chọn một field bất kỳ từ "Điều kiện theo field"
2. Đảm bảo "Toán tử" = "Bằng"
3. Quan sát ô "Giá trị"

**Expected:**
- Input "Giá trị" chuyển sang enabled (viền đầy đủ màu)
- Có thể nhập text vào input
- Giá trị nhập vào được lưu (sau khi save, mở lại thấy giá trị cũ)

---

## TC-C3 — Conditional "Giá trị" disabled khi operator = "Có dữ liệu"

**Bug ref:** BUG-C / FIX-C (regression)

**Steps:**
1. Chọn condition field
2. Đổi "Toán tử" sang "Có dữ liệu" (not_empty)
3. Quan sát ô "Giá trị"

**Expected:**
- Input "Giá trị" ở trạng thái disabled (viền mờ, không thể nhập)
- Hành vi này không thay đổi so với trước fix

---

## TC-D — TypeScript & lint clean

**Steps:**
```
cd frontend/mini-erp
npm run lint
```
hoặc
```
npx tsc --noEmit
```

**Expected:**
- Zero errors, zero warnings liên quan đến 2 file đã sửa

---

## Regression checks

| Check | Mô tả |
|-------|-------|
| R-01 | Logic Connector Builder dry-run cho copy/add/subtract/sumLines vẫn đúng |
| R-02 | Connector wizard thêm/xóa rule vẫn hoạt động |
| R-03 | Conditional visibility save/load đúng (value được lưu khi condition được chọn) |
| R-04 | "Xóa" button trong conditional row vẫn clear condition |
| R-05 | LightweightPreview trong Display tab vẫn render bảng (không crash sau khi đổi sampleRecord) |

---

## Pass/Fail definition

**PASS:** TC-A1, A2, B1, B2, C1, C2, C3, D đều pass + R-01 đến R-05 không regression.

**FAIL:** Bất kỳ TC nào fail, hoặc bất kỳ regression nào bị broken.
