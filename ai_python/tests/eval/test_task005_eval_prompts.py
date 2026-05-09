"""Parametrised eval over ``prompts.jsonl`` (same checks as ``run_eval.py``)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.eval.task005_eval_checks import run_eval_case


def _prompt_rows() -> list[dict[str, object]]:
    path = Path(__file__).resolve().parent / "prompts.jsonl"
    out: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


@pytest.mark.parametrize("row", _prompt_rows(), ids=lambda r: str(r["id"]))
def test_task005_eval_prompt(row: dict[str, object]) -> None:
    case_id = str(row["id"])
    ok, detail = run_eval_case(case_id)
    assert ok, f"{case_id}: {detail}"
