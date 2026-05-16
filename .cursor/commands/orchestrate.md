---
name: orchestrate
description: Lean auto-run cho ai_python — Planner → BA → PM → Tech Lead → Dev → Code Reviewer (HITL chỉ ở Planner A/B/C). CR Block → DEV tối đa 3 vòng. Không chạy Tester/Bridge/DocSync/Orchestrator trong luồng mặc định.
---

# /orchestrate — Auto-runner (lean) cho ai_python

> Driver thực thi **chuỗi tối thiểu**: **AI_PLANNER → AI_BA → AI_PM → AI_TECH_LEAD → AI_DEVELOPER → AI_CODE_REVIEWER**. Đọc [`ai_python/AGENTS/AGENT_REGISTRY.md`](../../ai_python/AGENTS/AGENT_REGISTRY.md) + instruction từng role; launch subagent qua **Task tool** (`subagent_type=generalPurpose`).

**Mặc định không gồm**: AI_TESTER (eval lâu), AI_BRIDGE, AI_DOC_SYNC, AI_ORCHESTRATOR final — chỉ chạy sau khi Owner chủ động yêu cầu hoặc task có ràng buộc contract/bàn giao.

## Tham số (parse từ user message)

```text
/orchestrate Task=<id?> Brief="<mô tả ngắn>" [Mode=run|dry-run] [Budget=<n=14>] [SkipPlanner=false]
/orchestrate Task=<id?> Brief="<mô tả ngắn>" [Mode=run ] [Budget=<n=14>] [SkipPlanner=false]
```

- `Task` (optional): nếu rỗng → AI_PM tự cấp ID Task tiếp theo.
- `Brief`: mô tả tính năng cho AI_PLANNER (bắt buộc nếu `SkipPlanner=false`).
- `Mode`: `run` (mặc định) | `dry-run` (in plan, không launch).
- `Budget`: trần số lần invoke subagent. Mặc định **14** (đủ lean + vài vòng CR). Vượt → escalate.
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
loop_count:
  cr: 0
budget_used: 0
budget_cap: 14
current_gate: G-AI-PLAN
```

Update state sau mỗi subagent return; in state ngắn cho user mỗi gate xong.

## Quy tắc tuyệt đối

1. **HITL duy nhất ở AI_PLANNER**: sau option A/B/C → DỪNG, Owner gõ `A` / `B` / `C` / `pick optimal`. **Không** hỏi user ở role khác trong luồng lean.
2. **STOP rules** từng role (`*_INSTRUCTIONS.md`): match → escalate Owner, không loop.
3. **Auto-loop chỉ Code Review**: CR `BLOCK` → relaunch DEV với feedback; `loop_count.cr` tối đa **3** → escalate.
4. **Budget**: mỗi launch subagent → `budget_used += 1`. Vượt cap → escalate.
5. **Không sửa file ngoài `ai_python/`**: output đụng `backend/` hoặc `frontend/` → STOP cross-scope.
6. **Không tự gõ `A/B/C` thay user**.

## Pipeline (mỗi step = 1 subagent qua Task tool)

### Step 0 — Pre-flight

1. Read [`ai_python/AGENTS/WORKFLOW_RULE.md`](../../ai_python/AGENTS/WORKFLOW_RULE.md) + [`ai_python/AGENTS/AGENT_REGISTRY.md`](../../ai_python/AGENTS/AGENT_REGISTRY.md).
2. Verify `ai_python/AGENTS/`, `ai_python/docs/`, `ai_python/TASKS/` tồn tại.
3. **Driver không dùng git**: không chạy git, không diff/merge/push.
4. `Mode=dry-run` → in dry-run template bên dưới, **không** launch. Stop.

### Step 1 — AI_PLANNER (HITL gate)

- Skip nếu `SkipPlanner=true` và `artifacts.prd` đã có path hợp lệ.
- Launch: `@ai_python/AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md` + `Brief` + output PRD `ai_python/docs/prd/PRD_<slug>.md`.
- **DỪNG** → User chọn A/B/C hoặc `pick optimal` → relaunch planner finalize PRD → `artifacts.prd`.

### Step 2 — AI_BA (G-AI-BA)

- [`AI_BA_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_BA_AGENT_INSTRUCTIONS.md) + contract: `PRD_PATH`, `TASK_ID`, `TASK_SLUG`, `OUT_PATH`, `MCP_PHASE=0`.
- Gate BA §5 → STOP nếu match → else `artifacts.srs`.

### Step 3 — AI_PM (G-AI-PM)

