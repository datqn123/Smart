# PRD (FINAL) — Task 1: Gemma 4 qua OpenAI-compatible API (FPT Cloud)

**Track:** `ai_python` only  
**Slug:** `langgraph-gemma4-task1`  
**Trạng thái:** FINAL — **Owner đã chọn Option B** (`LlmClient` / port + OpenAI-compatible implementation + registry theo role) — 2026-05-10  
**Tham chiếu thiết kế:** `docs/ai-python/tasks/DESIGN/TASK_LANGGRAPH_GEMMA4_TRIEN_KHAI.md` (Task 1, TASK-LM-01 … LM-04)  
**Phạm vi:** Task 1 — không bao gồm LangGraph đầy đủ, FastAPI route hoàn chỉnh, hay multimodal (LM-05) trong v1 PRD này.

**Roadmap (Owner):** Sau v1 sẽ có **thêm các model khác** phục vụ **các chức năng khác** (không chỉ một Gemma). Task 1 cần thiết kế **mở rộng được** (đăng ký thêm model/role) mà không bắt refactor lớn toàn bộ graph.

---

## 4.1. Project Overview

**Core goal:** Chuẩn hóa lớp kết nối LLM **Gemma 4** trên **FPT Cloud** thông qua API **OpenAI-compatible** (`chat.completions`), với cấu hình **chỉ qua biến môi trường**, **port `LlmClient`** với implementation bọc **`ChatOpenAI` (LangChain)**, **registry theo role** để mở rộng đa model/chức năng, **streaming** có wrapper rõ ràng, và **structured output** kèm **fallback parse JSON** khi gateway không hỗ trợ `response_format`/tool schema đầy đủ. Mọi node LangGraph sau này chỉ phụ thuộc port, không tạo client thủ công.

**Target users / actors:**

- **Developer triển khai:** cấu hình env, smoke test kết nối.
- **Code agents / maintainers:** dùng factory và helper structured/stream trong module `ai_python`.
- **Hệ thống downstream (sau Task 2+):** LangGraph nodes gọi factory thay vì tự tạo client.

**Giới hạn phiên bản này (v1 scope):**

- **Trong scope:** TASK-LM-01 … LM-04 (cấu hình, factory, streaming wrapper, structured + JSON fallback).
- **Ngoài scope v1 PRD:** TASK-LM-05 (multimodal, base64, `image_url`) — **phase 2**; Task 2 LangGraph, Task 3 FastAPI hoàn chỉnh, Task 4 QA đầy đủ (chỉ liệt kê dependency nếu cần cho acceptance của LM-03).

---

## 4.2. Specifications

### Functional requirements

1. **Cấu hình (TASK-LM-01)**  
   - Contract cấu hình gồm tối thiểu: `base_url`, `api_key`, `model`, `default_temperature`, `max_tokens`, `top_p`, `top_k`, cờ mặc định cho streaming.  
   - Tên biến môi trường chuẩn (gợi ý): `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TOP_P`, `LLM_TOP_K`, `LLM_STREAMING_DEFAULT`.  
   - Load qua module Settings (ví dụ Pydantic); **fail fast** khi thiếu `API_KEY` nếu bật đường LLM.  
   - Chỉ gửi tham số (vd. `top_k`) nếu gateway FPT hỗ trợ — tránh lỗi 400.  
   - `.env.example` / README: **chỉ tên biến**, không giá trị bí mật.

2. **Port + factory LLM (TASK-LM-02) — Option B**  
   - Định nghĩa **`LlmClient`** (Protocol): invoke/sync + stream text + hook cho structured (LM-04); implementation **`OpenAICompatibleChatClient`** bọc **`ChatOpenAI`** (`base_url`, `model`, `api_key`, tham số generation).  
   - **Registry theo role** (vd. `default`, sau này `sql_review`, …): `get_llm_client(role)` — v1 có thể map mọi role chưa đăng ký về `default` hoặc một client duy nhất; mở rộng sau bằng thêm entry / prefix env.  
   - Không tạo `ChatOpenAI` / `OpenAI()` rải rác ngoài module LLM.

3. **Streaming (TASK-LM-03)**  
   - Wrapper từ stream của `ChatOpenAI` → iterator chunk **văn bản** (delta) ổn định cho tầng graph/server sau này.  
   - Định nghĩa rõ định dạng chunk đầu ra (plain delta vs envelope có metadata như `correlation_id`) — **quyết định tối thiểu cho Task 1** để Task 2/3 không đổi contract.

