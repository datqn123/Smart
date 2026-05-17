# Chạy ai_python một lệnh — biến môi trường dev cố định (KHÔNG dùng production).
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# --- Auth (dev): bỏ qua verify JWT; secret vẫn set khớp default Spring local nếu sau này tắt bypass ---
$env:AUTH_DEV_BYPASS = "1"
$env:JWT_HS256_SECRET = "change-me-dev-jwt-secret-32-bytes-min!!"
$env:JWT_ISSUER = ""
$env:JWT_AUDIENCE = ""

# --- LLM: không có URL+key hợp lệ → chat trả "[chat] stub: no LLM registry". Bật model thật: một trong hai ---
#   (A) Tạo file .env trong thư mục ai_python (copy .env.example), điền LLM_BASE_URL + LLM_API_KEY + LLM_MODEL.
#   (B) Bỏ comment 2 dòng dưới và điền gateway OpenAI-compatible của bạn.
$env:LLM_REQUIRED = "0"
# $env:LLM_BASE_URL = "https://your-openai-compatible-host/v1"
# $env:LLM_API_KEY = "your-api-key"
$env:LLM_MODEL = "gemma-4-31B-it"
$env:LLM_TEMPERATURE = "0.2"
$env:LLM_STREAMING_DEFAULT = "0"
$env:LLM_SEND_TOP_K = "0"

# --- Graph / SQL dev ---
$env:APP_ENV = "dev"
$env:SQL_EXECUTOR_MODE = "stub"
$env:MASK_SQL = "0"
$env:SQL_LIMIT_MAX = "1000"

$uvicorn = Join-Path $ProjectRoot ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path $uvicorn)) {
	Write-Error "Chưa có .venv — tạo venv và pip install -r requirements.txt (xem README)."
}
Write-Host "run-dev: AUTH_DEV_BYPASS=1, uvicorn http://127.0.0.1:9000" -ForegroundColor Cyan
& $uvicorn "main:app" "--reload" "--host" "127.0.0.1" "--port" "9000"
