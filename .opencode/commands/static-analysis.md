---
description: Static analysis với CodeQL, Semgrep, SARIF
---

Load the `codeql`, `semgrep`, và `sarif-parsing` skills.

Sau đó chạy static analysis trên project này:
1. Dùng CodeQL để quét các vulnerability phổ biến (XSS, SQL injection, path traversal, v.v.)
2. Dùng Semgrep để quét security anti-patterns
3. Parse và tổng hợp kết quả dưới dạng SARIF nếu có

Báo cáo kết quả theo mức độ nghiêm trọng: Critical → High → Medium → Low.
