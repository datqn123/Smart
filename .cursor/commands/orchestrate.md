---
name: orchestrate
description: Auto-run AI agent chain (BA → PM → TECH_LEAD → DEV → CODE_REVIEWER → BRIDGE → TESTER → DOC_SYNC) for an ai_python feature. HITL only at AI_PLANNER's option A/B/C. Auto-loop on Block max 3 rounds. Budget cap escalate.
---

# /orchestrate — Auto-runner cho ai_python

> Driver thực thi chuỗi role theo [`ai_python/AGENTS/WORKFLOW_RULE.md`](../../ai_python/AGENTS/WORKFLOW_RULE.md). Bạn (driver agent) đọc file này + Workflow + Registry, rồi tuần tự launch subagent qua **Task tool** (`subagent_type=generalPurpose`) cho từng role.

## Tham số (parse từ user message)

```text
/orchestrate Task=<id?> Brief="<mô tả ngắn>" [Mode=run|dry-run] [Budget=<n=20>] [SkipPlanner=false]
```

- `Task` (optional): nếu rỗng → AI_PM tự cấp ID Task tiếp theo.
- `Brief`: mô tả tính năng cho AI_PLANNER (bắt buộc nếu `SkipPlanner=false`).
- `Mode`: `run` (mặc định, launch subagent thật) | `dry-run` (in plan từng bước, không launch).
- `Budget`: trần số lần invoke subagent. Mặc định 20. Vượt → escalate.
- `SkipPlanner`: nếu PRD đã có sẵn cho task → bỏ qua planner.

## Driver state (giữ trong message history của driver)

```yaml
task_id: <Task???>
task_slug: <slug>
artifacts:
  prd: <path?>
  srs: <path?>
  adr: <path?>
  task_file: <path?>
  code_review: <path?>
  bridge: <path?>
  tester: <folder?>
  sync_report: <path?>
  audit: <path?>
loop_count:
  cr: 0
  tester: 0
  bridge: 0
budget_used: 0
budget_cap: 20
current_gate: G-AI-PLAN
```

Update state sau mỗi subagent return; in lại state ngắn cho user mỗi gate xong.

## Quy tắc tuyệt đối (không vi phạm)

1. **HITL duy nhất ở AI_PLANNER**: sau khi planner trả option A/B/C → DỪNG, in prompt yêu cầu Owner gõ `A` / `B` / `C` / `pick optimal`. **Không** hỏi user ở role nào khác.
2. **STOP rules** từng role (xem mục 8 file `*_INSTRUCTIONS.md`): match → escalate Owner ngay, không loop.
3. **Auto-loop**: CR/TST/BRIDGE Block → relaunch DEV với feedback đính kèm, tăng `loop_count.<role>`. Vượt 3 → STOP escalate.
4. **Budget**: mỗi lần launch subagent → `budget_used += 1`. Vượt cap → STOP escalate.
5. **Không sửa file ngoài `ai_python/`**: nếu role nào trả output đụng `backend/` hoặc `frontend/` → STOP cross-scope.
6. **Không tự gõ `A/B/C` thay user** (ngay cả khi `pick optimal` được Owner uỷ quyền — vẫn để planner subagent quyết, driver chỉ relay).

## Pipeline (mỗi step = launch 1 subagent qua Task tool)

### Step 0 — Pre-flight

1. Read [`ai_python/AGENTS/WORKFLOW_RULE.md`](../../ai_python/AGENTS/WORKFLOW_RULE.md) + [`ai_python/AGENTS/AGENT_REGISTRY.md`](../../ai_python/AGENTS/AGENT_REGISTRY.md).
2. Verify `ai_python/AGENTS/`, `ai_python/docs/`, `ai_python/TASKS/` tồn tại.
3. **Driver không dùng git**: không chạy lệnh git, không lưu branch/commit/hash, không `diff` / merge / push. Quản lý VCS là việc Owner (ngoài `/orchestrate`).
4. Nếu `Mode=dry-run` → in plan từng step bên dưới + dự kiến artifact, **không** launch subagent. Stop.

### Step 1 — AI_PLANNER (HITL gate)

- Skip nếu `SkipPlanner=true` và PRD path đã có ở artifacts.prd.
- Launch:
  ```
  Task tool → subagent_type=generalPurpose
  prompt = nội dung @AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md +
           "Brief: <Brief>" +
           "Output PRD tới ai_python/docs/prd/PRD_<slug>.md theo format §4 PRD."
  ```
- Subagent trả ≥ 2 option A/B/C + recommendation.
- **DỪNG**, in cho user:
  > Planner đã đề xuất options A/B/C (xem PRD <path>). Vui lòng gõ `A`, `B`, `C` hoặc `pick optimal` để tiếp tục.
