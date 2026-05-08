# Cách chạy `ai_python` (FastAPI service)

> Cheat-sheet cá nhân. Chi tiết đầy đủ xem `README.md`.

## TL;DR — chạy lại (đã setup xong)

Mở PowerShell trong `d:\do_an_tot_nghiep\project\ai_python`:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload --env-file .env
```

Thấy `Uvicorn running on http://0.0.0.0:9000` là OK. Dừng: `Ctrl + C`.

Test nhanh (terminal khác):

```powershell
curl.exe -N "http://localhost:9000/v1/chat/stream?q=Xin%20ch%C3%A0o"
```

---

## Setup lần đầu (chỉ làm 1 lần)

```powershell
cd d:\do_an_tot_nghiep\project\ai_python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Nếu PowerShell chặn `Activate.ps1`, mở PowerShell **Admin** chạy 1 lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Biến môi trường (file `.env`)

File `ai_python/.env` đã được tạo và **gitignored** — chứa key thật, không lên git.

| Tên | Bắt buộc | Mặc định |
|---|---|---|
| `FPT_MKP_API_KEY` | Có | — |
| `FPT_MKP_BASE_URL` | Không | `https://mkp-api.fptcloud.com` |
| `FPT_MKP_MODEL` | Không | `gemma-4-31B-it` |

`uvicorn ... --env-file .env` sẽ tự nạp các biến này → **không cần `$env:...`**.

Đổi key/model: sửa thẳng `ai_python/.env`, rồi restart uvicorn (Ctrl+C → chạy lại).

> Cần share repo cho người khác? Họ copy `.env.example` → `.env`, điền key của họ.

### (Tuỳ chọn) Set thủ công bằng PowerShell — không khuyến nghị

```powershell
$env:FPT_MKP_API_KEY="..."
$env:FPT_MKP_BASE_URL="https://mkp-api.fptcloud.com"
$env:FPT_MKP_MODEL="gemma-4-31B-it"
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

`$env:...` chỉ tồn tại trong session PowerShell hiện tại.

---

## Khi nào cần làm lại bước nào

| Tình huống | Việc cần làm |
|---|---|
| Mở terminal mới | Activate venv → chạy uvicorn (env tự nạp từ `.env`) |
| Sửa `.env` | Restart uvicorn (Ctrl+C → chạy lại) |
| Sửa `requirements.txt` | `pip install -r requirements.txt` |
| Xoá / hỏng `.venv` | `python -m venv .venv` → `pip install -r requirements.txt` |
| Restart máy | Như "mở terminal mới" |
| Sửa code `.py` | Không cần — `--reload` tự reload |

---

## Lỗi hay gặp

- `python: The term 'python' is not recognized` → cài Python 3.10+ từ python.org, tick **Add to PATH**.
- `cannot be loaded because running scripts is disabled` → chạy `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- `ModuleNotFoundError: fastapi` → chưa activate venv hoặc chưa `pip install -r requirements.txt`.
- `Address already in use` (port 9000) → đổi port `--port 9001`, hoặc kill:
  ```powershell
  netstat -ano | findstr :9000
  taskkill /PID <PID> /F
  ```
- 401/403 khi gọi API → kiểm tra `FPT_MKP_API_KEY` trong `.env`, nhớ restart uvicorn sau khi sửa.
- Sửa `.env` mà không thấy biến mới → uvicorn chưa restart (`--reload` chỉ reload code, không reload env).

---

## Tham chiếu nhanh

- Entry app: `app/main.py` → `app = FastAPI(...)`
- Routers: `app/api/routers/health.py`, `app/api/routers/chat.py`
- Test SSE: `GET /v1/chat/stream?q=...`
- Health: `GET /health` (nếu router health expose)

---

## Lưu ý bảo mật

- **Không commit `.env`** (đã được `.gitignore` chặn).
- Không paste API key vào chat / Slack / issue. Nếu lỡ lộ → revoke + xoay key mới ngay.
- File để share lên repo: `.env.example` (placeholder, không có key thật).
