# ADR-006 — Agent SQL Factory (SQL-Factory–Lite, Option B)
**SRS_PATH:** `docs/upgrade/ai-python/srs/SRS_AI_Task007_agent-sql-factory-upgrade.md`  

**TASK_FILE:** `docs/upgrade/ai-python/tasks/Task007.md`  
**Date:** 2026-05-11

## 1. Bối cảnh & quyết định

Nhánh `system_data_query` cần nâng cấp theo kiểu **SQL-Factory–lite**: chọn subset bảng có giới hạn, luồng prompt **exploration / exploitation** trên các lần thử được kiểm soát, **hybrid similarity** (SimTok + SimAST; SimEmb tuỳ chọn) trên pool SQL cục bộ có cap trong state, và làm giàu `SchemaArtifact` với **PK, FK**, **`TableMeta.description`**—toàn bộ **tuỳ chọn** qua `GraphSettings` / env, giữ topology Task006 (`gen_sql → sql_review → validate_sql → execute_sql → validate_result`) và executor `http_spring` / stub không đổi contract. Owner đã **khóa Option B** (SRS/PRD): heuristic-first chọn bảng, tuỳ chọn structured LLM table-pick khi cờ và ngưỡng schema/độ tin cậy cho phép, tuỳ chọn node tuyến tính `select_tables` trước `gen_sql`, merge mô tả bảng **HTTP-first** (Spring) + YAML; **không** đọc metadata PostgreSQL trực tiếp trong `ai_python` trong phạm vi Task007 trừ khi sau này leo thang Option C.

## 2. Phương án đã xem xét

- **Option A — Heuristic-only selection, monolithic `gen_sql`, HTTP/YAML descriptions only**  
  - Chọn bảng hoàn toàn bằng heuristic/keyword; không gọi LLM thứ hai cho table pick; explore/exploit nằm trong `gen_sql`; mô tả chỉ từ YAML hoặc Spring HTTP; không thêm PostgreSQL driver trong Python.  
  - **Pros:** latency và chi phí LLM thấp nhất; ít nhánh cấu hình; footprint phụ thuộc nhỏ.  
  - **Cons:** chất lượng chọn bàng kém trên NL mơ hồ và schema lớn; logic heuristic phải bảo trì lâu dài.

- **Option B — Hybrid selection + optional `select_tables` node + HTTP-first descriptions (Owner-selected)**  
  - Heuristic-first; khi bật cờ và quy luật schema/độ tin cậy cho phép, có thể gọi structured LLM cho table pick; có thể tách node `select_tables` tuyến tính trước `gen_sql`; similarity + exploit sau `gen_sql` (ưu tiên theo SRS); mô tả ưu tiên merge qua HTTP Spring, fallback YAML; không PG reader trong scope Task007.  
  - **Pros:** cân bằng chất lượng/chi phí; khớp kế hoạch Owner và soft-launch flag; đường seam test rõ; mở đường leo Option C mà không phá similarity/exploit.  
  - **Cons:** nhiều cờ và nhánh; phải gate chặt để tránh bật “hai lần LLM” nhầm; contract HTTP mô tả phụ thuộc platform.

- **Option C — LLM-forward selection, dedicated `select_tables`, optional direct PostgreSQL reader**  
  - LLM structured cho table picking thường xuyên; luôn có node `select_tables`; có thể sync metadata RO qua `DATABASE_URL_METADATA_RO` trong service Python.  
  - **Pros:** chất lượng chọn bảng cao trên warehouse lớn; refresh metadata linh hoạt nếu chấp nhận credential Python.  
  - **Cons:** latency/cost baseline cao nhất; bề mặt bảo mật và vận hành DB URL trong Python; rủi ro pool/timeout cần NFR chặt—**không** chọn trong Task007.

## 3. Quyết định

**Áp dụng Option B** làm kiến trúc cố định cho Task007: triển khai bounded `selected_tables` (mặc định ≤ 8), pool similarity cục bộ (mặc định ≤ 32), chính sách deterministic explore→exploit trong budget `can_regen_sql`/max attempts Task006, không management LLM riêng; mở rộng `AgentState` (`total=False`) và `GraphSettings`; consumer merge **`table → description`** qua **Spring HTTP** (contract/handoff bridge **TBD**) và/hoặc YAML, **graceful degrade** khi thiếu nguồn; **`psycopg2`/`asyncpg` chỉ được xem xét trong tương lai Option C**, không trong deliverable hiện tại.

## 4. Hệ quả

- **Migration implementation:** module prompt/schema builders, có thể `sql_similarity`, wiring `sql_pipeline` / subgraph; không đổi thứ tự node bắt buộc; checkpoint cũ phải merge không `KeyError`.  
- **Feature flags & rollout:** mặc định **tất cả** tính năng mới **off** ≈ parity Task006; bật từng phần theo SRS Phase 1–6 trong `TASK_FILE`.  
- **Cross-repo:** Spring/other sở hữu API mô tả bảng, auth, rate limit; Python chỉ là HTTP consumer có timeout và xử lý lỗi an toàn.  
- **Risk:** sai cấu hình có thể tăng số LLM call hoặc kích thước prompt—cần cap chuỗi seed/feedback và gate schema-size/confidence trong code.  
- **Deferred:** Option C (PG reader, LLM-forward mặc định) là lộ trình sau nếu Owner chấp nhận credential và chi phí vận hành.

## 5. NFR (mục)

1. **Hiệu năng:** Khi mọi cờ Task007 giữ **mặc định off**, latency incremental median `system_data_query` trên đường CPU/stub không đáng kể so Task006 (**&lt; 50 ms** theo SRS/PRD NFR1); các cap pool/bảng/độ dài chuỗi prompt (NFR2) được enforce lúc assembly để tránh phình token/latency.  
2. **Độ tin cậy:** Thiếu descriptions, HTTP không sẵn sàng hoặc body lỗi **không** làm crash graph; graph compile không yêu cầu PostgreSQL client khi không dùng Option C; checkpoint cũ không có khóa mới vẫn chạy an toàn.  
3. **Bảo mật:** Không đưa connection string vào prompt LLM hoặc log INFO; không log secrets (`DATABASE_*`, JWT bearer); chi tiết auth HTTP (Bearer/mTLS) phối hợp platform, không lộ vào trace user-facing.  
4. **Vận hành:** Operator cấu hình URL/description feature, timeout, thresholds qua `.env.example` và `GraphSettings`; log/trace ở mức diagnostic ghi explore/exploit, similarity, `selected_tables` không rò rỉ PII.  
5. **Chi phí / token (LLM):** Trên nhánh SQL, khi bật table-pick + generation, **≤ 2** lần gọi LLM tuần tự trừ khi Owner duyệt mode đa-call; heuristic đủ mạnh thì **bỏ qua** lần gọi structured table-pick thứ hai để kiểm soát chi phí và độ trễ.
