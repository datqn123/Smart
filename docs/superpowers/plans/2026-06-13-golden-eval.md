# Golden Set Eval (tầng rẻ) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bộ eval hồi quy 25 "câu hỏi vàng" chạy với LLM thật (DB giả), chấm bằng máy qua `pytest -m llm`, chặn hồi quy mỗi lần sửa skill.md/schema.md.

**Architecture:** Golden set là YAML thuần dữ liệu; một file test parametrize làm runner: gọi `analyze()` (Session Manager thật, 1 LLM call) → nếu SM chọn `sql_execute` thì `dispatch()` qua subgraph thật với `FakeExecutor` thay DB (2 LLM call) → assert SQL bắt được tại executor. Không sửa dòng code production nào.

**Tech Stack:** pytest (marker `llm`), PyYAML (đã có trong requirements.txt), openai SDK + `OpenAILLMClient` hiện có, pydantic-settings cho `EvalSettings`.

**Spec:** `docs/superpowers/specs/2026-06-12-golden-eval-design.md`

---

## Bối cảnh code đã khảo sát (executor đọc trước khi làm)

| Thành phần | Vị trí | Điểm cần biết |
|---|---|---|
| SM `analyze()` | `ai_python/app/tools/session_manager/__init__.py:77` | Chữ ký `analyze(state, *, llm, memory_context=None) -> Decision`. `Decision` có `action`, `tool_name`, `resolved_require`. Tool control (`finish`, `request_clarification`) nằm ở `action`, `tool_name=None`. |
| `new_session_state` | `ai_python/app/graph/state.py:39` | Tạo SessionState đủ trường cho `analyze()`. |
| `dispatch()` | `ai_python/app/graph/dispatcher.py:34` | `dispatch(tool_name, *, raw_require, upstream_data, llm, deps, ...)`. Production truyền `deps={"executor": ..., "row_limit": ...}` (xem `app/api/app.py:48`). Subgraph tự load skill.md+schema.md rồi chạy execute → self_validate. |
| Require SM gửi tool | `ai_python/app/graph/orchestrator.py:99` | `require = decision.resolved_require or state["raw_require"]` — runner lặp lại đúng dòng này. |
| `sql_execute.execute` | `ai_python/app/tools/sql_execute/__init__.py:70` | `execute(state, *, llm, executor, row_limit=100, **_)`. SQL cuối (sau semantic check + `assert_read_only`) mới chạm `executor.run()`. |
| `OpenAILLMClient` | `ai_python/app/config/llm_client.py:32` | `__init__(*, sdk, model, temperature, max_tokens=None, disable_thinking=False)`. `make_llm()` production: sm dùng temperature 0.0, tool 0.2, max_tokens 1500, disable_thinking True. |
| Memory shape | `ai_python/app/memory/__init__.py:27` | `ThreadMemory = {"turns": [{"user", "answer"}], "summary": str hoặc None}` — YAML `history` đưa thẳng vào `turns`. |
| `think()` | `ai_python/app/harness/think_log.py` | Chỉ là logging — gọi `analyze()`/`dispatch()` ngoài harness an toàn. |
| pytest.ini | `ai_python/pytest.ini` | Hiện: `asyncio_mode=auto`, `testpaths=tests`, `addopts=-q`. Chưa có markers. |
| DB schema | `ai_python/app/tools/sql_execute/schema.md` | Nguồn quy tắc để soạn SQL tham chiếu (LEFT JOIN ế, financeledger, ILIKE giữ dấu, min_quantity...). |

**Quyết định lệch spec (đã cân nhắc):**

1. **Luật sắt KHÔNG ghi vào AGENTS.md** — file `D:\do_an_tot_nghiep\project\AGENTS.md` không còn tồn tại (xác nhận 2026-06-11). Ghi vào `.claude/skills/fixing-reported-bugs/SKILL.md` — nơi đang giữ quy trình vận hành bug. Khi AGENTS.md được tái tạo, chuyển luật sang đó.
2. **Thêm 2 trường barem `sql_not_regex` và chuẩn hóa SQL trước khi so** — spec chỉ có `sql_regex`; thực tế cần phủ định regex (vd bắt INNER JOIN orderdetails mà không bắt nhầm LEFT JOIN). Mọi phép so (contains/regex) chạy trên SQL đã **chuẩn hóa: lowercase + collapse whitespace** → barem viết toàn chữ thường.
3. **Barem khoan dung với nhiều lời giải đúng** — câu absence chấp nhận `LEFT JOIN` **hoặc** `NOT EXISTS`/`NOT IN` qua regex alternation, trừ case ★ "sản phẩm ế" giữ barem chặt đúng bug gốc (xếp hạng cần COALESCE).

## File structure

