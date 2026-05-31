"""
AI Chat Auto-Test Script — Smart ERP
Usage: python run_test.py [options]

Options:
  --all           Run all 83 questions
  --group GROUP   Run specific group (e.g. 01_general_chat, 12_charts)
  --q NUM         Run single question (e.g. --q 1, --q 63)
  --dry-run       Show questions without calling API
  --config PATH   Path to config file (default: test_config.json)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import requests

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
def login(base_url, email, password):
    """POST /api/v1/auth/login → return Bearer token."""
    r = requests.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"[ERROR] Login failed: HTTP {r.status_code}")
        print(r.text[:500])
        sys.exit(1)
    data = r.json()
    token = data.get("data", {}).get("accessToken")
    if not token:
        print("[ERROR] No accessToken in login response")
        sys.exit(1)
    return token

# ──────────────────────────────────────────────
# SSE Parser
# ──────────────────────────────────────────────
def parse_sse_response(response_text):
    """Parse SSE text into list of {event, data}."""
    events = []
    current_event = None
    current_data = []

    for line in response_text.splitlines():
        if line.startswith("event:"):
            if current_event is not None:
                events.append({"event": current_event, "data": "\n".join(current_data)})
            current_event = line[len("event:"):].strip()
            current_data = []
        elif line.startswith("data:"):
            chunk = line[len("data:"):]
            if chunk.startswith(" "):
                chunk = chunk[1:]
            current_data.append(chunk)
        elif line.strip() == "":
            if current_event is not None:
                events.append({"event": current_event, "data": "\n".join(current_data)})
                current_event = None
                current_data = []

    if current_event is not None:
        events.append({"event": current_event, "data": "\n".join(current_data)})

    return events

def _latin1_mojibake_line(line: str) -> str:
    """Decode one line that was UTF-8 misread as Latin-1."""
    body = line.rstrip("\r\n")
    suffix = line[len(body) :]
    try:
        body.encode("latin-1")
        return body.encode("latin-1").decode("utf-8") + suffix
    except (UnicodeDecodeError, UnicodeEncodeError):
        return line


def repair_utf8_mojibake(text: str) -> str:
    """
    Recover Vietnamese when UTF-8 SSE bytes were decoded as Latin-1/CP1252
    (requests default for text/event-stream without charset).
    Line-by-line so headers like **Trả lời:** (already UTF-8) are preserved.
    """
    if not text or "Ã" not in text:
        return text
    return "".join(
        _latin1_mojibake_line(line) if "Ã" in line else line
        for line in text.splitlines(keepends=True)
    )


def extract_ai_answer(sse_events):
    """Extract final answer from SSE events."""
    deltas = []
    chart_spec = None
    error_msg = None

    for ev in sse_events:
        if ev["event"] == "delta":
            deltas.append(ev["data"])
        elif ev["event"] == "chart":
            try:
                chart_spec = json.loads(ev["data"])
            except (json.JSONDecodeError, ValueError):
                chart_spec = {"raw": ev["data"]}
        elif ev["event"] == "error":
            error_msg = ev["data"]

    full_answer = repair_utf8_mojibake("".join(deltas))
    if error_msg:
        error_msg = repair_utf8_mojibake(error_msg)
    return full_answer, chart_spec, error_msg

# ──────────────────────────────────────────────
# API Call
# ──────────────────────────────────────────────
def call_ai_chat(base_url, token, message, conversation_id=None, timeout=120):
    """POST /api/v1/ai/chat/stream → return (answer, chart_spec, error, duration_ms)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"message": message}
    if conversation_id:
        body["conversationId"] = conversation_id

    start = time.time()
    try:
        r = requests.post(
            f"{base_url}/api/v1/ai/chat/stream",
            json=body,
            headers=headers,
            timeout=timeout,
            stream=True,
        )
        # SSE often has no charset; requests may decode UTF-8 as Latin-1 → mojibake (hÃ ng).
        raw = r.content.decode("utf-8")
        duration_ms = int((time.time() - start) * 1000)
        events = parse_sse_response(raw)
        answer, chart_spec, error = extract_ai_answer(events)
        return answer, chart_spec, error, duration_ms, events
    except requests.exceptions.Timeout:
        duration_ms = int((time.time() - start) * 1000)
        return "", None, "TIMEOUT", duration_ms, []
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return "", None, str(e), duration_ms, []