- Đợi user reply. Sau khi nhận → relaunch planner với choice → planner output PRD final với option đã chọn → set `artifacts.prd`.

### Step 2 — AI_BA (G-AI-BA)

- Launch subagent với prompt = nội dung [`ai_python/AGENTS/AI_BA_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_BA_AGENT_INSTRUCTIONS.md) + I/O Contract instantiate (`PRD_PATH`, `TASK_ID`, `TASK_SLUG`, `OUT_PATH`, `MCP_PHASE=0`).
- Verify gate exit §5 của BA. Match STOP rule → escalate. Pass → set `artifacts.srs`.

### Step 3 — AI_PM (G-AI-PM)

- Launch với [`AI_PM_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_PM_AGENT_INSTRUCTIONS.md). Slot: `SRS_PATH`, `TASK_ID`, `OUT_TASK_FILE`, `OUT_TASK_FOLDER`.
- Verify `Task<XXX>.md` + folder `ai_python/docs/task<XXX>/` đúng cấu trúc → set `artifacts.task_file`.

### Step 4 — AI_TECH_LEAD (G-AI-TL)

- Launch với [`AI_TECH_LEAD_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_TECH_LEAD_AGENT_INSTRUCTIONS.md). Slot: `SRS_PATH`, `TASK_FILE`, `ADR_NUMBER` (driver đọc folder `docs/adr/` lấy số kế tiếp), `OUT_PATH`.
- Verify NFR có 5 mục số. Pass → set `artifacts.adr`.

### Step 5 — AI_DEVELOPER (G-AI-DEV)

- Launch với [`AI_DEVELOPER_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_DEVELOPER_AGENT_INSTRUCTIONS.md). Slot: `TASK_FILE`, `SRS_PATH`, `ADR_PATH`, `LOOP_FEEDBACK` (rỗng lần đầu). Driver **không** nhồi SOP dài vào prompt — subagent đọc file; driver chỉ path artifact + `LOOP_FEEDBACK` nếu có.
- Verify gate exit §5 của DEV (pytest + coverage + ruff + mypy — **không** kiểm branch/commit). Pass → đi tiếp.

### Step 6 — AI_CODE_REVIEWER (G-AI-CR) — auto-loop

```
loop:
  launch AI_CODE_REVIEWER (iteration = loop_count.cr + 1)
  read CODE_REVIEW report verdict
  if verdict == PASS: break
  else if loop_count.cr >= 3: escalate STOP
  else if STOP rule matched: escalate STOP
  else:
    loop_count.cr += 1
    relaunch AI_DEVELOPER với LOOP_FEEDBACK = path report
    relaunch AI_CODE_REVIEWER (iteration += 1)
```

- Slot CR: `SRS_PATH`, `ADR_PATH`, `OUT_PATH`, `ITERATION`, `TASK_FILE` (path Task chain để CR lấy nhãn / scope).

### Step 7 — AI_BRIDGE (G-AI-BRIDGE) — conditional

- Skip nếu SRS + `Task<XXX>.md` không yêu cầu thay đổi contract SSE/MCP cho task này (driver đọc nhanh mục API/Design trong SRS/Task — **không** dùng git diff). Nếu không chắc → launch AI_BRIDGE `Mode=verify` (an toàn hơn skip nhầm).
- Nếu chạm → launch [`AI_BRIDGE_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_BRIDGE_AGENT_INSTRUCTIONS.md) `Mode=verify`.
- Drift `Block` ở `ai_python ↔ SRS` → loop về DEV (cùng cơ chế CR, đếm `loop_count.bridge`).
- Drift ngoài (Spring/FE) → ghi handoff section, **không** loop.

### Step 8 — AI_TESTER (G-AI-TST) — auto-loop

```
loop:
  launch AI_TESTER
  if pass: break
  else if loop_count.tester >= 3: escalate
  else if HITL bypass red-team passes (security STOP): escalate IMMEDIATELY
  else:
    loop_count.tester += 1
    relaunch AI_DEVELOPER với LOOP_FEEDBACK = report path
    rerun AI_CODE_REVIEWER (1 vòng nhanh — không đếm vào loop_count.cr)
    rerun AI_TESTER
```

- Slot: `SRS_PATH`, `ADR_PATH`, `TASK_ID`, `OUT_FOLDER`, `EVAL_PROMPTS`.

### Step 9 — AI_DOC_SYNC (G-AI-DS)

- Launch với [`AI_DOC_SYNC_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_DOC_SYNC_AGENT_INSTRUCTIONS.md). Slot: `SCOPE=Task<XXX>`, `OUT_PATH`.
- 0 drift Block → pass.