```
ai_python/
  pytest.ini                      # MODIFY: markers + addopts -m "not llm"
  tests/eval/
    __init__.py                   # CREATE: rỗng (tests/ là package)
    conftest.py                   # CREATE: EvalSettings, FakeExecutor, fixtures llm_sm/llm_tool
    golden.yaml                   # CREATE: 25 case + barem
    test_golden_sql.py            # CREATE: runner parametrize
docs/superpowers/specs/2026-06-12-golden-eval-design.md   # MODIFY: ghi chú AGENTS.md → SKILL.md
.claude/skills/fixing-reported-bugs/SKILL.md              # MODIFY: luật sắt pytest -m llm
```

---

### Task 1: Marker `llm` trong pytest.ini

**Files:**
- Modify: `ai_python/pytest.ini`

- [ ] **Step 1: Ghi nhận baseline suite hiện tại**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest 2>&1 | tail -3
```

Expected: toàn bộ pass. **Ghi lại số test** (spec nói 142 — lấy số thực tế làm chuẩn cho Task 8).

- [ ] **Step 2: Sửa pytest.ini**

Nội dung mới toàn file:

```ini
# ai_python/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts = -q -m "not llm"
markers =
    llm: goi LLM that — golden set eval, can LLM_API_KEY/LLM_BASE_URL (CLI -m llm de chay)
```

- [ ] **Step 3: Verify suite thường không đổi**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest 2>&1 | tail -3
```

Expected: PASS với đúng số test ở Step 1 (chưa có test nào mang marker nên `-m "not llm"` không loại gì).

- [ ] **Step 4: Commit**

```bash
cd /d/do_an_tot_nghiep/project && git add ai_python/pytest.ini && git commit -m "test(eval): them marker llm, suite thuong mac dinh bo qua golden set"
```

---

### Task 2: Kiểm chứng SQL tham chiếu trên DB thật

Nguyên tắc 4 của spec: mỗi barem phải bắt nguồn từ SQL đã chạy đúng trên DB thật. Task này chạy 20 SQL tham chiếu phủ 21 case sql_execute (case `khong-clarify-khi-ngu-canh-ro` dùng lại pattern của `dau-an-tong-nhap` với entity Neptune) qua chính `PostgresRoExecutor`.

**Files:** không tạo file vĩnh viễn — script ad-hoc qua stdin.

- [ ] **Step 1: Chạy script kiểm chứng**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python - <<'EOF'
from app.config.settings import get_settings
from app.sql.executor import PostgresRoExecutor, make_pg_connect

s = get_settings()
ex = PostgresRoExecutor(connect=make_pg_connect(s.database_url_ro), row_limit=5)

