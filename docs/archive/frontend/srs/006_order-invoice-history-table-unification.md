# SRS - Đồng bộ giao diện bảng Lịch sử hóa đơn

> Agent: SRS_WRITER  
> Ngày tạo: 01/06/2026  
> Phạm vi: Frontend Mini-ERP (`frontend/mini-erp`)  
> Trạng thái: READY_FOR_TECH_SPEC

## 1. Metadata

- Task ID: `Task008_order_invoice_history_table_unification`
- Scope: UI-only, không đổi API/backend contract.
- In-scope screen trong menu `Đơn hàng`:
  - `Lịch sử hóa đơn` - `/orders/wholesale`
- Out-of-scope:
  - `Đơn bán lẻ` - `/orders/retail`
  - `Trả hàng` - `/orders/returns`
  - Màn phê duyệt dùng lại `OrderTable`
  - Backend/API/database
  - Cấu hình ẩn/hiện cột table
  - Resize cột, kéo thả cột, đổi business rule trạng thái hóa đơn

## 2. Input và traceability

- User request: tiếp tục soạn tài liệu đồng bộ giao diện; trong menu Đơn hàng chỉ làm giao diện `Lịch sử hóa đơn`, không chỉnh sửa `Đơn bán lẻ`.
- CodeGraph preflight:
  - `Get-Content AGENTS/skills/codegraph-context/SKILL.md`
  - `codegraph status --json`
  - `codegraph sync` do có pending changes trước khi đọc scope
  - `codegraph context "SRS dong bo giao dien menu don hang chi man hinh lich su hoa don khong chinh don ban le" --format json`
