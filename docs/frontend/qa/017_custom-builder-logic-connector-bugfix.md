# QA Spec 017 — Custom Builder Logic Connector & Display Bugfix

**SRS ref:** `docs/frontend/srs/013_custom-builder-logic-connector-bugfix.md`  
**Tech Spec ref:** `docs/frontend/tech_lead/016_custom-builder-logic-connector-bugfix.md`  
**Test scope:** frontend only — mock adapter + CustomBuilderPage + MainLayout

---

## Setup

```
npm run dev   (tại frontend/mini-erp/)
Đăng nhập → /settings/custom-builder
Chọn "Hàng hỏng" (có sẵn logic connector mock)
Mở tab "Nâng cao" → mở accordion → xem Logic Connector Builder
```

---

## TC-01 — multiply dry-run với source = 0

**Bug ref:** BUG-01 / FIX-01

**Precondition:**
- Vào Advanced tab → Logic Connector Builder
- Tạo hoặc chọn rule có `operation = multiply`
- Chọn source field có giá trị mẫu = 0 (hoặc tạm thời không có sample nhưng mock trả 0)

**Steps:**
1. Set operation = "Nhân"
2. Set source = field bất kỳ
3. Quan sát dry-run panel "5. Review dry-run mock"

**Expected:**
- Nếu source value = 0: afterValue = `0` (target × 0 = 0)
- Nếu source value = 5 và target = 100: afterValue = `500`
- Không bao giờ hiển thị "multiplied by 1" khi source value thật sự là 0

**Fail condition (trước fix):** afterValue = target × 1 khi source = 0

---

## TC-02 — multiply scalar: source rỗng + value có số

**Bug ref:** BUG-01 / FIX-01 (scalar mode)

**Steps:**
1. Chọn operation = "Nhân"
2. Xóa source field (chọn "Không dùng")
3. Nhập giá trị hệ số = `1.5`
4. Quan sát dry-run

**Expected:**
- afterValue = target × 1.5 (ví dụ target = 100 → afterValue = 150)
- Không có validation error "cần source field hợp lệ"

**Fail condition:** Báo lỗi validate hoặc nhân sai

---

## TC-03 — sumLines dry-run cộng dồn vào target

**Bug ref:** BUG-02 / FIX-02

**Steps:**
1. Tạo rule mới, operation = "Tổng dòng chi tiết"
2. Chọn source field (giá trị mẫu, ví dụ = 200)
3. Quan sát dry-run

**Expected:**
- `beforeValue` = giá trị hiện tại của target field
- `afterValue` = beforeValue + 200 (cộng thêm, KHÔNG phải thay thế)
- Nếu target = 500, source = 200 → afterValue = 700

**Fail condition (trước fix):** afterValue = 200 + rule.value (bỏ qua target, kết quả nhỏ hơn beforeValue)

---

## TC-04 — multiply scalar validation: không block save

**Bug ref:** BUG-04 / FIX-04

**Steps:**
1. Tạo rule: operation = "Nhân", source = "Không dùng" (rỗng), giá trị hệ số = `2`
2. Vào tab "Kiểm tra"
3. Xem danh sách lỗi

**Expected:**
- KHÔNG có lỗi "cần source field hợp lệ" cho rule này
- Save (hoặc bấm "Lưu thay đổi") không bị block bởi rule này

**Fail condition:** Tab "Kiểm tra" hiển thị error, publish bị disable do false-positive

---

## TC-05 — multiply với source rỗng VÀ value rỗng thì báo lỗi

**Bug ref:** BUG-04 / FIX-04 (phải vẫn validate case thật sự sai)

**Steps:**
1. Tạo rule: operation = "Nhân", source = "Không dùng", giá trị hệ số = `""` (để trống)
2. Vào tab "Kiểm tra"

**Expected:**
- Có lỗi "cần source field hoặc giá trị hệ số" cho rule đó
- Rule name xuất hiện trong lỗi

---

## TC-06 — xóa rule cuối cùng rồi thêm mới → highlight đúng

**Bug ref:** BUG-03 / FIX-03

**Steps:**
1. Mở Logic Connector Builder, chỉ còn 1 rule
2. Bấm "Xóa rule" để xóa rule duy nhất
3. Danh sách rule hiển thị "Chưa có connector rule"
4. Bấm "Thêm connector"
5. Quan sát list và wizard panel

