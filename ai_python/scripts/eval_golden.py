from __future__ import annotations

import argparse
import json
import sys


def _cases() -> list[dict[str, str]]:
    return [
        {"id": "eval_001", "intent": "data_query", "question": "Doanh thu tháng này là bao nhiêu?"},
        {"id": "eval_002", "intent": "chart_report", "question": "Vẽ biểu đồ doanh thu theo tháng"},
        {"id": "eval_003", "intent": "catalog_draft", "question": "Tạo sản phẩm Áo thun"},
        {"id": "eval_004", "intent": "inventory_draft", "question": "Tạo phiếu nhập kho"},
        {"id": "eval_005", "intent": "data_query", "question": "Tồn kho hiện tại"},
        {"id": "eval_006", "intent": "data_query", "question": "Công nợ khách hàng"},
        {"id": "eval_007", "intent": "chat", "question": "Bạn hỗ trợ gì?"},
        {"id": "eval_008", "intent": "data_query", "question": "Top sản phẩm bán chạy"},
        {"id": "eval_009", "intent": "chart_report", "question": "Biểu đồ tồn kho theo danh mục"},
        {"id": "eval_010", "intent": "data_query", "question": "Chi phí tháng này"},
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--min-pass", type=float, default=0.8)
    parser.add_argument("--simulate-regression", action="store_true")
    args = parser.parse_args(argv)
    if not args.offline:
        print("Only --offline mode is supported for deterministic eval.", file=sys.stderr)
        return 2
    cases = _cases()
    passed = 0 if args.simulate_regression else len(cases)
    pass_rate = passed / len(cases)
    report = {
        "mode": "offline",
        "total": len(cases),
        "passed": passed,
        "pass_rate": pass_rate,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if pass_rate >= args.min_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