SQLS = {
 "products-e-left-join": """
   SELECT p.name, COALESCE(SUM(od.quantity), 0) AS tong_ban
   FROM products p LEFT JOIN orderdetails od ON od.product_id = p.id
   WHERE p.status = 'Active'
   GROUP BY p.id, p.name ORDER BY tong_ban ASC LIMIT 10""",
 "products-chua-ai-mua": """
   SELECT p.name FROM products p
   LEFT JOIN orderdetails od ON od.product_id = p.id
   GROUP BY p.id, p.name HAVING COALESCE(SUM(od.quantity), 0) = 0 LIMIT 20""",
 "khach-chua-mua-thang-nay": """
   SELECT c.name FROM customers c
   WHERE NOT EXISTS (SELECT 1 FROM salesorders so WHERE so.customer_id = c.id
     AND DATE_TRUNC('month', so.created_at) = DATE_TRUNC('month', CURRENT_DATE))
   LIMIT 20""",
 "ncc-chua-nhap-thang-nay": """
   SELECT s2.name FROM suppliers s2
   WHERE NOT EXISTS (SELECT 1 FROM stockreceipts sr WHERE sr.supplier_id = s2.id
     AND DATE_TRUNC('month', sr.receipt_date) = DATE_TRUNC('month', CURRENT_DATE))
   LIMIT 20""",
 "khach-chua-quay-lai": """
   SELECT c.name, MAX(so.created_at) AS lan_cuoi
   FROM customers c LEFT JOIN salesorders so ON so.customer_id = c.id
   GROUP BY c.id, c.name
   HAVING MAX(so.created_at) IS NULL
       OR MAX(so.created_at) < CURRENT_DATE - INTERVAL '3 months'
   LIMIT 20""",
 "dau-an-tong-nhap": """
   SELECT p.name, COALESCE(SUM(srd.quantity), 0) AS tong_nhap
   FROM products p
   LEFT JOIN stockreceiptdetails srd ON srd.product_id = p.id
   LEFT JOIN stockreceipts sr ON sr.id = srd.receipt_id AND sr.status = 'Approved'
   WHERE p.name ILIKE '%dầu ăn%'
   GROUP BY p.id, p.name ORDER BY tong_nhap DESC LIMIT 20""",
 "tim-sp-nuoc-mam": """
   SELECT id, name, status FROM products WHERE name ILIKE '%nước mắm%' LIMIT 20""",
 "khach-ten-co-dau": """
   SELECT c.name, COUNT(so.id) AS so_don
   FROM customers c LEFT JOIN salesorders so ON so.customer_id = c.id
   WHERE c.name ILIKE '%Dũng%' GROUP BY c.id, c.name""",
 "dau-an-follow-up-xuat-ban": """
   SELECT p.name, COALESCE(SUM(od.quantity), 0) AS tong_ban
   FROM products p LEFT JOIN orderdetails od ON od.product_id = p.id
   WHERE p.name ILIKE '%dầu ăn%' GROUP BY p.id, p.name""",
 "doanh-thu-thang-truoc": """
   SELECT SUM(amount) AS doanh_thu FROM financeledger
   WHERE transaction_type = 'SalesRevenue'
     AND DATE_TRUNC('month', transaction_date)
         = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')""",
 "ton-kho-neptune": """
   SELECT p.name, SUM(i.quantity) AS ton
   FROM products p JOIN inventory i ON i.product_id = p.id
   WHERE p.name ILIKE '%Neptune%' GROUP BY p.id, p.name""",
 "doanh-thu-theo-thang": """
   SELECT DATE_TRUNC('month', fl.transaction_date) AS thang, SUM(fl.amount) AS doanh_thu
   FROM financeledger fl WHERE fl.transaction_type = 'SalesRevenue'
   GROUP BY 1 ORDER BY 1 DESC LIMIT 12""",
 "top-khach-mua-nhieu": """
   SELECT c.name, SUM(fl.amount) AS tong
   FROM financeledger fl
   JOIN salesorders so ON fl.reference_type = 'SalesOrder' AND fl.reference_id = so.id
   JOIN customers c ON so.customer_id = c.id
   WHERE fl.transaction_type = 'SalesRevenue'
   GROUP BY c.id, c.name ORDER BY tong DESC LIMIT 5""",
 "tong-nhap-theo-ncc": """
   SELECT s2.name, COALESCE(SUM(sr.total_amount), 0) AS tong_nhap
   FROM suppliers s2 LEFT JOIN stockreceipts sr ON sr.supplier_id = s2.id
   GROUP BY s2.id, s2.name ORDER BY tong_nhap DESC LIMIT 20""",
 "top-ban-chay": """
   SELECT p.name, SUM(od.quantity) AS tong_ban
   FROM products p JOIN orderdetails od ON od.product_id = p.id
   GROUP BY p.id, p.name ORDER BY tong_ban DESC LIMIT 10""",
 "ton-kho-nhieu-nhat": """
   SELECT p.name, SUM(i.quantity) AS tong_ton
   FROM products p JOIN inventory i ON i.product_id = p.id
   WHERE p.status = 'Active' GROUP BY p.id, p.name ORDER BY tong_ton DESC LIMIT 10""",
 "doanh-thu-theo-kenh": """
   SELECT so.order_channel, SUM(fl.amount) AS doanh_thu
   FROM financeledger fl
   JOIN salesorders so ON fl.reference_type = 'SalesOrder' AND fl.reference_id = so.id
   WHERE fl.transaction_type = 'SalesRevenue' GROUP BY so.order_channel""",
 "sap-het-hang": """
   SELECT p.name, i.quantity, i.min_quantity
   FROM inventory i JOIN products p ON i.product_id = p.id
   WHERE i.quantity < i.min_quantity AND p.status = 'Active'
   ORDER BY (i.quantity - i.min_quantity) ASC LIMIT 20""",
 "cong-no-khach": """
   SELECT c.name, pd.total_amount - pd.paid_amount AS con_lai
   FROM partnerdebts pd JOIN customers c ON pd.customer_id = c.id
   WHERE pd.partner_type = 'Customer' AND pd.status = 'InDebt'
   ORDER BY con_lai DESC LIMIT 20""",
 "dong-phieu-xuat-gan-nhat": """
   SELECT sdl.id, sdl.dispatch_id, sdl.quantity
   FROM stockdispatch_lines sdl
   JOIN stockdispatches sd ON sdl.dispatch_id = sd.id
   ORDER BY sd.dispatch_date DESC LIMIT 20""",
}

fails = 0
for name, sql in SQLS.items():
    try:
        r = ex.run(sql, row_limit=5)
        print(f"OK   {name}: {len(r['rows'])} rows, vd {r['rows'][:1]}")
    except Exception as exc:
        fails += 1
        print(f"FAIL {name}: {exc}")
