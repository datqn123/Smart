# ai_python (Python AI service)

MVP: expose SSE endpoint để Spring Boot relay về frontend.

## 1) Cài đặt

```bash
cd ai_python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Cấu hình biến môi trường

- `FPT_MKP_API_KEY` (**bắt buộc** cho bước tổng hợp câu trả lời qua MKP)
- `FPT_MKP_BASE_URL` (mặc định `https://mkp-api.fptcloud.com`)
- `FPT_MKP_MODEL` (mặc định `gemma-4-31B-it`)
- **Spring DB read-only (MCP-shaped HTTP)** — để chat đọc PostgreSQL qua template (không SQL thô):
  - `SPRING_AI_DB_BASE_URL` (ví dụ `http://localhost:8080`) **hoặc**
  - `TASK005_DB_READONLY_ADAPTER=spring` (mặc định base URL `http://localhost:8080`)
  - Tuỳ chọn: `SPRING_AI_DB_TIMEOUT_SEC` (mặc định `60`)
- **RAG Task005**: sau khi chạy pipeline corpus + ingest, index nằm dưới `data/rag_corpus/index/` — có thể ghi đè gốc bằng `TASK005_CORPUS_ROOT`
- **`SMART_ERP_CHAT_USE_LLM`**: `true`/`false` — `false` chỉ stream nội dung định dạng từ RAG/SQL (tiết kiệm token)

PowerShell ví dụ:

```powershell
$env:FPT_MKP_API_KEY="..."
$env:FPT_MKP_BASE_URL="https://mkp-api.fptcloud.com"
$env:FPT_MKP_MODEL="gemma-4-31B-it"
$env:SPRING_AI_DB_BASE_URL="http://localhost:8080"
```

## 3) Chạy service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

**Lỗi `Invalid HTTP request received` (uvicorn):** Spring phải gọi **`http://127.0.0.1:9000`**, không dùng `https://` trừ khi bạn cấu hình TLS cho uvicorn. Nếu `AI_PYTHON_BASE_URL` trỏ `https://...:9000`, client sẽ gửi TLS vào cổng HTTP → parser lỗi.

## 4) Test nhanh SSE

```bash
curl -N "http://localhost:9000/v1/chat/stream?q=Xin%20ch%C3%A0o"
```

Bạn sẽ thấy các event `delta`, và kết thúc bằng event `done`.

