# Task002 — Unit (kiểm thử thủ công theo từng case)

> **ID:** `Task-002-U`  
> **Loại:** Unit = **đơn vị nghiệp vụ** — mỗi case một request Postman/tay, không automation.  
> **SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md)

## Mục tiêu

Hoàn thành bộ **U-01 … U-08** (và U-09 tùy chọn) trong [`../04-tester/MANUAL_UNIT_TEST_Task002.md`](../04-tester/MANUAL_UNIT_TEST_Task002.md), đối chiếu envelope API Task002.

## Artifact

| File | Vai trò |
| :--- | :--- |
| [`../04-tester/MANUAL_UNIT_TEST_Task002.md`](../04-tester/MANUAL_UNIT_TEST_Task002.md) | Kịch bản + chỗ ghi Pass/Fail |
| [`../../../smart-erp/docs/postman/Task002_logout.*.json`](../../../smart-erp/docs/postman/) | Body/headers mẫu |

## Verify (thủ công)

- Mở Postman → import / copy từng JSON `body` + headers mô tả trong manual.  
- Ghi kết quả vào cột **Kết quả tay** trong `MANUAL_UNIT_TEST_Task002.md` hoặc screenshot đính ticket.

## Definition of Done

- [ ] U-01 … U-08 đã chạy và ghi nhận kết quả (Pass hoặc Fail có lý do).  
- [ ] JSON Postman repo không lệch field so với `LoginRequest`/`LogoutRequest` thực tế sau khi Dev merge.