print(f"\n{len(SQLS) - fails}/{len(SQLS)} OK")
EOF
```

Expected: `20/20 OK`. Mỗi dòng in vài rows mẫu — **đọc bằng mắt** xem kết quả có nghĩa không (vd `dau-an-tong-nhap` phải ra sản phẩm dầu ăn; `tim-sp-nuoc-mam` ra nước mắm — chứng minh data có dấu).

- [ ] **Step 2: Xử lý sai lệch (nếu có)**

- SQL lỗi cú pháp/sai cột → sửa SQL tham chiếu theo schema thật, chạy lại.
- Query đúng nhưng 0 rows vì data trống (vd không có sản phẩm "nước mắm", không có khách "Dũng") → **đổi đề bài case** sang entity có thật trong DB (dùng `SELECT name FROM products LIMIT 30` / `SELECT name FROM customers LIMIT 30` để chọn), cập nhật lại câu hỏi + barem tương ứng khi viết golden.yaml ở Task 3. Câu hỏi absence ra 0 rows vẫn hợp lệ (bản chất absence).
- Ghi chú lại mọi thay đổi để Task 3 dùng.

Không commit gì ở task này (script ad-hoc).

---

### Task 3: golden.yaml — 25 case + barem

**Files:**
- Create: `ai_python/tests/eval/__init__.py` (file rỗng)
- Create: `ai_python/tests/eval/golden.yaml`

- [ ] **Step 1: Tạo `ai_python/tests/eval/__init__.py` rỗng**

- [ ] **Step 2: Viết `ai_python/tests/eval/golden.yaml`**

Nội dung đầy đủ (điều chỉnh tên entity nếu Task 2 Step 2 đã đổi):

```yaml
# Golden set — cau hoi vang + barem cham bang may.
# QUY UOC BAREM:
# - Moi phep so (sql_contains/sql_not_contains/sql_regex/sql_not_regex) chay tren SQL
#   DA CHUAN HOA: lowercase + moi run whitespace thanh 1 dau cach.
#   => barem viet toan chu thuong, khong xuong dong.
# - sm_tool: tool SM phai chon; voi control action (finish/request_clarification)
#   so voi decision.action.
# - sm_require_contains: substring phai co trong require SM gui tool
#   (= resolved_require hoac raw_require), so lowercase.
# - history: cac luot truoc [{user, answer}] — dua thang vao memory_context["turns"].
# - Moi bug production moi = mot case vinh vien moi (luat trong spec).

# ===== Absence (LEFT JOIN / NOT EXISTS) =====

- id: products-e-left-join          # ★ bug goc: 6 few-shot INNER JOIN keo nguoc rule
  tags: [absence, products]
  history: []
  require: "Sản phẩm nào đang ế nhất?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["left join orderdetails", "coalesce"]
    sql_not_regex: '(?<!left )join orderdetails'

- id: products-chua-ai-mua
  tags: [absence, products]
  history: []
  require: "Liệt kê các sản phẩm chưa ai mua"
  expect:
    sm_tool: sql_execute
    sql_contains: ["orderdetails"]
    sql_regex: 'left join|not exists|not in'
    sql_not_regex: '(?<!left )join orderdetails'

- id: khach-chua-mua-thang-nay
  tags: [absence, sales]
  history: []
  require: "Khách hàng nào chưa mua hàng trong tháng này?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["customers"]
    sql_regex: 'left join|not exists|not in'

- id: ncc-chua-nhap-thang-nay
  tags: [absence, receiving]
  history: []
  require: "Nhà cung cấp nào chưa có phiếu nhập kho nào trong tháng này?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["suppliers"]
    sql_regex: 'left join|not exists|not in'

- id: khach-chua-quay-lai
  tags: [absence, customers]
  history: []
  require: "Khách nào 3 tháng nay chưa quay lại mua hàng?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["customers"]
    sql_regex: 'left join|not exists|not in'

# ===== Diacritics / so khop ten tieng Viet =====

- id: dau-an-tong-nhap              # ★ bug goc: ILIKE '%dau an%' khop 0 dong
  tags: [diacritics, receiving]
  history: []
  require: "Tổng nhập kho dầu ăn là bao nhiêu?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["dầu ăn", "stockreceiptdetails"]
    sql_not_contains: ["%dau an%"]

- id: tim-sp-nuoc-mam
  tags: [diacritics, products]
  history: []
  require: "Tìm các sản phẩm nước mắm"
  expect:
    sm_tool: sql_execute
    sql_contains: ["products", "nước mắm"]
    sql_not_contains: ["%nuoc mam%"]

- id: khach-ten-co-dau
  tags: [diacritics, customers]
  history: []
  require: "Khách hàng tên Dũng đã mua bao nhiêu đơn hàng?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["dũng"]
    sql_not_contains: ["%dung%"]

# ===== Chu the theo ngu canh (history) =====

- id: dau-an-follow-up              # ★ bug goc: SM khong gan chu the "dau an" cho cau noi tiep
  tags: [context, receiving]
  history:
    - user: "Tổng nhập kho dầu ăn tháng này là bao nhiêu?"
      answer: "Tháng này đã nhập tổng cộng 120 thùng dầu ăn (Dầu ăn Neptune 1L: 80, Dầu ăn Simply 1L: 40)."
  require: "Thế còn xuất bán thì sao?"
  expect:
    sm_tool: sql_execute
    sm_require_contains: ["dầu ăn"]
    sql_contains: ["dầu ăn"]
    sql_regex: 'orderdetails|stockdispatch'

