# Fix Progress Bar — Implementation Plan

## Problem
Progress bar không hiển thị khi user gửi câu hỏi, dù code đã được thêm vào backend và frontend.

## Root Cause Analysis

### Issue 1: Condition hiển thị sai (Frontend)
**File:** `ChatBotPage.tsx`
**Dòng hiện tại:**
```tsx
{isProcessing && progressText && (
   <div className="...">...</div>
)}
```
**Vấn đề:** Khi `onDelta` đầu tiên nhận được → `setIsProcessing(false)` → progress bar biến mất ngay lập tức, dù `progressText` vẫn có giá trị.

**Giải pháp:** Bỏ `isProcessing` khỏi condition, chỉ dùng `progressText`:
```tsx
{progressText && (
   <div className="...">...</div>
)}
```

### Issue 2: Python server chưa restart
Code `emit_progress()` đã thêm vào nodes nhưng server chưa reload → không có event `progress` nào được emit.

### Issue 3: Nhiều return paths thiếu `emit_progress`
77 return statements trong nodes, chỉ ~25 có `emit_progress`. Cần fix 52 paths còn lại.

---

## Implementation Steps

### Step 1: Fix Frontend condition (ChatBotPage.tsx)

**File:** `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`

**Thay đổi 1:** Sửa condition hiển thị progress bar
```tsx
// OLD
{isProcessing && progressText && (
   <div className="...">...</div>
)}

// NEW
{progressText && (
   <div className="flex items-center gap-3 px-4 py-2 bg-amber-50 border border-amber-100 rounded-xl">
     <Loader2 className="h-4 w-4 text-amber-600 animate-spin" />
     <span className="text-xs font-semibold text-amber-700">{progressText}</span>
   </div>
)}
```

**Thay đổi 2:** Thêm console.log debug (tạm thời)
```tsx
onProgress: (text) => {
  console.log("[SSE progress]", text)
  setProgressText(text)
},
onDelta: (delta) => {
  if (!firstDeltaReceived) {
    firstDeltaReceived = true
    setIsProcessing(false)
    setProgressText("")  // Clear progress khi bắt đầu stream delta
    console.log("[SSE delta first]", delta.slice(0, 50))
  }
  ...
}
```

### Step 2: Fix 52 missing `emit_progress` return paths

**Priority nodes (user-facing, run first):**

| File | Missing Paths | Action |
|------|--------------|--------|
| `domain_guard.py` | Lines 262, 285, 322 | Add `**emit_progress(state, "domain_guard")` |
| `context_compact.py` | Lines 113, 129 | Add `**emit_progress(state, "context_compact")` |
| `sql_pipeline.py` | Lines 212, 230, 430, 615, 625, 639, 649, 659, 673 | Add appropriate `emit_progress` |
| `summarize.py` | Lines 87, 113, 185 | Add `**emit_progress(state, "summarize_answer")` |
| `chart_report.py` | Lines 86, 106, 120, 310, 367 | Add appropriate `emit_progress` |
| `catalog_draft.py` | Lines 55, 106, 149, 168, 182, 202, 243 | Add appropriate `emit_progress` |
| `inventory_draft.py` | Lines 57, 122, 194, 214, 225, 246, 284 | Add appropriate `emit_progress` |
| `schema_explore.py` | Lines 77, 157, 180 | Add `**emit_progress(state, "schema_explore")` |
| `draft_resolve.py` | Lines 63, 105 | Add `**emit_progress(state, "draft_resolve")` |
| `query_table.py` | Lines 21, 31, 45 | Add `**emit_progress(state, "emit_query_table")` |

### Step 3: Restart Python server

```bash
cd D:\do_an_tot_nghiep\project\ai_python
# Kill existing uvicorn process
# Then restart:
uvicorn app.main:app --reload --port 9000
```

### Step 4: Verify

1. Mở browser DevTools → Console
2. Gửi câu hỏi → kiểm tra log `[SSE progress] Đang kiểm tra phạm vi câu hỏi...`
3. Kiểm tra progress bar hiển thị màu amber với spinner
4. Kiểm tra progress bar biến mất khi delta bắt đầu stream
5. Xóa console.log debug sau khi verify xong

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx` | Fix condition, add debug logs |
| `ai_python/app/graph/nodes/domain_guard.py` | Add emit_progress to 3 missing paths |
| `ai_python/app/graph/nodes/context_compact.py` | Add emit_progress to 2 missing paths |
| `ai_python/app/graph/nodes/sql_pipeline.py` | Add emit_progress to 9 missing paths |
| `ai_python/app/graph/nodes/summarize.py` | Add emit_progress to 3 missing paths |
| `ai_python/app/graph/nodes/chart_report.py` | Add emit_progress to 5 missing paths |
| `ai_python/app/graph/nodes/catalog_draft.py` | Add emit_progress to 7 missing paths |
| `ai_python/app/graph/nodes/inventory_draft.py` | Add emit_progress to 7 missing paths |
| `ai_python/app/graph/nodes/schema_explore.py` | Add emit_progress to 3 missing paths |
| `ai_python/app/graph/nodes/draft_resolve.py` | Add emit_progress to 2 missing paths |
| `ai_python/app/graph/nodes/query_table.py` | Add emit_progress to 3 missing paths |

## Files NOT to Modify

| File | Reason |
|------|--------|
| `AiChatRelayController.java` | Already forwards all SSE events generically |
| `routes.py` | Already yields `progress` event correctly |
| `progress.py` | Already has correct agent→text mapping |
| `aiChatSse.ts` | Already parses `progress` event correctly |
| `state.py` | Already has `progress_text` field |

---

## Testing Checklist

- [ ] Progress bar hiển thị ngay khi gửi câu hỏi
- [ ] Progress text thay đổi theo từng node (domain_guard → intent → chat_normal/sql)
- [ ] Progress bar biến mất khi AI bắt đầu stream delta
- [ ] Progress bar biến mất khi có lỗi
- [ ] Progress bar biến mất khi done
- [ ] Không có console errors
- [ ] Python log có dòng `[progress] agent=...`

---

## Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Progress bar flash quá nhanh | Giữ progressText cho đến khi delta đầu tiên đến |
| Progress text không cập nhật | Kiểm tra Python log, verify emit_progress được gọi |
| Spring relay drop event | Không thể — Spring forward generic tất cả events |
| Browser không hỗ trợ SSE | Không thể — đã hoạt động với delta/chart/error |
