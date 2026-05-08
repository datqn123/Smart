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

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

## 4) Test nhanh SSE

```bash
curl -N "http://localhost:9000/v1/chat/stream?q=Xin%20ch%C3%A0o"
```

Bạn sẽ thấy các event `delta`, và kết thúc bằng event `done`.