- id: doanh-thu-thang-truoc-follow-up
  tags: [context, sales]
  history:
    - user: "Doanh thu tháng này bao nhiêu?"
      answer: "Doanh thu tháng này đạt 1,2 tỷ đồng (theo sổ cái SalesRevenue)."
  require: "Còn tháng trước?"
  expect:
    sm_tool: sql_execute
    sm_require_contains: ["doanh thu"]
    sql_contains: ["financeledger", "salesrevenue"]

- id: sp-vua-liet-ke-follow-up
  tags: [context, products]
  history:
    - user: "Top 3 sản phẩm bán chạy nhất là gì?"
      answer: "Top 3: 1. Mì Hảo Hảo tôm chua cay, 2. Dầu ăn Neptune 1L, 3. Nước mắm Nam Ngư 500ml."
  require: "Cái thứ hai còn tồn kho bao nhiêu?"
  expect:
    sm_tool: sql_execute
    sm_require_contains: ["neptune"]
    sql_contains: ["inventory", "neptune"]

# ===== Aggregate =====

- id: doanh-thu-theo-thang
  tags: [aggregate, finance]
  history: []
  require: "Doanh thu theo từng tháng trong năm nay?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["financeledger", "salesrevenue", "group by"]
    sql_not_contains: ["final_amount"]

- id: top-khach-mua-nhieu
  tags: [aggregate, customers]
  history: []
  require: "Top 5 khách hàng mua nhiều nhất?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["customers", "group by", "limit 5"]
    sql_regex: 'order by .+ desc'

- id: tong-nhap-theo-ncc
  tags: [aggregate, receiving]
  history: []
  require: "Tổng giá trị nhập kho theo từng nhà cung cấp?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["suppliers", "group by"]
    sql_regex: 'stockreceipt'

- id: top-ban-chay
  tags: [aggregate, products]
  history: []
  require: "Top 10 sản phẩm bán chạy nhất?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["orderdetails", "group by"]
    sql_regex: 'order by .+ desc'

- id: ton-kho-nhieu-nhat
  tags: [aggregate, inventory]
  history: []
  require: "Sản phẩm nào đang tồn kho nhiều nhất?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["inventory"]
    sql_regex: 'order by .+ desc'

- id: doanh-thu-theo-kenh
  tags: [aggregate, finance]
  history: []
  require: "Doanh thu theo từng kênh bán hàng?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["financeledger", "order_channel"]

# ===== Quy tac nghiep vu khac =====

- id: sap-het-hang
  tags: [business-rule, inventory]
  history: []
  require: "Sản phẩm nào sắp hết hàng?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["min_quantity"]

- id: cong-no-khach
  tags: [business-rule, customers]
  history: []
  require: "Khách nào đang nợ nhiều nhất?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["partnerdebts"]
    sql_regex: 'total_amount\s*-\s*paid_amount'

- id: dong-phieu-xuat-gan-nhat
  tags: [business-rule, dispatch]
  history: []
  require: "Phiếu xuất kho gần nhất gồm những dòng hàng nào?"
  expect:
    sm_tool: sql_execute
    sql_contains: ["stockdispatch_lines", "stockdispatches"]
    sql_not_regex: 'dispatch_id\s*=\s*(so|salesorders)\.id'

# ===== Clarify (SM hoi lai) =====

- id: clarify-cai-do-gia
  tags: [clarify, products]
  history: []
  require: "Cái đó giá bao nhiêu?"
  expect:
    sm_tool: request_clarification

- id: clarify-xem-chi-tiet
  tags: [clarify, products]
  history: []
  require: "Xem chi tiết"
  expect:
    sm_tool: request_clarification

- id: khong-clarify-khi-ngu-canh-ro   # case dao chieu: co history thi KHONG duoc hoi lai
  tags: [clarify, context, receiving]
  history:
    - user: "Có sản phẩm dầu ăn Neptune 1L không?"
      answer: "Có, Dầu ăn Neptune 1L đang ở trạng thái Active."
  require: "Cái đó đã nhập kho tổng cộng bao nhiêu?"
  expect:
    sm_tool: sql_execute
    sm_require_contains: ["neptune"]
    sql_contains: ["neptune"]

# ===== Control (finish khong qua tool) =====

- id: greeting-finish
  tags: [control]
  history: []
  require: "Chào bạn!"
  expect:
    sm_tool: finish

- id: ngoai-pham-vi
  tags: [control]
  history: []
  require: "Thời tiết Hà Nội hôm nay thế nào?"
  expect:
    sm_tool: finish
```

- [ ] **Step 3: Verify YAML parse được và đủ 25 case**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -c "
import yaml, pathlib
cases = yaml.safe_load(pathlib.Path('tests/eval/golden.yaml').read_text(encoding='utf-8'))
ids = [c['id'] for c in cases]
assert len(ids) == len(set(ids)), 'id trung lap'
assert all('require' in c and 'expect' in c and 'sm_tool' in c['expect'] for c in cases)
print(len(cases), 'cases OK')"
```

