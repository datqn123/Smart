# ADR-XXXX: <Tiêu đề quyết định>

> **Trạng thái**: Proposed | Accepted | Superseded | Deprecated  
> **Ngày**: <DD/MM/YYYY>  
> **Owner**: Tech Lead Agent  
> **Liên quan**: <Task/SRS/PR link hoặc path>  

## 1. Bối cảnh (Context)

- **Vấn đề cần quyết định**: <1-2 đoạn>
- **Phạm vi ảnh hưởng**: Frontend | Backend | Database | DevOps | Observability
- **Ràng buộc**: (ví dụ: `RULES.md`, deadline, team size, ngân sách, nền tảng hiện có)

## 2. Quyết định (Decision)

<Mô tả rõ quyết định kiến trúc, API contract, thư viện, pattern, trade-offs>

## 3. Lý do (Rationale)

- **Vì sao chọn phương án này**:
  - ...
- **Vì sao không chọn phương án khác**:
  - ...

## 4. Các phương án đã cân nhắc (Alternatives)

### 4.1 Option A

- Pros:
- Cons:

### 4.2 Option B

- Pros:
- Cons:

## 5. Hệ quả (Consequences)

- **Tích cực**:
- **Tiêu cực / rủi ro**:
- **Mitigation**:

## 6. Non-Functional Requirements (BẮT BUỘC - KHÔNG ĐƯỢC ĐỂ TRỐNG)

> Phần này **bắt buộc** trong mọi ADR và **không được bổ sung sau**. ADR không có NFR hoàn chỉnh thì **PR không được approve**.

### 6.1 Tác động hiệu suất (Performance impact)

- **Hot paths**: <các đường chạy thường xuyên/nhạy cảm>
- **Tác động dự kiến**: <CPU/IO/memory/network/bundle size>
- **Biện pháp kiểm chứng**: <benchmark/log/measurement>

### 6.2 Khả năng mở rộng (Scalability)

- **Scale dimension**: <users/requests/data volume/tenants>
- **Điểm nghẽn tiềm ẩn**:
- **Cách mở rộng**: <caching, pagination, queue, sharding...>

### 6.3 Bảo mật (Security)

- **Threats**: <authz, injection, PII leakage, SSRF...>
- **Controls**: <RBAC, validation, sanitization, secrets, audit>
- **Privacy**: <PII handling, retention, access logging>

### 6.4 Độ tin cậy (Reliability)

- **Failure modes**: <network, partial failure, concurrency, timeouts>
- **Fallback/rollback**:
- **Data integrity**: <transactions, idempotency, constraints>

### 6.5 Khả năng quan sát (Observability)

- **Logs**: <structured logs, correlation id>
- **Metrics**: <SLIs, error rate, latency, saturation>
- **Tracing**: <distributed tracing nếu có>
- **Alerting**: <cảnh báo nào là bắt buộc>

## 7. Kế hoạch triển khai (Implementation Plan)

- <Bước triển khai theo pha, migration plan nếu có>

## 8. Checklist (Gate trước khi PR được approve)

- [ ] ADR đã được viết theo template và **đủ NFR**.
- [ ] Mapping tới SRS/Task/PR rõ ràng.
- [ ] Có kế hoạch kiểm chứng (test/metrics) cho các tác động chính.