4. **Structured output + fallback (TASK-LM-04)**  
   - Thử đường “native”: `with_structured_output` / tool schema / `response_format` nếu gateway Gemma hỗ trợ.  
   - Schema Pydantic cho **intent** (vd. `system_data_query` | `general_chat`) và cho **sql_review** (`ok`, `issues[]`).  
   - Fallback: prompt ép **chỉ JSON**, parse an toàn, **retry parse** giới hạn (vd. tối đa 2–3 lần) với backoff nhẹ hoặc tái prompt ngắn.  
   - Ghi nhận trong doc nội bộ/spike: gateway có/không hỗ trợ gì — để Task 2 không giả định sai.

### Non-functional requirements (NFRs) — định lượng / placeholder có lý do

| ID | Yêu cầu | Mục tiêu / placeholder | Ghi chú |
| :-- | :-- | :-- | :-- |
| NFR-PERF-01 | Độ trễ **first token** (streaming, sau khi request rời Python) | **p95 placeholder:** \< **3 s** khi mạng ổn định và model không quá tải | Đo trên môi trường thật FPT Cloud; điều chỉnh sau benchmark |
| NFR-PERF-02 | Độ trễ **invoke đồng bộ** (không stream, prompt ngắn smoke) | **p95 placeholder:** \< **8 s** | Phụ thuộc model và độ dài `max_tokens` |
| NFR-REL-01 | Tỷ lệ lỗi không phục hồi từ provider (5xx/timeout) | **\< 1%** trong cửa sổ quan sát ngắn sau triển khai | Retry ngoài scope Task 1 trừ retry parse JSON |
| NFR-SEC-01 | Bí mật | **Không** commit key; chỉ env/secret manager | Audit checklist LM-01 |
| NFR-OBS-01 | Logging | Không log full prompt/response nếu policy; không log base64 (multimodal out-of-scope v1 anyway) | Chuẩn bị cho Task 2 correlation |

### Kiến trúc — tùy chọn A / B / C (**đã chốt: B**)

> **Quyết định Owner:** **Option B** — port/adapter + implementation OpenAI-compatible + registry role (roadmap đa model). Các option A/C giữ tham chiếu lịch sử / rollback.

#### Option A — “LangChain-centric thin factory”

**Mô tả:** `ChatOpenAI` + Pydantic Settings trực tiếp; wrapper stream/structured nằm trong một package `llm/` mỏng; không thêm interface riêng ngoài hàm factory.

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Triển khai nhanh; khớp tài liệu LangGraph/LangChain; ít lớp trung gian. |
| **Cons** | Khó thay provider không OpenAI-compatible mà không chạm nhiều chỗ. |
| **Risks** | Coupling với hành vi `langchain-openai` khi nâng version. |
| **Cost-to-change** | Thấp ngắn hạn; trung bình dài hạn nếu phải tách adapter. |
| **When to choose** | V1 tập trung FPT/Gemma, ít rủi ro đổi vendor trước 6–12 tháng. |

#### Option B — “Port/adapter: `LlmClient` + implementation OpenAI-compatible”

**Mô tả:** Định nghĩa protocol (typing.Protocol hoặc ABC) cho invoke/stream/structured; một implementation bọc `ChatOpenAI`; có thể thêm implementation mock/stub cho test.

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Test không cần mạng; đổi backend hoặc thêm wrapper retry/policy tập trung. |
| **Cons** | Nhiều file và boilerplate hơn cho team nhỏ. |
| **Risks** | Over-engineering nếu protocol quá rộng so với nhu cầu thực tế. |
| **Cost-to-change** | Cao hơn ban đầu; thấp khi đổi provider hoặc mở rộng policy. |
| **When to choose** | Cần mock nặng, CI không gọi API thật, hoặc roadmap đa provider. |

#### Option C — “Hybrid: `openai` SDK cho spike/gateway quirks + LangChain chỉ ở biên”

**Mô tả:** Dùng package `openai` trực tiếp cho một số đường (workaround header/param đặc thù), đồng bộ hành vi với thin wrapper tạo `ChatOpenAI` cho phần còn lại; hoặc fork logic stream giữa hai client.

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Kiểm soát chi tiết request/response nếu gateway lệch chuẩn nhẹ. |
| **Cons** | Hai stack; dễ lệch hành vi giữa đường “thô” và LangChain. |
| **Risks** | Nợ kỹ thuật và bug inconsistency (đặc biệt streaming). |
| **Cost-to-change** | Trung bình–cao để gom về một đường sau này. |
| **When to choose** | Spike cho thấy `ChatOpenAI` không map đủ tham số FPT mà không có patch upstream. |

#### Quyết định đã khóa (Owner)

- **Đã chọn Option B:** `LlmClient` + implementation bọc `ChatOpenAI` + **registry theo role** (mở rộng đa model/chức năng).  
- **Không triển khai** đường A (factory mỏng không port) hay C (SDK thuần song song) trong phạm vi Task 1 này.

---

## 4.3. Tech stack