**Expected:**
- Rule mới vừa thêm được highlight (border đậm) ngay lập tức
- Wizard panel hiển thị nội dung của rule mới
- Không có trạng thái "wizard hiển thị nhưng không row nào được chọn"

**Fail condition (trước fix):** Rule thêm vào nhưng không có row nào highlight (border vẫn grey)

---

## TC-07 — xóa rule giữa danh sách → rule kế tiếp được chọn

**Bug ref:** BUG-03 / FIX-03

**Steps:**
1. Tạo ít nhất 3 rule (A, B, C)
2. Chọn rule B (giữa)
3. Bấm "Xóa rule"

**Expected:**
- Rule C (đã "rơi" vào vị trí B) được chọn và highlight
- Hoặc nếu B là cuối: rule A (trước đó) được chọn

---

## TC-08 — preview cột format currency hiển thị ₫

**Bug ref:** BUG-05 / FIX-05

**Steps:**
1. Vào tab "Hiển thị"
2. Chọn một cột có type = money hoặc chỉnh format = "Tiền"
3. Quan sát preview bảng danh sách (scroll xuống phần "Xem thử")

**Expected:**
- Giá trị tiền hiển thị có ký hiệu `₫`, ví dụ: `1.200.000 ₫`
- Cột format "Số" (number) hiển thị `1.200.000` không có ₫

**Fail condition (trước fix):** Cả hai format cho cùng output `1.200.000`

---

## TC-09 — sidebar mobile không flash khi load trang

**Bug ref:** BUG-07 / FIX-07

**Steps:**
1. Mở browser DevTools → chuyển sang mobile viewport (375×667 hoặc tương đương)
2. Refresh trang (Ctrl+R)
3. Quan sát sidebar trong ~300ms đầu tiên

**Expected:**
- Sidebar không visible ở lần render đầu
- Không thấy flash overlay hay sidebar open ngay sau load
- Sau đó trang render bình thường với sidebar đóng

**Cách test nhanh:** DevTools → Performance → record trang load → xem paint frames → frame đầu không có sidebar open

**Fail condition (trước fix):** Frame đầu thấy sidebar overlay hiện lên rồi biến mất ngay

---

## TC-10 — sidebar desktop load mở

**Bug ref:** BUG-07 / FIX-07 (regression check)

**Steps:**
1. Đảm bảo viewport ≥ 768px (desktop)
2. Refresh trang

**Expected:**
- Sidebar vẫn mở bình thường trên desktop
- Không thay đổi hành vi so với trước khi fix

---

## TC-11 — inferColumnFormat áp dụng nhất quán

**Bug ref:** BUG-08 / FIX-08

**Steps:**
1. Tạo wizard interface mới với field type "money" và "number"
2. Hoàn thành wizard → vào tab "Hiển thị"
3. Xem cột được generate mặc định

**Expected:**
- Cột `money` có format mặc định = "Tiền" (currency)
- Cột `number` có format mặc định = "Số" (number)
- Cột `date` có format mặc định = "Ngày" (date)
- Cột text/reference/v.v. có format mặc định = "Text"
- Nhất quán giữa wizard-generated và manual add column trong Display tab

---

## TC-12 — TypeScript & lint clean

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
- Zero errors
- Zero warnings liên quan đến các file đã sửa

---

## Regression checks

Sau khi fix, verify các tính năng không bị ảnh hưởng:

| Check | Mô tả |
|-------|-------|
| R-01 | Logic Connector Builder enable/disable toggle vẫn hoạt động |
| R-02 | Copy/add/subtract/sumLines operations vẫn validate đúng khi thiếu source |
| R-03 | `set` operation vẫn báo lỗi khi `value` rỗng |
| R-04 | Workflow Designer (tab Nâng cao) không bị ảnh hưởng |
| R-05 | Publish button vẫn enable/disable đúng theo validation state |
| R-06 | Display tab: toggle cột, chỉnh width/align/format vẫn hoạt động |
| R-07 | Form sections add/remove/reorder vẫn hoạt động |
| R-08 | Sidebar resize trên desktop vẫn hoạt động |
| R-09 | Sidebar open/close toggle (hamburger) vẫn hoạt động trên mobile |

---

## Pass/Fail definition

**PASS:** Tất cả TC-01 đến TC-12 pass + tất cả regression checks R-01 đến R-09 không regression.

**FAIL:** Bất kỳ TC nào fail, hoặc bất kỳ regression nào bị broken.
