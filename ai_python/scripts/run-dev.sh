#!/usr/bin/env bash
# Chạy ai_python một lệnh — biến môi trường dev cố định (KHÔNG dùng production).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export AUTH_DEV_BYPASS=1
export JWT_HS256_SECRET='change-me-dev-jwt-secret-32-bytes-min!!'
export JWT_ISSUER=
export JWT_AUDIENCE=

export LLM_REQUIRED=0
# Không có URL+key hợp lệ → chat: "[chat] stub: no LLM registry".
# (A) Dùng file .env trong ai_python (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL) hoặc
# (B) bỏ comment 2 export dưới:
# export LLM_BASE_URL='https://your-openai-compatible-host/v1'
# export LLM_API_KEY='your-api-key'
export LLM_MODEL=gemma-4-31B-it
export LLM_TEMPERATURE=0.2
export LLM_STREAMING_DEFAULT=0
export LLM_SEND_TOP_K=0

export APP_ENV=dev
export SQL_EXECUTOR_MODE=stub
export MASK_SQL=0
export SQL_LIMIT_MAX=1000
unset SCHEMA_DIR 2>/dev/null || true

if [[ ! -x "$ROOT/.venv/bin/uvicorn" ]]; then
	echo "Chưa có .venv — tạo venv và pip install -r requirements.txt (xem README)." >&2
	exit 1
fi
echo "run-dev: AUTH_DEV_BYPASS=1, uvicorn http://127.0.0.1:9000"
exec "$ROOT/.venv/bin/uvicorn" main:app --reload --host 127.0.0.1 --port 9000