- [`AI_PM_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_PM_AGENT_INSTRUCTIONS.md) — `SRS_PATH`, `TASK_ID`, `OUT_TASK_FILE`, `OUT_TASK_FOLDER`.
- Verify `Task<XXX>.md` + `ai_python/docs/task<XXX>/` → `artifacts.task_file`.

### Step 4 — AI_TECH_LEAD (G-AI-TL)

- [`AI_TECH_LEAD_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_TECH_LEAD_AGENT_INSTRUCTIONS.md) — `SRS_PATH`, `TASK_FILE`, `ADR_NUMBER` (số kế từ `ai_python/docs/adr/`), `OUT_PATH`.
- NFR 5 mục → `artifacts.adr`.

### Step 5 — AI_DEVELOPER (G-AI-DEV)

- [`AI_DEVELOPER_AGENT_INSTRUCTIONS.md`](../../ai_python/AGENTS/AI_DEVELOPER_AGENT_INSTRUCTIONS.md) — `TASK_FILE`, `SRS_PATH`, `ADR_PATH`, `LOOP_FEEDBACK` (rỗng lần đầu).
- Gate DEV §5 (pytest, coverage, ruff, mypy theo instruction).

### Step 6 — AI_CODE_REVIEWER (G-AI-CR) — auto-loop (duy nhất)

```
loop:
  launch AI_CODE_REVIEWER (iteration = loop_count.cr + 1)
  if verdict == PASS: break → DONE lean pipeline
  if STOP rule: escalate
  if loop_count.cr >= 3: escalate
  loop_count.cr += 1
  relaunch AI_DEVELOPER với LOOP_FEEDBACK = path CODE_REVIEW report
```

- Slot CR: `SRS_PATH`, `ADR_PATH`, `OUT_PATH`, `ITERATION`, `TASK_FILE`.

## Phần mở rộng (không chạy trong `/orchestrate` mặc định)

Chỉ khi Owner ghi rõ trong message (ví dụ `PostSteps=bridge` hoặc chạy session riêng):

| Role | Khi nào |
|------|--------|
| AI_BRIDGE | Đổi contract SSE/MCP — verify drift |
| AI_TESTER | Eval / red-team — **tốn thời gian**, chạy định kỳ hoặc trước release |
| AI_DOC_SYNC | Đồng bộ doc sau khi codebase ổn định |
| AI_ORCHESTRATOR final | Audit tổng hợp + WARN/FAIL — HITL nếu WARN |

## Auto-loop snippet (chỉ CR)

```python
def cr_loop(state, launch_cr, launch_dev, max_loops=3):
    iteration = 1
    while True:
        report = launch_cr(iteration=iteration)
        if report.verdict == "PASS":
            return report
        if report.verdict == "STOP":
            escalate(report)
            return None
        if state["loop_count"]["cr"] >= max_loops:
            escalate("CR loop > max", report)
            return None
        state["loop_count"]["cr"] += 1
        launch_dev(loop_feedback=report.path)
        iteration += 1
```

## Final summary template (lean)

```text
## /orchestrate done (lean) — Task<XXX>
- PRD: <link>
- SRS: <link>
- Task chain: <link>
- ADR: <link>
- CR iterations: <n> (max 3)
- Budget used: <m>/<cap>
```

## Dry-run output template

```text
## /orchestrate DRY-RUN — Task=<id> Brief="..."
1. AI_PLANNER → ai_python/docs/prd/PRD_<slug>.md (HITL: A/B/C)
2. AI_BA → ai_python/docs/srs/SRS_AI_<task>_<slug>.md
3. AI_PM → ai_python/TASKS/<task>.md + ai_python/docs/task<XXX>/
4. AI_TECH_LEAD → ai_python/docs/adr/ADR-<NNN>-<slug>.md
5. AI_DEVELOPER → ai_python/app/** + tests (gate §5 DEV)
6. AI_CODE_REVIEWER → …/05-code-review/CODE_REVIEW_<task>.md (loop ≤3 nếu BLOCK)
Budget cap: 14. Ước invoke tuyến tính: 6 (+ mỗi vòng CR fail +2: DEV+CR).
```

## Lưu ý kỹ thuật

- Launch subagent: `@path` instruction + contract slot + đường dẫn artifact (không paste full PRD/SRS).
- Subagent không có history chat driver — prompt phải đủ context file path.
- Loop: đính kèm **path** report + vài dòng Block, không paste full report.

## Khi gặp escalation

```text
## /orchestrate ESCALATED at <gate>
Reason: <STOP | budget | CR loop > 3>
State: <yaml>
Last report: <link>
Suggested next steps:
1. ...
```

Resume: `/orchestrate resume Task=<id>` từ gate kế hoặc abort.
