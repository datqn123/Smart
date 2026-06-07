# Smoke test cho harness loop THẬT (LLM + Spring thật từ .env).
# Tiền đề: ai_python đang chạy (xem hướng dẫn start ở dưới), Spring 8080 + Postgres đang chạy.
# Dùng: .\scripts\smoke-harness.ps1            (mặc định http://127.0.0.1:9000)
#        .\scripts\smoke-harness.ps1 -BaseUrl http://127.0.0.1:9000
param([string]$BaseUrl = "http://127.0.0.1:9000")
$ErrorActionPreference = "Stop"

function Send-Chat([string]$label, [string]$msg) {
    $body = @{
        message  = $msg
        metadata = @{ user_id = "smoke"; tenant_id = "t1"; thread_id = [guid]::NewGuid().ToString(); schema_version = "v1" }
    } | ConvertTo-Json -Compress -Depth 6
    $cid = [guid]::NewGuid().ToString()
    Write-Host "`n=== [$label] $msg ===" -ForegroundColor Cyan
    # curl.exe -N: stream SSE không buffer (Invoke-RestMethod sẽ gom hết, không thấy progress).
    curl.exe -sN -X POST "$BaseUrl/api/v1/ai/chat/stream" `
        -H "Content-Type: application/json" `
        -H "X-Correlation-Id: $cid" `
        -H "Authorization: Bearer dev" `
        --data $body
    Write-Host ""
}

Write-Host "Health:" -ForegroundColor Yellow
curl.exe -s "$BaseUrl/health"; Write-Host ""

# 1) data_query — kỳ vọng: progress -> (data_table?) -> delta_full -> done, có số liệu thật.
Send-Chat "data_query" "doanh thu tháng này là bao nhiêu"
# 2) schema_explore — kỳ vọng: tool schema_explore chạy, trả mô tả bảng.
Send-Chat "schema_explore" "hệ thống có những bảng nào liên quan đơn hàng"
# 3) HITL draft — kỳ vọng: event 'draft', KHÔNG có 'done' (chờ xác nhận).
Send-Chat "catalog_draft" "tạo sản phẩm Áo thun size M giá bán 150000"
# 4) out-of-scope — kỳ vọng: từ chối lịch sự, gợi ý phạm vi ERP, không gọi tool.
Send-Chat "out_of_scope" "thời tiết Hà Nội hôm nay thế nào"