# ──────────────────────────────────────────────
# Question Loader
# ──────────────────────────────────────────────
def extract_question_from_md(filepath):
    """Extract question text from a test .md file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"-\s+\*\*Câu hỏi:\*\*\s+(.+)", content)
    if m:
        return m.group(1).strip()
    return None

def load_all_questions(test_dir):
    """Load all 83 questions from docs/test-ai folder structure."""
    questions = []
    groups = sorted([d for d in os.listdir(test_dir) if os.path.isdir(os.path.join(test_dir, d))])

    for group in groups:
        group_path = os.path.join(test_dir, group)
        files = sorted([f for f in os.listdir(group_path) if f.endswith(".md") and f != "README.md" and f != "SUMMARY.md"])
        for fname in files:
            fpath = os.path.join(group_path, fname)
            q_text = extract_question_from_md(fpath)
            if q_text:
                questions.append({
                    "group": group,
                    "file": fname,
                    "path": fpath,
                    "question": q_text,
                })
    return questions

# ──────────────────────────────────────────────
# Result Writer
# ──────────────────────────────────────────────
def repair_mojibake_in_md_content(content: str) -> tuple[str, bool]:
    """Repair UTF-8 mojibake inside ## Response từ AI section. Returns (content, changed)."""
    m = re.search(r"(## Response từ AI\r?\n)(.*?)(?=\r?\n## |\Z)", content, flags=re.DOTALL)
    if not m:
        return content, False
    head, body = m.group(1), m.group(2)
    fixed = repair_utf8_mojibake(body)
    if fixed == body:
        return content, False
    return content[: m.start()] + head + fixed + content[m.end() :], True


