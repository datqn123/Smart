"""Run Task005 eval prompts and write ``eval_run_<timestamp>.jsonl`` (G-AI-TST).

Usage (from ``ai_python/``)::

    python tests/eval/run_eval.py

Output: ``docs/task005/04-tester/eval_run_<UTC>.jsonl``
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_AI_PYTHON = Path(__file__).resolve().parents[2]
if str(_AI_PYTHON) not in sys.path:
    sys.path.insert(0, str(_AI_PYTHON))

from tests.eval.task005_eval_checks import run_eval_case  # noqa: E402


def _load_prompts() -> list[dict[str, object]]:
    path = Path(__file__).resolve().parent / "prompts.jsonl"
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def main() -> int:
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _AI_PYTHON / "docs" / "task005" / "04-tester"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"eval_run_{ts}.jsonl"

    prompts = _load_prompts()
    passed = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for row in prompts:
            case_id = str(row["id"])
            ok, detail = run_eval_case(case_id)
            if ok:
                passed += 1
            rec = {
                "id": case_id,
                "ok": ok,
                "detail": detail,
                "capability": row.get("capability"),
                "base_scenario": row.get("base_scenario"),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(prompts)
    rate = (100.0 * passed / total) if total else 0.0
    print(f"Task005 eval: {passed}/{total} passed ({rate:.1f}%)")
    print(f"Wrote {out_path}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