### Step 10 — AI_ORCHESTRATOR (G-AI-OR final)

- Launch với [`AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md). Slot: `MODE=final`, `TASK_ID`, `OUT_PATH=ai_python/docs/orchestration/AUDIT_<Task>_final.md`.
- Verdict `PASS` → toàn task xong.
- Verdict `WARN` → in danh sách warn, hỏi Owner accept (đây là **HITL ngoại lệ duy nhất** sau planner — nếu Owner muốn skip Warn → driver chấp nhận và đóng task).
- Verdict `FAIL` → escalate Owner full report.

## Auto-loop snippet (mã giả runner dùng)

```python
def run_with_loop(role_launch_fn, gate_check_fn, loop_key, max_loops=3, dev_relaunch_fn=None):
    iteration = 1
    while True:
        report = role_launch_fn(iteration=iteration)
        verdict = gate_check_fn(report)
        if verdict == "PASS":
            return report
        if verdict == "STOP":
            escalate(report)
            return None
        if state["loop_count"][loop_key] >= max_loops:
            escalate(f"{loop_key} loop > {max_loops}", report)
            return None
        state["loop_count"][loop_key] += 1
        if dev_relaunch_fn:
            dev_relaunch_fn(loop_feedback=report.path)
        iteration += 1
```

## Final summary template (driver in cho user khi xong)

```text
## /orchestrate done — Task<XXX>
- PRD: <link>
- SRS: <link>
- Task chain: <link>
- ADR: <link>
- CR iterations: <n>
- Bridge: <link or n/a>
- Tester iterations: <n>; Eval pass-rate: <%>; HITL bypass: 0%
- Doc Sync: <link>
- Final audit: <link>
- Budget used: <m>/<cap>
```

## Dry-run output template

```text
## /orchestrate DRY-RUN — Task=<id> Brief="..."
1. AI_PLANNER → ai_python/docs/prd/PRD_<slug>.md (HITL: A/B/C)
2. AI_BA → ai_python/docs/srs/SRS_AI_<task>_<slug>.md
3. AI_PM → ai_python/TASKS/<task>.md + ai_python/docs/task<XXX>/
4. AI_TECH_LEAD → ai_python/docs/adr/ADR-<NNN>-<slug>.md
5. AI_DEVELOPER → `ai_python/app/**` + tests (SOP §3: 3 bước — đọc → code+test → gate §5 một lượt)
6. AI_CODE_REVIEWER → ai_python/docs/<task>/05-code-review/CODE_REVIEW_<task>.md (auto-loop ≤3)
7. AI_BRIDGE (if SSE/MCP changed) → ai_python/docs/api/bridge/BRIDGE_AI_<task>_<slug>.md
8. AI_TESTER → ai_python/docs/<task>/04-tester/* (auto-loop ≤3)
9. AI_DOC_SYNC → ai_python/docs/sync_reports/SYNC_REPORT_<task>_<date>.md
10. AI_ORCHESTRATOR (final) → ai_python/docs/orchestration/AUDIT_<task>_final.md
Budget cap: 20. Estimated invocations: 10–18 (no loops). With max loops: ~25 (sẽ escalate).
```

## Lưu ý kỹ thuật

- Khi launch subagent qua Task tool, truyền (a) nội dung file `*_INSTRUCTIONS.md` **hoặc** `@path` đủ để subagent đọc trong repo, (b) I/O Contract instantiate, (c) đường dẫn artifact (không paste full PRD/SRS). **AI_DEVELOPER**: ưu tiên `@ai_python/AGENTS/AI_DEVELOPER_AGENT_INSTRUCTIONS.md` + slot path — không paste full instructions để tránh nhân đôi SOP.
- Subagent không thấy lịch sử chat của driver — driver phải ghi rõ context cần thiết trong prompt.
- Khi loop, đính kèm **path** của report cũ + 5–10 dòng quote Block nổi bật, không paste full report (tiết kiệm token).
- Sau mỗi subagent xong: driver ghi 1 dòng vào terminal-log dạng `[gate=G-AI-DEV iter=1 budget=5/20] PASS/BLOCK <summary>`.

## Khi gặp escalation

In cho Owner:

```text
## /orchestrate ESCALATED at <gate>
Reason: <STOP rule | budget exceeded | loop > 3>
State: <yaml dump>
Last report: <link>
Suggested next steps:
1. ...
2. ...
```

Đợi Owner quyết định: `/orchestrate resume Task=<id>` (rerun từ gate kế) hoặc abort.