- Evidence files:
  - `frontend/mini-erp/src/App.tsx`
  - `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
  - `frontend/mini-erp/src/components/shared/layout/Header.tsx`
  - `frontend/mini-erp/src/features/orders/pages/WholesalePage.tsx`
  - `frontend/mini-erp/src/features/orders/pages/RetailPage.tsx`
  - `frontend/mini-erp/src/features/orders/components/OrderTable.tsx`
  - `frontend/mini-erp/src/features/orders/components/OrderToolbar.tsx`
  - `frontend/mini-erp/src/features/orders/hooks/useRetailSalesHistoryListQuery.ts`
  - `frontend/mini-erp/src/features/orders/api/salesOrdersApi.ts`
  - `frontend/mini-erp/src/lib/data-table-layout.ts`
  - `docs/frontend/srs/007_product-management-table-unification.md`

## 3. Hiện trạng và GAP

| ID | GAP | Evidence | Tác động |
| :-- | :-- | :-- | :-- |
| GAP-1 | Page title đang là `Lịch sử hóa đơn bán lẻ`, trong khi menu/breadcrumb là `Lịch sử hóa đơn`. | `WholesalePage.tsx`, `Sidebar.tsx`, `Header.tsx` | User thấy cùng một màn nhưng tên gọi không nhất quán. |
| GAP-2 | Header page dùng `font-black uppercase`, khác contract đã áp dụng ở Kho hàng/Sản phẩm. | `WholesalePage.tsx` | Màn này trông nặng và lệch nhịp với các table record đã đồng bộ. |
| GAP-3 | Loading/error/cập nhật đang hiển thị ngoài table shell. | `WholesalePage.tsx` | Chuyển trạng thái loading/data/error gây layout shift. |
| GAP-4 | Table shell đang dùng `rounded-lg shadow-sm border-slate-200`, chưa dùng contract `DATA_TABLE_SHELL_CLASS`. | `WholesalePage.tsx`, `data-table-layout.ts` | Khác border/radius/shadow so với table record chuẩn. |
| GAP-5 | Toolbar `retailHistory` nằm trong shell nhưng style border/radius riêng, input chưa thống nhất focus slate như các toolbar đã chuẩn hóa. | `OrderToolbar.tsx` | Bộ lọc ngày/tìm kiếm chưa cùng nhịp giao diện. |
| GAP-6 | Footer/pagination đang nằm phía trên table, không nằm cố định dưới table shell như các màn record mới. | `WholesalePage.tsx` | Thông tin `Trang X/Y`, `total` không cùng vị trí với footer record counter. |
| GAP-7 | `OrderTable` còn dùng checkbox màu xanh khi `showCheckbox=true` và badge loại đơn có xanh/tím; dù lịch sử hóa đơn đang `showCheckbox=false`, component dùng chung có rủi ro lệch khi mở rộng. | `OrderTable.tsx` | Root cause style chưa thống nhất nằm ở shared component. |
| GAP-8 | Empty state copy là `Không tìm thấy đơn hàng nào`, chưa đúng ngữ cảnh hóa đơn. | `OrderTable.tsx` | Nội dung chưa thuần theo màn `Lịch sử hóa đơn`. |
| GAP-9 | Action column lịch sử hóa đơn chỉ có icon xem chi tiết nhưng vẫn dùng width action mặc định 168px. | `OrderTable.tsx`, `data-table-layout.ts` | Cột thao tác rộng hơn nhu cầu, làm mất cân bằng table. |
| GAP-10 | Copy mô tả có `POS` và `Chỉ xem` hơi kỹ thuật; cần thống nhất với ngôn ngữ nghiệp vụ trên menu. | `WholesalePage.tsx` | Giao diện chưa thuần tiếng Việt, dễ làm user hiểu đây là một phần của màn bán lẻ POS. |

## 4. Mục tiêu nghiệp vụ

- Đồng bộ giao diện `Lịch sử hóa đơn` với contract table đã làm ở Kho hàng và Sản phẩm.
- Giữ màn `Đơn bán lẻ` nguyên trạng vì đây là màn thao tác POS có layout chuyên biệt, không phải table record.
- Tên gọi user-facing phải thống nhất là `Lịch sử hóa đơn`.
- Bảng phải dễ scan, footer/pagination ổn định, không gây cảm giác mỗi menu dùng một design khác nhau.
- Hạn chế màu xanh/tím kiểu AI; ưu tiên slate/neutral, chỉ giữ màu semantic khi thật sự biểu thị trạng thái nghiệp vụ.

## 5. Functional requirements

### FR-1 - Scope route

- Chỉ áp dụng cho route `/orders/wholesale`.
- Không chỉnh sửa route `/orders/retail`.
- Không chỉnh sửa layout POS, giỏ hàng, chọn sản phẩm, checkout hoặc bất kỳ flow bán lẻ trực tiếp nào.
- Không đổi API đang dùng:
  - `GET /api/v1/sales-orders/retail/history`
  - `GET /api/v1/sales-orders/{id}` khi mở chi tiết.

### FR-2 - Page header contract

Màn `Lịch sử hóa đơn` phải dùng header giống các table record đã chuẩn hóa:

- Container: `p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden`.
- Title: `text-xl md:text-2xl font-semibold text-slate-900 tracking-tight`.
- Title text: `Lịch sử hóa đơn`.
- Description đề xuất: `Tra cứu hóa đơn đã phát sinh và xem chi tiết giao dịch.`
- Không dùng uppercase, không dùng `font-black`, không hiển thị task/code/API trong user-facing copy.

### FR-3 - Toolbar/filter contract

Toolbar lịch sử hóa đơn cần đồng bộ với các toolbar record:

- Search input:
  - Height desktop/mobile nhất quán với toolbar mới.
  - Icon search màu slate.
  - Placeholder: `Tìm theo mã hóa đơn hoặc khách hàng...`
  - Focus tone `slate`, không dùng blue focus.
- Date filter:
  - Hai input `Từ ngày`, `Đến ngày`.
  - Trên desktop nằm cùng hàng với search.
  - Trên mobile xếp dọc hoặc 2 hàng, touch target tối thiểu 44px.
- Không hiển thị create/edit/delete/export action trên màn lịch sử hóa đơn.
- Toolbar không tạo card lồng trong table shell; nếu nằm trong shell thì chỉ là top control band có border bottom.

### FR-4 - Sort/pagination placement

- Sort control không nằm tách rời gây lệch flow.
- Cho phép một trong hai phương án:
  - Đưa sort vào toolbar cùng search/date.
  - Hoặc giữ một control row ngay dưới toolbar nhưng phải cùng typography/spacing với các màn record khác.
- Pagination phải nằm trong footer table shell, không nằm phía trên table.
- Footer đề xuất:
  - Trái: `Đang hiển thị X / Y hóa đơn`
  - Giữa/phải: `Trang A / B`
  - Phải: icon button `Trước`, `Sau`
- Nếu đang fetching trang mới:
  - Footer hiển thị `Đang cập nhật...` bên phải hoặc cạnh pagination.
  - Không đẩy table xuống.

### FR-5 - Table shell contract

- Table shell phải dùng `DATA_TABLE_SHELL_CLASS` hoặc class tương đương:
  - white background
  - `border border-slate-200/60`
  - `rounded-xl`
  - `shadow-md`
  - `overflow-hidden`
- Scroll area dùng `DATA_TABLE_SCROLL_CLASS`.
- Loading first page nằm trong shell.
- Error first page nằm trong shell.
- Empty state nằm trong table body hoặc shell, style thống nhất.

### FR-6 - Table visual contract

`OrderTable` khi dùng cho lịch sử hóa đơn phải đảm bảo:

- Header sticky giống record tables khác.
- Row height ổn định `h-14` hoặc `h-16` nhưng phải nhất quán trong màn.
- Hover/selected neutral slate.
- Không dùng màu xanh/tím làm màu chủ đạo.
- Header/cell width khớp nhau, không giật khi scroll.
- Text dài như khách hàng/order code truncate đúng, không đẩy cột thao tác.

### FR-7 - Column labels và dữ liệu hiển thị

Màn lịch sử hóa đơn cần dùng label thuần tiếng Việt:

| Cột hiện tại | Label mới đề xuất | Ghi chú |
| :-- | :-- | :-- |
| `Mã đơn` | `Mã hóa đơn` | Phù hợp menu `Lịch sử hóa đơn`. |
| `Khách hàng` | `Khách hàng` | Giữ nguyên. |
| `Ngày tạo` | `Ngày lập` | Phù hợp hóa đơn; nếu product muốn giữ theo API thì dùng `Ngày tạo`. |
| `Tổng tiền` | `Thành tiền` | Khớp sort label `Thành tiền`. |
| `Thao tác` | `Thao tác` | Giữ nguyên. |

Không hiển thị cột `Trạng thái` trong scope hiện tại nếu business vẫn chỉ xem lịch sử hóa đơn đã phát sinh.

### FR-8 - Action column

- Vì lịch sử hóa đơn chỉ hỗ trợ xem chi tiết, action column nên dùng width single-action:
  - `DATA_TABLE_ACTION_SINGLE_HEAD_CLASS`
  - `DATA_TABLE_ACTION_SINGLE_CELL_CLASS`
- Icon `Eye` luôn hiển thị.
- Button có title/tooltip `Xem chi tiết hóa đơn`.
- Không hiển thị edit/delete trong màn lịch sử hóa đơn.
- Không làm thay đổi behavior của các màn khác đang dùng `OrderTable` có edit/delete.

### FR-9 - Type badge / channel display

- Nếu vẫn hiển thị loại đơn trong cell khách hàng, badge `Bán lẻ` phải dùng neutral style hoặc bỏ badge nếu màn chỉ có hóa đơn bán lẻ.
- Không dùng purple/blue làm badge mặc định trong màn này.
- Nếu cần giữ thông tin loại giao dịch, dùng label nhỏ màu slate:
  - `Bán lẻ`
  - `X mặt hàng`
- Không để badge làm hàng table cao bất thường.

### FR-10 - Empty/loading/error copy

- Loading first page: `Đang tải lịch sử hóa đơn...`
- Fetching filter/page: `Đang cập nhật...`
- Error first page: `Không tải được lịch sử hóa đơn.`
- Empty state: `Chưa có hóa đơn phù hợp.`
- Nếu có refetch trong hook hoặc query available ở page, thêm button `Thử lại`; nếu chưa có, không bắt buộc trong task này.

### FR-11 - Responsive behavior

- Desktop:
  - Header, toolbar, sort/filter, table, footer nằm trong một vertical flow.
  - Table chiếm phần còn lại của viewport, không chèn ép cột — các cột giữ độ rộng đủ để hiển thị nội dung rõ ràng.
- Mobile:
  - Search/date/sort xếp dọc hoặc wrap hợp lý.
  - Footer pagination không overlap; button `Trước`/`Sau` giữ touch target tối thiểu 44px.
  - Text `Đang hiển thị X / Y hóa đơn` không tràn khỏi footer.

## 6. Non-functional requirements

- NFR-1: Không đổi API request/response, query key, permission hoặc business rule.
- NFR-2: Không chỉnh sửa màn `/orders/retail`.
- NFR-3: Không tạo màu chủ đạo xanh/tím; dùng slate/neutral.
- NFR-4: Build không phát sinh lỗi TypeScript.
- NFR-5: Lint không phát sinh error mới; warning cũ nếu có phải ghi rõ trong review.
- NFR-6: Không phá các nơi khác dùng `OrderTable`, đặc biệt approval pages và returns nếu vẫn import component này.
- NFR-7: Không thêm abstraction lớn nếu chỉ cần prop/config nhỏ để phục vụ màn lịch sử hóa đơn.

## 7. Business rules / permission display

- Lịch sử hóa đơn là màn đọc dữ liệu:
  - Không tạo hóa đơn.
  - Không sửa hóa đơn.
  - Không hủy/xóa hóa đơn.
  - Chỉ xem chi tiết.
- Quyền truy cập vẫn theo menu hiện tại `can_manage_orders`.
- Nếu user không có quyền hoặc API trả lỗi, UI chỉ hiển thị error state trong shell; không đổi logic phân quyền.

## 8. Horizontal analysis

- Root cause giống các task đồng bộ trước: thiếu contract chung ở 3 lớp:
  - Page shell/footer.
  - Toolbar/filter row.
  - Shared `OrderTable`.
- Khi xử lý cần tránh vá riêng `WholesalePage` mà làm lệch component dùng chung:
  - Nếu thay `OrderTable` style checkbox/badge/action, phải kiểm tra các màn đang dùng lại.
  - Nếu chỉ cần riêng lịch sử hóa đơn, nên thêm prop rõ nghĩa như `variant="invoiceHistory"` hoặc `singleAction`.
- Cần giữ ranh giới scope:
  - `/orders/retail` là POS workspace, không phải record table, nên không đồng bộ theo contract table trong task này.
  - `/orders/returns` không nằm trong yêu cầu hiện tại.
  - Approval pages dùng `OrderTable` nhưng không đổi layout page trong task này.

## 9. Acceptance criteria

```gherkin
Given user mở menu Đơn hàng > Lịch sử hóa đơn
When trang tải xong
Then title hiển thị "Lịch sử hóa đơn"
And không hiển thị title "Lịch sử hóa đơn bán lẻ"
And màn Đơn bán lẻ không bị thay đổi
```

```gherkin
Given user mở /orders/wholesale
When quan sát table
Then table shell, header, scroll area và footer có style giống contract đã áp dụng ở Kho hàng/Sản phẩm
And loading/error nằm trong shell thay vì nằm rời bên ngoài
```

```gherkin
Given danh sách có dữ liệu
When quan sát footer
Then footer hiển thị "Đang hiển thị X / Y hóa đơn"
And pagination "Trang A / B" cùng nút Trước/Sau nằm ở footer
```

```gherkin
Given user đang ở màn Lịch sử hóa đơn
When quan sát cột Thao tác
Then chỉ có icon xem chi tiết
And icon có tooltip/title "Xem chi tiết hóa đơn"
And không có icon sửa/xóa
```

```gherkin
Given user mở màn Đơn bán lẻ
When so sánh trước/sau task
Then layout POS, chọn sản phẩm, giỏ hàng và checkout không thay đổi
```

## 10. Test strategy

- Unit/component:
  - `OrderTable` render variant lịch sử hóa đơn với `showCheckbox=false`, `hideStatusColumn=true`, single action width.
  - Empty state copy đúng ngữ cảnh hóa đơn.
  - Action view gọi đúng handler, không render edit/delete.
- Page/manual QA:
  - `/orders/wholesale` desktop/mobile: header, toolbar, table, footer không overlap.
  - Loading/error/empty/data đều nằm trong shell.
  - Pagination hoạt động và footer không đổi chiều cao khi fetching.
  - `/orders/retail` không thay đổi.
- Regression:
  - `OrderDetailDialog` vẫn mở đúng hóa đơn.
  - Search/date/sort vẫn gọi hook hiện tại.
  - Các màn dùng `OrderTable` khác không vỡ action/checkbox/status.
- Commands:
  - `npm run build`
  - `npm run lint`

## 11. Open questions

| ID | Câu hỏi | Blocker |
| :-- | :-- | :-- |
| OQ-1 | Cột ngày nên đặt là `Ngày lập` hay giữ `Ngày tạo` theo API? | Non-blocker; mặc định dùng `Ngày lập` cho user-facing hóa đơn. |
| OQ-2 | Có cần hiển thị badge `Bán lẻ` trong màn chỉ có lịch sử hóa đơn bán lẻ không? | Non-blocker; mặc định bỏ hoặc neutralize badge để giảm màu. |
| OQ-3 | Footer có cần chọn page size không? | Out-of-scope; giữ page size 20 như hook hiện tại. |

## 12. Ready state

- SRS status: READY_FOR_TECH_SPEC
- Đề xuất stage tiếp theo: TECH_SPEC_WRITER tạo handoff cho `WholesalePage`, `OrderToolbar`, `OrderTable`, `data-table-layout.ts` trong phạm vi `/orders/wholesale`.