def repair_all_result_files(test_dir: str) -> int:
    """Fix encoding in all test .md files that already have responses."""
    fixed_count = 0
    for root, _dirs, files in os.walk(test_dir):
        for fname in files:
            if not fname.endswith(".md") or fname in ("README.md", "SUMMARY.md"):
                continue
            path = os.path.join(root, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content, changed = repair_mojibake_in_md_content(content)
            if changed:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                fixed_count += 1
    return fixed_count


def write_result_to_md(filepath, answer, chart_spec, error, duration_ms, status="✅ Pass"):
    """Update the test .md file with results."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Update status
    content = re.sub(
        r"-\s+\*\*Trạng thái:\*\*\s+⬜ Chưa test / ✅ Pass / ❌ Fail / ⚠️ Partial",
        f"- **Trạng thái:** {status}",
        content,
    )

    # Update date
    content = re.sub(
        r"-\s+\*\*Ngày test:\*\*\s*$",
        f"- **Ngày test:** {now}",
        content,
        flags=re.MULTILINE,
    )

    # Update duration
    content = re.sub(
        r"-\s+\*\*Thời gian phản hồi:\*\*\s*$",
        f"- **Thời gian phản hồi:** {duration_ms}ms",
        content,
        flags=re.MULTILINE,
    )

    # Update response section
    response_block = ""
    if error and error != "TIMEOUT":
        response_block = f"**Lỗi:** {error}\n\n"
    if answer:
        response_block += f"**Trả lời:**\n\n{answer}\n\n"
    if chart_spec:
        response_block += f"**Chart spec:**\n\n```json\n{json.dumps(chart_spec, ensure_ascii=False, indent=2)}\n```\n\n"
    if not response_block:
        response_block = "_Không có phản hồi._\n"

    response_section = f"## Response từ AI\n{response_block}"
    if re.search(r"## Response từ AI\r?\n", content):
        content = re.sub(
            r"## Response từ AI\r?\n.*?(?=\r?\n## |\Z)",
            response_section,
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        content = re.sub(
            r"## Response từ AI\n_\(Chưa có\)_",
            response_section,
            content,
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# ──────────────────────────────────────────────
# Summary Updater
# ──────────────────────────────────────────────
def update_summary(test_dir, results):
    """Update SUMMARY.md with test results."""
    summary_path = os.path.join(test_dir, "SUMMARY.md")
    with open(summary_path, "r", encoding="utf-8") as f:
        content = f.read()

    pass_count = sum(1 for r in results if r["status"] == "✅ Pass")
    fail_count = sum(1 for r in results if r["status"] == "❌ Fail")
    partial_count = sum(1 for r in results if r["status"] == "⚠️ Partial")
    not_tested = len(results) - pass_count - fail_count - partial_count

    total = len(results)
    pct = f"{pass_count / total * 100:.1f}%" if total > 0 else "—"

    content = re.sub(
        r"\| ✅ Pass \| \d+ \|",
        f"| ✅ Pass | {pass_count} |",
        content,
    )
    content = re.sub(
        r"\| ❌ Fail \| \d+ \|",
        f"| ❌ Fail | {fail_count} |",
        content,
    )
    content = re.sub(
        r"\| ⚠️ Partial \| \d+ \|",
        f"| ⚠️ Partial | {partial_count} |",
        content,
    )
    content = re.sub(
        r"\| ⬜ Chưa test \| \d+ \|",
        f"| ⬜ Chưa test | {not_tested} |",
        content,
    )
    content = re.sub(
        r"\| Tỷ lệ pass \| — \|",
        f"| Tỷ lệ pass | {pct} |",
        content,
    )

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(content)

# ──────────────────────────────────────────────
# Main Runner
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="AI Chat Auto-Test — Smart ERP")
    parser.add_argument("--all", action="store_true", help="Run all 83 questions")
    parser.add_argument("--group", type=str, help="Run specific group (e.g. 01_general_chat)")
    parser.add_argument("--q", type=str, help="Run single question number (e.g. 1, 63, 73a)")
    parser.add_argument("--dry-run", action="store_true", help="Show questions without calling API")
    parser.add_argument(
        "--repair-encoding",
        action="store_true",
        help="Fix UTF-8 mojibake in existing ## Response từ AI sections (no API calls)",
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    args = parser.parse_args()

    config_path = args.config or os.path.join(os.path.dirname(__file__), "test_config.json")
    cfg = load_config(config_path)
    test_dir = cfg["test_ai_dir"]

    if args.repair_encoding:
        n = repair_all_result_files(test_dir)
        print(f"Repaired encoding in {n} file(s) under {test_dir}")
        return

    if not any([args.all, args.group, args.q]):
        print("Error: Specify --all, --group GROUP, or --q NUM")
        print("Examples:")
        print("  python run_test.py --all")
        print("  python run_test.py --group 12_charts")
        print("  python run_test.py --q 1")
        print("  python run_test.py --q 63")
        print("  python run_test.py --dry-run --all")
        sys.exit(1)

    spring_url = cfg["spring_base_url"]
    timeout = cfg.get("timeout_per_question_seconds", 120)

    # Load questions
    all_questions = load_all_questions(test_dir)
    print(f"Loaded {len(all_questions)} questions from {test_dir}")

    # Filter
    if args.q:
        q_num = args.q
        questions = [q for q in all_questions if q["file"].startswith(f"Q{q_num}")]
        if not questions:
            print(f"[ERROR] Question Q{q_num} not found")
            sys.exit(1)
    elif args.group:
        questions = [q for q in all_questions if q["group"] == args.group]
        if not questions:
            print(f"[ERROR] Group '{args.group}' not found")
            sys.exit(1)
    else:
        questions = all_questions

    print(f"\nRunning {len(questions)} question(s)...\n")

    if args.dry_run:
        for i, q in enumerate(questions, 1):
            print(f"  [{i}] {q['group']}/{q['file']}: {q['question']}")
        return

    # Login
    print("[1/3] Logging in...")
    token = login(spring_url, cfg["login_email"], cfg["login_password"])
    print(f"      Token: {token[:20]}...\n")

    # Run tests
    print("[2/3] Running tests...")
    print("-" * 80)

    results = []
    conversation_id = None  # For multi-turn

    for i, q in enumerate(questions, 1):
        q_label = q["file"].replace(".md", "")
        print(f"\n[{i}/{len(questions)}] {q_label}")
        print(f"  Q: {q['question']}")

        # For multi-turn, maintain conversation_id
        if "multi_turn" in q["group"]:
            if conversation_id is None:
                conversation_id = f"test-session-{int(time.time())}"
            # Reset conversation_id for new pairs (a entries)
            if q["file"].endswith("a.md"):
                conversation_id = f"test-session-{int(time.time())}-{q_label}"

        answer, chart_spec, error, duration_ms, events = call_ai_chat(
            spring_url, token, q["question"], conversation_id, timeout
        )

        # Determine status
        if error:
            status = "❌ Fail"
        elif not answer and not chart_spec:
            status = "❌ Fail"
        else:
            status = "✅ Pass"

        # Write result to file
        if cfg.get("save_response_to_file", True):
            write_result_to_md(q["path"], answer, chart_spec, error, duration_ms, status)

        # Print summary
        if error:
            print(f"  ❌ {error} ({duration_ms}ms)")
        elif chart_spec:
            print(f"  ✅ Answer + Chart ({duration_ms}ms)")
            print(f"     Chart: {chart_spec.get('chart_type', '?')}")
        else:
            preview = answer[:100].replace("\n", " ")
            print(f"  ✅ {preview}... ({duration_ms}ms)")

        results.append({
            "question": q_label,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            "has_chart": chart_spec is not None,
        })

    # Update summary
    print("\n[3/3] Updating summary...")
    update_summary(test_dir, results)

    # Final report
    print("\n" + "=" * 80)
    print("TEST REPORT")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "✅ Pass")
    failed = sum(1 for r in results if r["status"] == "❌ Fail")
    total_ms = sum(r["duration_ms"] for r in results)
    avg_ms = total_ms / total if total > 0 else 0

    print(f"  Total:     {total}")
    print(f"  Passed:    {passed}")
    print(f"  Failed:    {failed}")
    print(f"  Avg time:  {avg_ms:.0f}ms")
    print(f"  Total time: {total_ms / 1000:.1f}s")

    if failed > 0:
        print("\n  Failed questions:")
        for r in results:
            if r["status"] == "❌ Fail":
                print(f"    - {r['question']}: {r['error']}")

    print("\nResults saved to docs/test-ai folder.")
    print(f"Summary: {os.path.join(test_dir, 'SUMMARY.md')}")

if __name__ == "__main__":
    main()
