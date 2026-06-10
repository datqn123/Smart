# Tester — Kế hoạch kiểm thử Task002 (thủ công)

**SRS AC:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md) §5  
**Bộ case “unit” chạy tay (chi tiết):** [`MANUAL_UNIT_TEST_Task002.md`](MANUAL_UNIT_TEST_Task002.md)  
**JSON mẫu Postman:** [`../../../smart-erp/docs/postman/`](../../../smart-erp/docs/postman/) — `Task002_logout.*.json`

## Ma trận (ánh xạ tài liệu tay)

| ID tài liệu | Nội dung | HTTP |
| :--- | :--- | :---: |
| U-01 | Logout thành công | 200 |
| U-02 | Thiếu `refreshToken` | 400 |
| U-03 | `refreshToken` rỗng | 400 |
| U-04 | Thiếu Bearer | 401 |
| U-05 | Bearer sai | 401 |
| U-06 | Refresh không khớp user / token giả | 403 |
| U-07 | Logout lặp sau revoke | 403 |
| U-08 | Token cũ sau logout | 401 (theo SRS, kiểm chứng thực tế) |
| U-09 | 500 (optional dev) | 500 |

Không yêu cầu JUnit/automation cho Task002 — chỉ cần **đánh dấu Pass/Fail** trong file manual hoặc ticket.
