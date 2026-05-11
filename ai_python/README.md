# ai_python

Dịch vụ FastAPI cho chat AI (LangGraph). Chạy **một luồng duy nhất** dưới đây: cấu hình file `.env` rồi khởi động `uvicorn` **không** `--reload` (chạy thực, không phục vụ chỉnh sửa code tức thì).

**Trước khi bật Python:** PostgreSQL + Spring Boot (`smart-erp`) đã chạy trên `8080`, JWT và relay đã cấu hình (`JWT_SECRET` trùng `JWT_HS256_SECRET` bên dưới, `APP_SECURITY_MODE=jwt-api`, `AI_PYTHON_BASE_URL=http://127.0.0.1:9000`). Frontend (Vite) proxy `/api` tới Spring.

---

## 1. Cài đặt một lần

Trong thư mục `ai_python`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

---

## 2. Cấu hình `.env`

Tạo file `.env` trong `ai_python` (không commit). Thay URL/key/model bằng giá trị thật; secret JWT **cùng một chuỗi** với `JWT_SECRET` của Spring (UTF-8, ≥ 32 byte).

```env
AUTH_DEV_BYPASS=0
JWT_HS256_SECRET=change-me-dev-jwt-secret-32-bytes-min!!
JWT_ISSUER=
JWT_AUDIENCE=

LLM_REQUIRED=1
LLM_BASE_URL=https://your-openai-compatible-host/v1
LLM_API_KEY=your-llm-api-key
LLM_MODEL=gemma-4-31B-it
LLM_TEMPERATURE=0.2
LLM_STREAMING_DEFAULT=0
LLM_SEND_TOP_K=0

APP_ENV=dev
SQL_EXECUTOR_MODE=http_spring
SPRING_SQL_URL=http://127.0.0.1:8080/api/v1/ai/db/sql/query-readonly-raw
SPRING_SQL_BEARER_TOKEN=
SQL_EXECUTOR_TIMEOUT_SECONDS=10
SQL_EXECUTOR_ROW_LIMIT=100

MASK_SQL=0
SQL_LIMIT_MAX=1000
```

---

## 3. Chạy dịch vụ

```powershell
cd ai_python
.\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 9000
```

Kiểm tra: `http://127.0.0.1:9000/health` → `{"status":"ok"}`. Chat từ Mini ERP qua Spring relay tới `http://127.0.0.1:9000/api/v1/ai/chat/stream`.

Mẫu đầy đủ biến khác: [`.env.example`](.env.example). Tài liệu kiến trúc: `docs/`, `TASKS/`.