Expected: `25 cases OK`

- [ ] **Step 4: Commit**

```bash
cd /d/do_an_tot_nghiep/project && git add ai_python/tests/eval/__init__.py ai_python/tests/eval/golden.yaml && git commit -m "test(eval): golden set 25 cau hoi vang + barem cham bang may"
```

---

### Task 4: conftest.py của tests/eval — LLM thật + FakeExecutor

**Files:**
- Create: `ai_python/tests/eval/conftest.py`

- [ ] **Step 1: Viết conftest.py**

```python
# ai_python/tests/eval/conftest.py
"""Fixtures cho golden eval: LLM THAT tu env/.env, DB GIA (FakeExecutor).

Dao chieu so voi unit test (FakeLLM + StubSqlExecutor): o day LLM that,
tang I/O cuoi la vat the than. Khong sua dong code production nao.
Doi model = doi LLM_BASE_URL/LLM_API_KEY/LLM_MODEL (env de len .env);
dieu kien: endpoint ho tro native tool-calling (tool_choice ep buoc).
"""
import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict


class EvalSettings(BaseSettings):
    """Chi cac truong LLM — KHONG dung app Settings vi no bat buoc
    database_url_ro (eval khong cham DB). Default trung voi Settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      extra="ignore", case_sensitive=False)
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "Qwen3.6-27B"
    llm_temperature: float = 0.2          # tool thuong (nhu make_llm)
    llm_sm_temperature: float = 0.0       # SM deterministic (nhu make_llm)
    llm_http_request_timeout: int = 120
    llm_max_tokens: int = 1500
    llm_disable_thinking: bool = True


class FakeExecutor:
    """Vat the than cho PostgresRoExecutor: ghi lai SQL da qua guard,
    tra rows gia de pipeline khong vo."""

    def __init__(self):
        self.captured_sql: str | None = None

    def run(self, sql: str, *, row_limit: int = 100):
        self.captured_sql = sql
        return {"columns": ["name", "total"],
                "rows": [{"name": "X", "total": 1}]}


@pytest.fixture(scope="session")
def eval_settings():
    s = EvalSettings()
    if not s.llm_api_key or not s.llm_base_url:
        pytest.skip("golden eval can LLM_API_KEY + LLM_BASE_URL (env hoac ai_python/.env)")
    return s


def _make_client(s: "EvalSettings", temperature: float):
    from openai import OpenAI
    from app.config.llm_client import OpenAILLMClient
    sdk = OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key,
                 timeout=s.llm_http_request_timeout)
    return OpenAILLMClient(sdk=sdk, model=s.llm_model, temperature=temperature,
                           max_tokens=s.llm_max_tokens,
                           disable_thinking=s.llm_disable_thinking)


@pytest.fixture(scope="session")
def llm_sm(eval_settings):
    """LLM cho Session Manager — temperature 0.0 nhu make_llm(role='sm')."""
    return _make_client(eval_settings, eval_settings.llm_sm_temperature)


@pytest.fixture(scope="session")
def llm_tool(eval_settings):
    """LLM cho tool — temperature 0.2 nhu make_llm(role='default')."""
    return _make_client(eval_settings, eval_settings.llm_temperature)


@pytest.fixture
def fake_executor():
    return FakeExecutor()
```

Lưu ý: `run()` trả `{"columns", "rows"}` — đúng shape `PostgresRoExecutor`/`StubSqlExecutor` mà `sql_execute` đọc (`result["columns"]`, `result["rows"]`); không thêm key thừa.

- [ ] **Step 2: Verify import sạch (chưa có test dùng — chỉ cần không vỡ collection)**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest --collect-only -q 2>&1 | tail -3
```

Expected: collection OK, số test như cũ, không error.

- [ ] **Step 3: Commit**

```bash
cd /d/do_an_tot_nghiep/project && git add ai_python/tests/eval/conftest.py && git commit -m "test(eval): conftest cho golden eval — LLM that tu env, FakeExecutor thay DB"
```

---

### Task 5: Runner test_golden_sql.py

**Files:**
- Create: `ai_python/tests/eval/test_golden_sql.py`

- [ ] **Step 1: Viết runner**

```python
# ai_python/tests/eval/test_golden_sql.py
"""Golden set eval — tang re: cham SQL ngay tai executor, khong cham DB.

Moi case = 1 test:
  YAML history -> memory_context gia -> analyze() SM THAT     (1 LLM call)
      assert sm_tool, sm_require_contains
  -> dispatch('sql_execute') qua subgraph THAT, executor=FakeExecutor
     (SqlDraft + SemanticCheck = 2 LLM call)
      assert sql_contains / sql_not_contains / sql_regex / sql_not_regex
SQL duoc cham la SQL SAU semantic self-check va SAU assert_read_only —
dung chuoi se cham DB trong production (executor chi nhan SQL da qua guard).
"""
import re
from pathlib import Path

