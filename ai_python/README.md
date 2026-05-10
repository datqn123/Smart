# ai_python

Service FastAPI (Python) cho tích hợp AI / chatbot.

## Yêu cầu

- Python 3.11+ (khuyến nghị 3.12)

## Cài đặt lần đầu

Mở terminal tại thư mục `ai_python`:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

## Chạy dự án

**Windows (PowerShell)** — tự reload khi sửa code:

```powershell
cd ai_python
.\.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

**macOS / Linux**

```bash
cd ai_python
./.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Sau khi chạy:

- Trang chỉ báo service: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Biến môi trường

Cấu hình đọc từ **biến môi trường** và file **`.env`** trong thư mục làm việc (thường là `ai_python/` khi đã `cd ai_python`). Danh sách đầy đủ và thứ tự gợi ý: [`.env.example`](.env.example).

### Cách 1 — File `.env` (khuyến nghị)

1. Trong thư mục `ai_python`, sao chép mẫu:  
   `copy .env.example .env` (Windows) hoặc `cp .env.example .env` (macOS/Linux).
2. Mở `.env`, điền giá trị thật cho `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (không commit file `.env`).
3. Tuỳ chọn: đặt `LLM_REQUIRED=1` để thiếu cấu hình bắt buộc thì **ứng dụng không khởi động** (fail-fast trong `main.py` lifespan).
4. Cùng file `.env`: tuỳ chỉnh nhóm **LangGraph / SQL** (bảng dưới) nếu triển khai graph hoặc checkpoint SQLite.

### LLM / OpenAI-compatible (`LLM_*`)

Tiền tố **`LLM_`** — chi tiết field: `app/config/settings.py`.

### LangGraph / SQL executor / checkpoint (Task 2)

**Không** dùng tiền tố `LLM_` — load qua `app/config/graph_settings.py` (tên biến env trùng tên field viết HOA, ví dụ `SQL_EXECUTOR_MODE`).

| Biến | Ý nghĩa |
| :-- | :-- |
| `SQL_EXECUTOR_MODE` | `stub` (mặc định, CI/test), `python_ro` (cần `DATABASE_URL_RO`), `http_spring` (cần `SPRING_SQL_URL`). |
| `DATABASE_URL_RO` | URL DB chỉ đọc khi `SQL_EXECUTOR_MODE=python_ro`. |
| `SPRING_SQL_URL` | Base URL API Spring chạy SQL khi `SQL_EXECUTOR_MODE=http_spring` (Task 3). |
| `CHECKPOINT_SQLITE_PATH` | Đặt path file SQLite để dùng SqliteSaver; để trống → MemorySaver. |
| `MASK_SQL` | `1`/`true`: không log SQL đầy đủ (an toàn log). |
| `SQL_ALLOWED_TABLES` | Danh sách bảng cho phép (comma-separated); để trống = không siết allowlist (chỉ dev). |

Graph LangGraph: `app/graph/` (`compile_agent_graph`, SqlExecutor port, checkpointer).

### Cách 2 — PowerShell (chỉ phiên terminal hiện tại)

Chạy trong thư mục `ai_python` trước khi gọi `uvicorn` hoặc `pytest`:

```powershell
$env:LLM_REQUIRED = "0"
$env:LLM_BASE_URL = "https://mkp-api.fptcloud.com"
$env:LLM_API_KEY = "<secret>"
$env:LLM_MODEL = "gemma-4-31B-it"
$env:LLM_TEMPERATURE = "0.2"
# Tuỳ chọn: $env:LLM_MAX_TOKENS = "1024"; $env:LLM_TOP_P = "0.95"; $env:LLM_TOP_K = "40"
# Chỉ khi gateway hỗ trợ top_k: $env:LLM_SEND_TOP_K = "1"
# Graph (tuỳ chọn): $env:SQL_EXECUTOR_MODE = "stub"; $env:MASK_SQL = "0"
.\.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

Xóa biến trong phiên hiện tại: `Remove-Item Env:\LLM_API_KEY` (ví dụ).

### Cách 3 — macOS / Linux (bash, phiên hiện tại)

```bash
export LLM_REQUIRED=0
export LLM_BASE_URL="https://mkp-api.fptcloud.com"
export LLM_API_KEY="<secret>"
export LLM_MODEL="gemma-4-31B-it"
export LLM_TEMPERATURE=0.2
# export SQL_EXECUTOR_MODE=stub
# export MASK_SQL=0
./.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Bảng biến LLM (tóm tắt)

| Biến | Bắt buộc khi `LLM_REQUIRED=1` | Ý nghĩa |
| :-- | :--: | :-- |
| `LLM_REQUIRED` | — | `1`/`true`: bắt buộc đủ URL, key, model khi start app. |
| `LLM_BASE_URL` | Có | Base URL OpenAI-compatible (không hard-code secret trong repo). |
| `LLM_API_KEY` | Có | API key (chỉ env / secret manager). |
| `LLM_MODEL` | Có | Tên model, ví dụ `gemma-4-31B-it`. |
| `LLM_TEMPERATURE` | — | Mặc định `0.2` nếu không set (trong code). |
| `LLM_MAX_TOKENS` | — | Giới hạn token sinh (số nguyên). |
| `LLM_TOP_P` | — | Nucleus sampling. |
| `LLM_TOP_K` | — | Chỉ gửi lên provider nếu `LLM_SEND_TOP_K=1`. |
| `LLM_STREAMING_DEFAULT` | — | Gợi ý mặc định có ưu tiên stream hay không. |
| `LLM_SEND_TOP_K` | — | `1`: gửi `top_k` — chỉ bật khi tài liệu gateway xác nhận hỗ trợ (tránh HTTP 400). |

Giá trị boolean có thể dùng `0`/`1`, `true`/`false` (Pydantic parse chuẩn). Riêng graph: `MASK_SQL` nhận `1`/`true`/`yes` (xem `GraphSettings`).

### Lưu ý

- Không đưa `LLM_API_KEY` vào git; `.env` nên có trong `.gitignore` (môi trường local).
- Code LLM (port `LlmClient`, registry): `app/llm/` (Task001 / Option B).
- Graph LangGraph + SqlExecutor + checkpoint: `app/graph/` (Task002).
- Kiểm thử nhanh không cần key LLM thật: `python -m pytest tests` (mock).

## Ghi chú

- Điều phối Agent (`/orchestrate`): [`AGENTS/WORKFLOW_RULE.md`](AGENTS/WORKFLOW_RULE.md), [`AGENTS/AGENT_REGISTRY.md`](AGENTS/AGENT_REGISTRY.md).
- Thư mục `.venv` đã được liệt kê trong `.gitignore`, không commit lên git.
- Đổi cổng bằng cách thay `--port 8000` (ví dụ `8001`).
