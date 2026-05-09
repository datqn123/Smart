# ai_python (Python AI service)

MVP: expose SSE endpoint để Spring Boot relay về frontend.

## 1) Cài đặt

```bash
cd ai_python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Nếu gặp **`No module named uvicorn`** khi dùng `.\.venv\Scripts\python.exe -m uvicorn`, chạy lại **`pip install -r requirements.txt`** trong `.venv` đã activate (hoặc `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`). Pip có thể cảnh báo `Ignoring invalid distribution ~vicorn` — có thể bỏ qua nếu cài đặt vẫn “Successfully installed … uvicorn”; nếu tái diễn, xóa thư mục lạ `...\site-packages\~vicorn*` rồi `pip install -r requirements.txt` lại.

## 2) Cấu hình biến môi trường

- `FPT_MKP_API_KEY` (**bắt buộc**)
- `FPT_MKP_BASE_URL` (mặc định `https://mkp-api.fptcloud.com`)
- `FPT_MKP_MODEL` (mặc định `gemma-4-31B-it`)

PowerShell ví dụ:

```powershell
$env:FPT_MKP_API_KEY="..."
$env:FPT_MKP_BASE_URL="https://mkp-api.fptcloud.com"
$env:FPT_MKP_MODEL="gemma-4-31B-it"
```

## 3) Chạy service

Luôn chạy **`python -m uvicorn`** trong thư mục `ai_python` sau khi bật `.venv`. Tránh gõ riêng lệnh `uvicorn ...` khi có nhiều Python trên máy — đặc biệt **Windows + `--reload`**: process con của reloader có thể dùng sai interpreter và báo **`ModuleNotFoundError: No module named 'uvicorn'`**.

PowerShell:

```powershell
cd ai_python
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

Không cần `activate` (một dòng):

```powershell
cd ai_python
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

Nếu vẫn lỗi khi `--reload`: tắt reload tạm thời để làm việc ổn định: bỏ cờ `--reload` (restart tay sau khi sửa code).

## 4) Test nhanh SSE

```bash
curl -N "http://localhost:9000/v1/chat/stream?q=Xin%20ch%C3%A0o"
```

Bạn sẽ thấy các event `delta`, và kết thúc bằng event `done`.

## 5) MCP `smart-erp-ai` (Task004 — stdio)

Chạy MCP server cho Cursor (thư mục làm việc `ai_python/`):

```powershell
cd ai_python
python -m app.smart_erp_mcp
```

Chi tiết: [`docs/task004/RUNBOOK_MCP.md`](docs/task004/RUNBOOK_MCP.md).

