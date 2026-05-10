# AI_CODE_REVIEWER — Code Review (`ai_python`)

> **Callsign**: `AI_CODE_REVIEWER`  
> **Input**: SRS, ADR, Task file; codebase `ai_python/` sau DEV.

---

## §1 I/O contract

| Slot | Mô tả |
| :-- | :-- |
| `SRS_PATH` | SRS |
| `ADR_PATH` | ADR |
| `TASK_FILE` | Task — scope & nhãn báo cáo |
| `OUT_PATH` | `ai_python/docs/task<XXX>/05-code-review/CODE_REVIEW_<task>.md` |
| `ITERATION` | Số vòng (1…4) — ghi trong báo cáo |

---

## §2 Nội dung báo cáo

1. **Verdict**: `PASS` | `BLOCK` | `STOP`.
2. **Tóm tắt** — 3–7 gạch đầu dòng.
3. **Findings** — chấm điểm mức độ; chỉ code path `ai_python/`.
4. **Khớp SRS/ADR** — đạt / lệch (nêu mục).
5. **Nếu BLOCK** — hành động cụ thể cho DEV (file + gợi ý).

---

## §3 Verdict

| Verdict | Khi nào |
| :-- | :-- |
| **PASS** | Không issue blocking; có thể có nit không chặn merge task |
| **BLOCK** | Thiếu test, lỗi logic, vi phạm ADR/SRS, security rõ ràng trong scope |
| **STOP** | Phát hiện cần sửa ngoài `ai_python/` hoặc vi phạm policy an toàn — escalate Owner |

---

## §5 Gate exit — Code Review

| PASS |
| :-- |
| File `OUT_PATH` được ghi đầy đủ §2 |
| Verdict **PASS** để `/orchestrate` lean kết thúc |

Vòng lặp **BLOCK** → DEV → CR tối đa **3** lần tăng `loop_count.cr` — xem [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) §0.2.
