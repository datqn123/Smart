# MANUAL_UNIT_TEST — Task005 (smoke checklist)

## Automated (executed)

| Suite | Command | Result |
| :--- | :--- | :--- |
| Task005 pytest | `pytest tests/ -k task005 -q` | **93 passed**, 2 deselected |
| G-AI-TST eval JSONL | `python tests/eval/run_eval.py` | **38/38** (100%) — see `eval_run_20260509T053858Z.jsonl` |

## Manual / FE (SRS: out of scope)

Task005 v1 has **no** browser chat, **no** Excel upload UI, **no** SSE stream (SRS §2). The generic AI_TESTER “open browser FE chat, upload Excel, approve flow” item is **N/A** for this slice.

## Operator sanity (optional, ~5 min)

1. From repo root `ai_python/`, with valid MCP config when available: run `python -m app.cli.task005_corpus_job --help` and confirm argparse renders.
2. Inspect `ai_python/data/rag_corpus/` (or `--corpus-root`) after a real run — expect `erp_schema/catalog__*.json`, `erp_template_health/health__*.json`, `index/index__*.json`.
