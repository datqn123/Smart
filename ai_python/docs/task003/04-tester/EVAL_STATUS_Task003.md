# Eval status — Task003

- Seed prompts: `ai_python/docs/task003/eval_seed_e1_e5.jsonl` (SRS §6 #E1–#E5)
- Automated tests: `pytest` 16 passed; integration matrix `tests/integration/test_task003_stream_matrix.py` covers MCP/SSE branching với scripted clients.
- **G-AI-TST** (≥30 prompt, ≥80% pass against live LLM + red-team MCP): **chưa chạy** trong phiên này — cần môi trường `FPT_MKP_*` + MCP thật. Không chứng minh HITL bypass; stub path không mutate DB.
