# SRS-013 — Custom Builder: Logic Connector & Display Bugfix

## 1. Overview

Sau khi code review stage 015 + display polish phát hiện 8 vấn đề trong Logic Connector Builder và Display tab của Custom Builder Settings. Tài liệu này mô tả yêu cầu sửa lỗi, không thêm tính năng mới.

**Phạm vi:** frontend-only, mock adapter + CustomBuilderPage + MainLayout.  
**Không đụng:** backend, ai_python, runtime page, các feature khác.

---

## 2. Bugs cần sửa

### BUG-01 — multiply dry-run falsy-zero

**File:** `customBuilderMockAdapter.ts` line 741  
**Hiện tại:** `numericValue(sourceValue || rule.value || 1)`  
**Vấn đề:** Nếu `sourceValue` là số `0` (ví dụ damaged_quantity = 0), biểu thức `0 || rule.value || 1` bỏ qua số 0 hợp lệ và dùng `rule.value` hoặc `1` làm nhân tử — kết quả preview sai hoàn toàn.  
**Yêu cầu:** Phân biệt rõ "source field có giá trị 0" với "source field chưa được chọn". Khi `sourceFieldKey` được chọn, dùng `sourceValue` kể cả khi bằng 0. Khi `sourceFieldKey` rỗng, dùng `rule.value` làm scalar.

---

### BUG-02 — sumLines dry-run bỏ qua targetValue

**File:** `customBuilderMockAdapter.ts` line 744  
**Hiện tại:** `afterValue = numericValue(sourceValue) + numericValue(rule.value)`  
**Vấn đề:** Kết quả bằng source + rule.value, hoàn toàn bỏ qua giá trị hiện tại của target. Preview hiển thị tổng nhỏ hơn trước, gây hiểu nhầm về logic rule.  
**Yêu cầu:** `sumLines` phải cộng dồn vào target: `targetValue + numericValue(sourceValue)`. `rule.value` không tham gia tính toán sumLines (nó chỉ dùng cho `set` và `multiply` scalar).

---

### BUG-03 — selectedRuleId stale sau khi xóa-thêm rule

**File:** `CustomBuilderPage.tsx` line 911  
**Hiện tại:** `useState(logicConnector.rules[0]?.id ?? "")` — ID chỉ init một lần  
**Vấn đề:** Sau khi xóa rule cuối cùng, `selectedRuleId = ""`. Rule mới được thêm vào nhưng button trong danh sách không highlight (border vẫn grey) vì `selectedRule?.id === rule.id` so sánh với `""`.  
**Yêu cầu:** Khi xóa rule đang chọn, `selectedRuleId` phải được cập nhật sang rule tiếp theo (hoặc rule cuối nếu xóa ở giữa). Khi rules rỗng, `selectedRuleId = ""` là đúng. Khi thêm rule mới, luôn set `selectedRuleId` sang ID của rule mới.

---

### BUG-04 — validateLogicConnector false-positive cho scalar multiply

**File:** `customBuilderMockAdapter.ts` line 924  
**Hiện tại:** `["copy", "add", "subtract", "multiply", "sumLines"].includes(rule.operation) && (!rule.sourceFieldKey || !sourceField)` → push error  
**Vấn đề:** `multiply` hỗ trợ dùng `rule.value` làm scalar khi không có source field (và dry-run preview đã tính đúng theo đó). Nhưng validate lại reject pattern này, người dùng không save được rule hợp lệ.  
**Yêu cầu:** `multiply` được phép có `sourceFieldKey = ""` miễn là `rule.value` không rỗng. Chỉ báo lỗi khi cả `sourceFieldKey` lẫn `rule.value` đều rỗng.

---

### BUG-05 — formatPreviewValue: currency không có ký hiệu ₫

**File:** `CustomBuilderPage.tsx` line 355–362  
**Hiện tại:** Cả `currency` và `number` đều dùng `amount.toLocaleString("vi-VN")` — output giống nhau  
**Vấn đề:** Người dùng chọn format `currency` nhưng preview không thấy khác biệt với `number`, không có ký hiệu tiền tệ.  
**Yêu cầu:** Format `currency` phải hiển thị thêm đơn vị "₫" sau số (ví dụ: `1.200.000 ₫`). Có thể dùng `Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" })` hoặc append string " ₫".

---

### BUG-06 — allowedOperations duplicate type union

**File:** `customBuilderMockAdapter.ts` line 908  
**Hiện tại:** `const allowedOperations: BuilderLogicConnectorOperation[] = ["copy", "set", "add", "subtract", "multiply", "sumLines"]`  
**Vấn đề:** Array này duplicate type union `BuilderLogicConnectorOperation`. Thêm operation mới vào type mà quên thêm vào array → silently reject với "không nằm trong allowlist", không có compile-time warning.  
**Yêu cầu:** Loại bỏ array literal. Derive allowedOperations từ một constant gắn liền với type, hoặc dùng Object.keys trên một lookup object. Check này phải compile-safe.

---

### BUG-07 — MainLayout: sidebar flash-of-open trên mobile

**File:** `MainLayout.tsx` line 15–28  
**Hiện tại:** `useUIStore` init `sidebarOpen: true`. `useEffect` chạy sau first render → `setSidebarOpen(false)` trên mobile  
**Vấn đề:** Trên mobile (<768px), sidebar + overlay render visible cho một paint frame trước khi Effect đóng lại — gây flash mỗi khi load trang.  
**Yêu cầu:** Initial state của `sidebarOpen` phải được set đúng ngay từ đầu dựa vào viewport. Không được có visible flash. Chấp nhận: init `sidebarOpen: false` mặc định (vì desktop đóng cũng hợp lý với layout hiện tại), hoặc dùng `window.matchMedia` trong store initializer để set initial state.

---

### BUG-08 — defaultColumnForField ternary lặp 3 chỗ

**File:** `customBuilderMockAdapter.ts` line ~670 và `CustomBuilderPage.tsx` line ~760  
**Hiện tại:** Ternary chain `money → currency, number → number, date → date, text` xuất hiện ≥ 3 lần  
**Vấn đề:** Thêm field type mới (vd `percent`) phải update tất cả chỗ, không có guard compile-time.  
**Yêu cầu:** Extract logic suy luận format từ field type thành một hàm/helper dùng chung (`inferColumnFormat(field)`) hoặc lookup map, đặt trong `customBuilderMockAdapter.ts`. Tất cả nơi dùng logic này gọi về cùng một chỗ.

---

## 3. Out of scope

- Thay đổi types `BuilderLogicConnectorRule`, `BuilderViewColumn`, hay bất kỳ type nào khác
- Thêm operation mới (`divide`, `percent`, v.v.)
- Kết nối backend thật
- Thay đổi UX layout, step wizard, hay flow của builder

---

## 4. Acceptance criteria tổng quát

- Dry-run `multiply` với source = 0 cho kết quả `target × 0 = 0`
- Dry-run `sumLines` cộng dồn vào target: `target + source`
- Xóa-thêm rule: rule mới được highlight đúng ngay lập tức
- `multiply` scalar (không có source, có value) save được không báo lỗi
- Preview currency hiện `₫` sau số
- Sidebar mobile không flash khi load trang
- Không có lỗi TypeScript / ESLint sau fix
