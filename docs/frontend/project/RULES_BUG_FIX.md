# 🐞 Bug-Fix & Lessons Learned Rules (Mini-ERP)

> [!IMPORTANT]
> **MANDATORY:** AI Assistants MUST read this file in conjunction with `RULES.md` before any analysis or implementation. These rules are derived from real project bugs to prevent regressions.

---

## 1. Core Bug-Fix Principles
- **Root Cause First:** Never fix a symptom without identifying the root cause.
- **Regression Testing:** Every bug fix MUST have a corresponding test case in Vitest or Playwright.
- **Minimalist Fix:** Do not refactor unrelated code while fixing a bug.
- **Documentation Sync:** If a fix changes logic described in `SRS` or `FUNCTIONAL_SUMMARY.md`, update those files immediately.

---

## 2. Specific Rules from Bug History

### [BF-001] Component Visibility & Dropdowns
- **Symptom:** Dropdown menus or popovers being cut off or hidden behind other elements.
- **Root Cause:** Incorrect Z-index management or `overflow-hidden` on parent containers.
- **Rule:** 
  - Use Radix UI `Portal` for all dropdowns/popovers to render at the body level.
  - Verify `z-index` against the project's layering system.
- **Check:** Ensure no parent container has `overflow-hidden` if it contains absolute-positioned elements that need to break out.

### [BF-002] Responsive Grid Overlap
- **Symptom:** Content overlapping or squashing on mobile viewports.
- **Root Cause:** Using fixed widths (`w-[400px]`) instead of relative classes or grid-cols.
- **Rule:** 
  - Always use `grid-cols-1` as default (mobile) and upgrade to `md:grid-cols-2` etc.
  - Never use fixed pixel widths for main layout components.

### [BF-003] Sticky Header Context
- **Symptom:** Table headers (`sticky top-0`) do not stick during scroll.
- **Root Cause:** Missing `overflow-y-auto` on the scrollable container, or a parent having `overflow-hidden` without defined height.
- **Rule:** 
  - The immediate parent of the `Table` or the main list container MUST have `overflow-y-auto` and a set height (e.g. `flex-1`).
  - Use `z-10` on headers to ensure they stay above row content.

### [BF-004] White Screen of Death (WSOD) - Missing Constants
- **Symptom:** Entire page goes white after refactor. Console shows `ReferenceError: X is not defined`.
- **Root Cause:** Accidental deletion of local constants (e.g. `statusOptions`, `config`) during large code replacements.
- **Rule:** 
  - Always verify that all variables used in JSX are defined or imported.
  - Mandatory: Run the dev server and check the page immediately after any `replace_file_content` that modifies the main component body.

### [BF-005] Test Side Effects (Multiple Elements)
- **Symptom:** Unit tests fail with `Found multiple elements with data-testid` even if only 1 is rendered in the component.
- **Root Cause:** Vitest not cleaning up the DOM between tests because `afterEach(cleanup)` is missing or `globals: true` is disabled.
- **Rule:** 
  - Ensure `vite.config.ts` has `test: { globals: true }` or manually call `cleanup()` in test setup.

### [BF-006] Sticky Header Wrapper Breakage (Shadcn/Radix UI)
- **Symptom:** `sticky top-0` on `TableHeader` fails to stay fixed when scrolling.
- **Root Cause:** Shadcn's `<Table />` component wraps the `<table>` in a `div` with `overflow-x-auto`. This intermediate wrapper prevents the `thead` from sticking to the *outer* scroll container.
- **Rule:** 
  - Apply `sticky top-0 z-20 bg-slate-50` directly to each `<TableHead />` (`th`) element rather than the parent `<TableHeader />` (`thead`).
  - Use `shadow-[inset_0_-1px_0_rgba(0,0,0,0.1)]` on `th` to preserve the bottom border look while sticky.
  - Set `z-index` of `th` high enough (e.g., `z-20`) to stay above scrolling row content.

### [BF-007] Sheet Content Padding
- **Symptom:** Content inside a Sheet or Drawer touches the edges (especially the left edge).
- **Root Cause:** Overriding `SheetContent` without providing sufficient padding.
- **Master Pattern:** `[UI-001]` (Table Layout): Luôn tuân thủ [Master Table Pattern](file:///d:/do_an_tot_nghiep/frontend/docs/rules/RULES_UI_TABLE.md).
- **Rule:** 
  - Always ensure `SheetContent` has at least `p-6` (or `px-6 py-4`) to maintain readability and aesthetic standards.

### [BF-008] JSX Nesting & Parse Error (oxc)
- **Symptom:** `[PARSE_ERROR] Error: Unexpected token. Did you mean {'}'} or &rbrace;?` at the end of the file.
- **Root Cause:** Missing closing tag (e.g., `</div>`) for a main container, causing the parser to treat the closing function bracket `}` as JSX content.
- **Prevention Rule:** 
  - Always verify that each opening tag has a corresponding closing tag before committing.
  - Run `npm test` or a simple render test for the modified component to catch syntax errors early.
  - When wrapping large sections of code, use an IDE feature (like "Go to Matching Bracket") to confirm the structure.

---

## 3. Knowledge Harvesting Template (For Agents)
When a bug is fixed, the Developer/Doc-Sync agent should add an entry here if it meets the project's "Learning Filter":

```markdown
### [BF-XXX] Short Title
- **Symptom:** What happened?
- **Root Cause:** Why did it happen?
- **Prevention Rule:** What is the new rule to prevent this?
- **Example:** (Optional) Good vs Bad code snippets.
```
