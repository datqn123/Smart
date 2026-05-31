# Test Result — Q68: PN theo trạng thái

## Thông tin
- **Câu hỏi:** Biểu đồ số phiếu nhập kho theo trạng thái
- **Nhóm:** system_data_chart (bar)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:22
- **Thời gian phản hồi:** 8263ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ phân bổ số phiếu nhập kho theo trạng thái: Rejected (25), Draft (26), Pending (25), Approved (28). Điều này cho thấy có 25 phiếu nhập kho bị từ chối, 26 phiếu đang ở dạng nháp, 25 phiếu đang chờ xử lý và 28 phiếu đã được phê duyệt. Bạn có thể thử tìm hiểu nguyên nhân của việc từ chối phiếu nhập kho hoặc xem xét các phiếu đang chờ xử lý để đảm bảo chúng được xử lý kịp thời.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "status",
  "series": [
    {
      "dataKey": "count",
      "name": "Biểu đồ phân bổ số phiếu nhập kho theo trạng thái"
    }
  ],
  "title": "Biểu đồ phân bổ số phiếu nhập kho theo trạng thái",
  "data": [
    {
      "status": "Rejected",
      "count": 25
    },
    {
      "status": "Draft",
      "count": 26
    },
    {
      "status": "Pending",
      "count": 25
    },
    {
      "status": "Approved",
      "count": 28
    }
  ]
}
```



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu
- [ ] (chart) Có chart_spec hợp lệ

## Ghi chú
- **Bảng liên quan:** stockreceipts