| Lớp | Lựa chọn |
| :-- | :-- |
| **Runtime** | Python 3.11+ (repo khuyến nghị 3.12) |
| **HTTP / LLM** | Endpoint OpenAI-compatible (FPT Cloud); **port `LlmClient`**; implementation nội bộ dùng `langchain-openai` `ChatOpenAI` |
| **Cấu hình** | Pydantic Settings (hoặc tương đương), biến môi trường |
| **Validation schema** | Pydantic v2 cho structured models |
| **UI / Frontend** | Không (service Python) |
| **Database & storage** | Không bắt buộc Task 1 (graph/checkpointer thuộc Task 2) |

---

## 4.4. Task breakdown & dependency graph

Mỗi mục dùng checklist `[ ]`; acceptance criteria là điều kiện kiểm tra được.

- [ ] **TASK-LM-01 — Cấu hình env & Settings**
  - **Description:** Định nghĩa contract và load từ env; `.env.example` chỉ tên biến; fail fast nếu thiếu key khi cần LLM.
  - **Input/Output:** Input: env / file `.env` local. Output: object Settings có validate; không chứa secret trong repo.
  - **Acceptance Criteria:** Thiếu `LLM_API_KEY` (khi policy yêu cầu bật LLM) → lỗi khởi động rõ ràng; `top_k` chỉ gửi khi được cấu hình và tương thích gateway.

- [ ] **TASK-LM-02 — Port `LlmClient` + implementation + registry**
  - **Description:** Protocol `LlmClient`; class bọc `ChatOpenAI`; `get_llm_client(role)` / registry (v1: tối thiểu role `default`; role chưa biết → `default` hoặc lỗi có kiểm soát — ghi rõ trong SRS).
  - **Input/Output:** Input: role string + messages LangChain. Output: trả lời văn bản / stream / structured theo LM-03/04.
  - **Acceptance Criteria:** Không tạo `OpenAI()`/`ChatOpenAI` ngoài module LLM; có fake/mock implement `LlmClient` cho unit test; smoke `invoke` một message thành công khi có credential thật (test tùy chọn skip nếu thiếu env).

- [ ] **TASK-LM-03 — Streaming wrapper**
  - **Description:** Wrapper stream → iterator text chunks; quy ước định dạng chunk cho tích hợp sau.
  - **Input/Output:** Input: model đã cấu hình stream; Output: async/sync iterator theo quy ước đã ghi.
  - **Acceptance Criteria:** Consumer demo (script hoặc unit nhẹ) đọc được toàn bộ nội dung ghép từ chunk; không crash khi stream kết thúc bình thường.

- [ ] **TASK-LM-04 — Structured output + JSON fallback**
  - **Description:** Thử native structured/tool/`response_format`; schema intent + sql_review; fallback prompt JSON + parse + retry giới hạn.
  - **Input/Output:** Input: prompt + schema; Output: object Pydantic hoặc lỗi parse có kiểm soát.
  - **Acceptance Criteria:** Có bảng ghi nhận hỗ trợ gateway; test parse thành công với response mẫu (mock) cho intent và sql_review; retry không vượt ngưỡng đã định.

**Phụ thuộc:** TASK-LM-02 phụ thuộc LM-01; LM-03 và LM-04 phụ thuộc LM-02. LM-04 có thể song song LM-03 sau khi LM-02 xong.

**Ngoài scope checklist:** TASK-LM-05 (multimodal) — không có checkbox trong v1 PRD này.

---

## 4.5. Risks & mitigations

| Risk | Ảnh hưởng | Mitigation |
| :-- | :-- | :-- |
| Gateway không hỗ trợ `response_format`/tools như OpenAI chuẩn | Structured intent/sql_review không ổn định | LM-04 fallback JSON + retry; bảng capability sau spike |
| Tham số `top_k`/khác gây 400 | Không gọi được model | Chỉ gửi field được whitelist sau khi đọc doc/gateway |
| Trộn hai client (Option C) | Bug hành vi stream khác nhau | Tránh C trừ khi spike bắt buộc; document một đường “truth” |
| Nhiều model/role mà không có port/registry | Refactor lớn khi thêm chức năng | Chọn **B** (hoặc convention A có prefix theo role rõ ràng); ghi contract “một node → một role model” |
| Lộ API key | Rò rỉ credential | Chỉ env; không log key; review `.gitignore` |

---

## 4.6. Out-of-scope (ghi rõ)

- Multimodal (TASK-LM-05), LangGraph compile (Task 2), FastAPI production routes đầy đủ (Task 3), bộ test E2E đầy đủ (Task 4).
- Chỉnh sửa `backend/smart-erp`, `frontend/mini-erp`.

---

## HITL — đã hoàn thành

- **Owner đã chọn:** **Option B** (2026-05-10).  
- **Hành động kế:** SRS → Task chain → ADR → DEV → CR theo `/orchestrate` lean.
