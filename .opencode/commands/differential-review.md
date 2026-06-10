---
description: Security review cho PR / code changes
---

Load the `differential-review` skill.

Sau đó review code changes dưới góc độ bảo mật:
1. Phân tích git diff hoặc PR changes
2. Tìm security issues: injection, auth bypass, data leak, insecure defaults, v.v.
3. Kiểm tra git history để hiểu context của changes
4. Đánh giá risk level cho từng issue tìm được
5. Đề xuất remediation cụ thể

Nếu chưa có PR/diff cụ thể, hãy hỏi tôi để lấy thông tin.