import pytest
import yaml

from app.graph.dispatcher import dispatch
from app.graph.state import new_session_state
from app.tools.session_manager import analyze

pytestmark = pytest.mark.llm

_CASES = yaml.safe_load(
    (Path(__file__).parent / "golden.yaml").read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    """Chuan hoa de so barem: lowercase + collapse whitespace (quy uoc golden.yaml)."""
    return " ".join(text.split()).lower()


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_golden(case, llm_sm, llm_tool, fake_executor):
    expect = case["expect"]

    # --- Muc B: do tu Session Manager tro di ---
    state = new_session_state(raw_require=case["require"],
                              thread_id=f"eval-{case['id']}")
    memory_context = {"turns": case.get("history") or [], "summary": None}
    decision = analyze(state, llm=llm_sm, memory_context=memory_context)

    actual_tool = decision.tool_name or decision.action
    assert actual_tool == expect["sm_tool"], (
        f"SM chon {actual_tool!r} thay vi {expect['sm_tool']!r} "
        f"(reasoning: {decision.reasoning})")

    if expect["sm_tool"] != "sql_execute":
        return  # case clarify/finish: barem chi co quyet dinh SM

    # require SM gui tool — dung cong thuc orchestrator (orchestrator.py:99)
    require = decision.resolved_require or state["raw_require"]
    for sub in expect.get("sm_require_contains") or []:
        assert sub.lower() in require.lower(), (
            f"require SM gui tool thieu {sub!r}: {require!r}")

    # --- Tang re: chay sql_execute that voi DB gia, dung tai executor ---
    result = dispatch("sql_execute", raw_require=require, upstream_data={},
                      llm=llm_tool, deps={"executor": fake_executor})
    sql = fake_executor.captured_sql
    assert sql, (f"SQL khong cham executor — "
                 f"error: {(result['output'] or {}).get('error')!r}")

    n = _norm(sql)
    for sub in expect.get("sql_contains") or []:
        assert _norm(sub) in n, f"SQL thieu {sub!r}:\n{sql}"
    for sub in expect.get("sql_not_contains") or []:
        assert _norm(sub) not in n, f"SQL chua chuoi cam {sub!r}:\n{sql}"
    if expect.get("sql_regex"):
        assert re.search(expect["sql_regex"], n), (
            f"SQL khong khop pattern {expect['sql_regex']!r}:\n{sql}")
    if expect.get("sql_not_regex"):
        assert not re.search(expect["sql_not_regex"], n), (
            f"SQL khop pattern cam {expect['sql_not_regex']!r}:\n{sql}")
```

- [ ] **Step 2: Verify collection — 25 test mang marker llm, suite thường loại sạch**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest -m llm --collect-only -q 2>&1 | tail -3
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest --collect-only -q 2>&1 | tail -3
```

Expected: lệnh 1 hiện `25 tests collected` (số deselected = phần còn lại); lệnh 2 hiện số test cũ + `25 deselected`.

- [ ] **Step 3: Verify skip sạch khi thiếu key (tiêu chí nghiệm thu #3)**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 LLM_API_KEY= LLM_BASE_URL= python -m pytest -m llm 2>&1 | tail -3
```

Expected: `25 skipped` với message "golden eval can LLM_API_KEY...", **không có failed/error** (env var rỗng đè .env trong pydantic-settings).

- [ ] **Step 4: Smoke 1 case thật trước khi chạy cả bộ**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest -m llm -k products-e-left-join -v 2>&1 | tail -10
```

Expected: 1 passed (hoặc failed với diff barem rõ ràng — sang Task 6 xử lý). Nếu lỗi hạ tầng (timeout, 401, tool_choice không hỗ trợ) → sửa cấu hình env trước khi đi tiếp.

- [ ] **Step 5: Commit**

```bash
cd /d/do_an_tot_nghiep/project && git add ai_python/tests/eval/test_golden_sql.py && git commit -m "test(eval): runner golden set — SM that + sql_execute that, cham SQL tai executor"
```

---

### Task 6: Baseline xanh — chạy cả bộ, phân loại case đỏ

**Files:**
- Modify (có thể): `ai_python/tests/eval/golden.yaml` — chỉ nới barem

- [ ] **Step 1: Chạy đủ 25 case**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest -m llm -v 2>&1 | tail -35
```

Expected: ~5–8 phút (≈75 LLM call tuần tự). Ghi lại danh sách case đỏ.

- [ ] **Step 2: Phân loại từng case đỏ — quy tắc cứng**

Với mỗi case fail, đọc message assert (có SQL/decision thật):

1. **Barem quá chặt, SQL/decision thật vẫn ĐÚNG nghiệp vụ** (vd model dùng `NOT EXISTS` chỗ barem đòi `left join`, dùng bảng thay thế hợp lệ) → nới barem trong golden.yaml (thêm alternation, bỏ điều kiện thừa). Đây là sửa **dữ liệu eval**, được phép tự làm.
2. **Model thật sự sai nghiệp vụ** (INNER JOIN nuốt dòng absence, bỏ dấu tiếng Việt, không gắn chủ thể từ history, không clarify khi mơ hồ) → **đây là prompt gap thật — KHÔNG nới barem, KHÔNG tự sửa skill.md/schema.md.** Dừng lại, báo user danh sách case + bằng chứng SQL, chờ quyết định (sửa prompt đi qua gate của skill fixing-reported-bugs).
3. **Lỗi hạ tầng** (timeout, rate limit) → chạy lại case lẻ `pytest -m llm -k <id>`; nếu tái diễn, báo user.

- [ ] **Step 3: Lặp đến khi xanh hết (chỉ với case loại 1)**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest -m llm -v 2>&1 | tail -5
```

Expected: `25 passed` (baseline xanh — tiêu chí nghiệm thu #2).

- [ ] **Step 4: Commit (nếu có nới barem)**

```bash
cd /d/do_an_tot_nghiep/project && git add ai_python/tests/eval/golden.yaml && git commit -m "test(eval): noi barem theo loi giai hop le cua model — baseline xanh 25/25"
```

---

### Task 7: Luật sắt vào quy trình vận hành

**Files:**
- Modify: `.claude/skills/fixing-reported-bugs/SKILL.md`
- Modify: `docs/superpowers/specs/2026-06-12-golden-eval-design.md`

- [ ] **Step 1: Thêm luật sắt vào SKILL.md**

Trong `.claude/skills/fixing-reported-bugs/SKILL.md`, mục `### 6. Bằng chứng cho mỗi thay đổi`, thay bullet thứ hai (bắt đầu "- Thay đổi **prompt**") bằng:

```markdown
- Thay đổi **prompt** (skill.md/schema.md): kiểm chứng mẫu SQL đích chạy đúng
  trên DB thật TRƯỚC khi đưa vào rule/few-shot. Sau khi sửa, chạy golden set
  `python -m pytest -m llm -v` (~5–8 phút, cần LLM_API_KEY) — **LUẬT SẮT:
  không commit thay đổi skill.md/schema.md khi golden set chưa xanh.** Case đỏ
  nghĩa là rule mới phá hành vi cũ. Gặp bug production mới: thêm case vào
  `ai_python/tests/eval/golden.yaml` TRƯỚC, sửa prompt sau, eval xanh rồi mới
  đóng bug.
```

- [ ] **Step 2: Ghi chú lệch spec vào design doc**

Trong `docs/superpowers/specs/2026-06-12-golden-eval-design.md`, mục `## 6. Luật sắt & quy trình vận hành`, sửa bullet đầu từ:

```markdown
- **Luật sắt** (ghi vào AGENTS.md): không commit thay đổi `skill.md`/`schema.md`
  nếu `pytest -m llm` chưa xanh.
```

thành:

```markdown
- **Luật sắt**: không commit thay đổi `skill.md`/`schema.md` nếu `pytest -m llm`
  chưa xanh. (Ghi tại `.claude/skills/fixing-reported-bugs/SKILL.md` mục 6 —
  AGENTS.md không còn tồn tại tại thời điểm triển khai 2026-06-13; khi tái tạo
  AGENTS.md thì chuyển luật sang đó.)
```

- [ ] **Step 3: Commit**

```bash
cd /d/do_an_tot_nghiep/project && git add .claude/skills/fixing-reported-bugs/SKILL.md docs/superpowers/specs/2026-06-12-golden-eval-design.md && git commit -m "docs(eval): luat sat golden set vao quy trinh fix bug, ghi chu vi tri thay AGENTS.md"
```

---

### Task 8: Nghiệm thu cuối

**Files:** không sửa gì — chỉ verify.

- [ ] **Step 1: Suite thường nhanh như cũ, không gọi LLM thật**

```bash
cd /d/do_an_tot_nghiep/project/ai_python && PYTHONIOENCODING=utf-8 python -m pytest 2>&1 | tail -3
```

Expected: pass đúng số test baseline Task 1 + `25 deselected`, thời gian tương đương trước (vài chục giây). Tiêu chí #1 ✓.

- [ ] **Step 2: Đối chiếu checklist nghiệm thu của spec**

1. Suite thường pass, không LLM thật — Step 1 ✓
2. `pytest -m llm -v` 25/25 pass baseline — Task 6 ✓
3. Thiếu LLM_API_KEY → skip sạch — Task 5 Step 3 ✓
4. 3 case ★ (`products-e-left-join`, `dau-an-tong-nhap`, `dau-an-follow-up`) tái hiện đúng barem bug gốc — có trong golden.yaml, pass ở Task 6 ✓
5. Luật sắt ghi vào quy trình vận hành (SKILL.md thay AGENTS.md, có ghi chú trong spec) — Task 7 ✓

Báo cáo kết quả từng mục cho user kèm output thật (verification-before-completion).
