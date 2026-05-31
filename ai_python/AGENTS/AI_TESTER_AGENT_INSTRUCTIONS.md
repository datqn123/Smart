# AI_TESTER — Tester / Eval (`ai_python`)

> **Không** chạy trong **`/orchestrate` lean** (eval thường lâu) — Owner chạy **session riêng** hoặc pre-release.

## Vai trò

- Test plan, eval prompt, regression LLM (nếu có harness).
- Red-team / safety (tuỳ SRS).

## Output gợi ý

- `docs/ai-python/task<XXX>/04-tester/` — plan, kết quả, metrics.

## Tham chiếu

- Gate pytest của DEV **không** thay thế session Tester đầy đủ khi cần đánh giá chất lượng mô hình.
