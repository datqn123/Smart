# AI Coding Rules for Mini-ERP Project (React/Vite - Minimalist & High Performance)

> [!IMPORTANT]
> **MANDATORY:** The AI Assistant MUST read both `RULES.md` and `RULES_BUG_FIX.md` file carefully BEFORE writing any code or proposing any implementation plans. Compliance with these rules is non-negotiable.
> **Context tối thiểu theo loại task** (tiết kiệm token): [`AGENTS/docs/CONTEXT_INDEX.md`](AGENTS/docs/CONTEXT_INDEX.md).

---

## 1. Core Principles: "Minimalist & Professional"

- **Client-Side:** Minimal computation. Offload complex logic to backend.
- **Network Payload:** Compress aggressively before sending. Send Text over Audio whenever possible.
- **UI Responsiveness:** Use Optimistic Updates (TanStack Query) for all mutations.
- **Aesthetic:** Minimalist, Monochrome (Slate/Zinc palette), White background, highly professional.
- **Typography:** Base font size is `14px` (`text-sm`), titles are `Medium` (500) rather than huge.
- **Layout:** Compact padding/margins. Nested left sidebar for clear navigation without clutter.
- **Simplicity First:** Eliminate complexity of traditional ERPs. Minimal steps for every action.
- **Human-in-the-Loop:** AI never performs destructive actions (like saving to DB) directly. It generates a "Draft/Pending" state for the user to review and "Confirm" manually.

---

## 2. Tech Stack & Libraries

- **Framework:** React 18+ (Vite).
- **Language:** TypeScript (Strict mode).
- **Routing:** React Router DOM (v6+).
- **Styling:** Tailwind CSS v4.
- **UI Components:** Shadcn UI (Radix UI primitives).
- **State Management:** TanStack Query v5 & Zustand.
- **Forms:** React Hook Form + Zod.
- **Icons:** Lucide React (18px for standard icons).

---

## 3. Design Tokens (Monochrome / Slate)

### Color Palette

- **Background:** White (`#ffffff`)
- **Primary / Text:** Slate 900 (`#0f172a`)
- **Borders / Muted:** Slate 200 (`#e2e8f0`) / Slate 50 (`#f8fafc`)
- **Accent/Hover:** Slate 800 (`#1e293b`)
- **Surface Variants:**
  - Sidebar background: Slate 100 (`#f1f5f9`)
  - Active menu item: Slate 200 (`#e2e8f0`)
  - Hover states: Slate 50 (`#f8fafc`)

### Status Colors

- **Success:** `#15803d` (text) / `#dcfce7` (background)
- **Alert/Error:** `#b91c1c` (text) / `#fee2e2` (background)
- **Warning:** `#d97706` (text) / `#fef3c7` (background)
- **Info:** `#0284c7` (text) / `#e0f2fe` (background)

### Brand Colors

- **Primary Brand:** Deep Trust Blue - Professional/Reliable
- **Usage:** Primary actions, active states, links

### Typography

- **Base Font:** Inter (UI elements, body text)
- **Display Font:** Public Sans (Headers, group labels)
- **Base Size:** `14px` (`text-sm`)
- **Line Height:** `1.6` for body text
- **Letter Spacing:** `-0.02em` for headings (premium feel)
- **Font Weights:**
  - Regular: 400
  - Medium: 500 (titles, labels)
  - Semibold: 600 (emphasis, active states)
  - Bold: 700 (rare, only for critical alerts)

---

## 4. Responsive Design Rules ⭐ (MANDATORY)

### 4.1 Breakpoint Strategy

All components MUST be responsive across these breakpoints:

```
Mobile:    < 640px   (sm)
Tablet:    640px - 1024px  (md, lg)
Desktop:   > 1024px  (xl, 2xl)
```

**Tailwind Breakpoints:**

- `sm:` 640px (mobile landscape / small tablets)
- `md:` 768px (tablets portrait)
- `lg:` 1024px (tablets landscape / small desktops)
- `xl:` 1280px (standard desktops)
- `2xl:` 1536px (large screens)

### 4.2 Mobile-First Approach

- **Write mobile styles FIRST**, then enhance for larger screens
- Use `sm:`, `md:`, `lg:` as progressive enhancements
- Example:

  ```tsx
  // ✅ CORRECT - Mobile first
  <div className="flex flex-col md:flex-row lg:gap-6">

  // ❌ WRONG - Desktop first
  <div className="flex flex-row md:flex-col">
  ```

### 4.3 Layout Responsiveness

#### Grid Systems

- **Mobile (default):** Single column layout
  ```tsx
  <div className="grid grid-cols-1 gap-4">
  ```
- **Tablet (md):** 2 columns
  ```tsx
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
  ```
- **Desktop (lg/xl):** 3-4 columns for dashboards
  ```tsx
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
  ```

#### Flex Layouts

- **Stack on mobile, row on desktop:**
  ```tsx
  <div className="flex flex-col md:flex-row gap-4">
  ```
- **Full width mobile, auto desktop:**
  ```tsx
  <div className="w-full md:w-auto">
  ```

### 4.4 Component-Specific Responsive Rules

#### Tables

- **Master Table Pattern (MANDATORY):** All data tables MUST follow [RULES_UI_TABLE.md](docs/rules/RULES_UI_TABLE.md) and reuse tokens from [`mini-erp/src/lib/data-table-layout.ts`](mini-erp/src/lib/data-table-layout.ts): **one** `<Table>` (shared `thead`/`tbody` in the same scroll area), not split header/body tables; fixed scroll on the list container with `[scrollbar-gutter:stable]`.
- **Mobile (< md):**
  - Stack rows vertically (card-like presentation)
  - Hide non-essential columns
  - Use "Show more" expandable sections
  - Horizontal scroll as LAST resort (with visual indicator)
- **Tablet (md - lg):**
  - Show essential columns only
  - Reduce padding (`px-2 py-3` instead of `px-4 py-4`)
- **Desktop (> lg):**
  - Full table with all columns
  - Standard padding

**Example - Responsive Table:**

```tsx
// Mobile: Card view
<div className="block md:hidden">
  {data.map(item => (
    <div className="mb-4 p-4 border rounded-lg">
      <div className="font-medium">{item.name}</div>
      <div className="text-sm text-muted-foreground">{item.sku}</div>
      {/* Essential info only */}
    </div>
  ))}
</div>

// Desktop: Table view
<div className="hidden md:block">
  <Table>
    <TableHeader>...</TableHeader>
    <TableBody>...</TableBody>
  </Table>
</div>
```

#### Forms

- **Mobile:**
  - Full-width inputs (`w-full`)
  - Stack labels above inputs (not inline)
  - Increase touch targets to 44px minimum
  - Use appropriate input types (`tel`, `email`, `number`)
- **Tablet/Desktop:**
  - Multi-column layouts where logical
  - Max-width containers for readability (`max-w-2xl`)

**Example - Responsive Form:**

```tsx
<form className="space-y-4 md:space-y-6">
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div className="space-y-2">
      <label>First Name</label>
      <Input className="w-full" />
    </div>
    <div className="space-y-2">
      <label>Last Name</label>
      <Input className="w-full" />
    </div>
  </div>
</form>
```

#### Cards / KPI Widgets

- **Mobile:** 1 column, full width
- **Tablet:** 2 columns
- **Desktop:** 3-4 columns depending on content

```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
  <KpiCard title="Revenue" value="12.5M" />
  <KpiCard title="Orders" value="142" />
  <KpiCard title="Low Stock" value="8" alert />
  <KpiCard title="Pending" value="3" />
</div>
```

#### Modals / Dialogs

- **Mobile:**
  - Full-screen or bottom-sheet style
  - `className="w-full h-full md:max-w-lg md:h-auto"`
- **Tablet/Desktop:**
  - Centered with max-width
  - Proper overlay backdrop

#### Sidebar Navigation

- **Mobile (< lg):**
  - Hidden by default, slide-in on toggle
  - Overlay backdrop when open
  - Close on route change or overlay click
- **Desktop (≥ lg):**
  - Persistent, visible
  - Resizable (192px - 320px, default 256px)

**Implementation:**

```tsx
// Mobile overlay
{
  isOpen && (
    <div
      className="fixed inset-0 bg-black/50 lg:hidden z-40"
      onClick={closeSidebar}
    />
  );
}

// Sidebar with responsive behavior
<Sidebar
  className={`
    fixed lg:relative inset-y-0 left-0 z-50
    transform transition-transform duration-200
    ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
  `}
/>;
```

### 4.5 Typography Responsiveness

#### Headings

- **Mobile:** `text-lg` or `text-xl` (avoid huge headings)
- **Tablet:** `text-xl` or `text-2xl`
- **Desktop:** `text-2xl` or `text-3xl`

```tsx
<h1 className="text-xl md:text-2xl lg:text-3xl font-medium">Dashboard</h1>
```

#### Body Text

- **Base:** `text-sm` (14px) across all breakpoints
- **Large text:** `text-base` on mobile for readability
- **Small text:** `text-xs` for captions, timestamps (use sparingly)

### 4.6 Spacing Responsiveness

- **Mobile:** Compact but not cramped
  - Gaps: `gap-3` (12px) to `gap-4` (16px)
  - Padding: `p-3` to `p-4`
- **Tablet:**
  - Gaps: `gap-4` to `gap-6`
  - Padding: `p-4` to `p-6`
- **Desktop:**
  - Gaps: `gap-6` to `gap-8`
  - Padding: `p-6` to `p-8`

**Example:**

```tsx
<div className="p-4 md:p-6 lg:p-8 space-y-4 md:space-y-6">
```

### 4.7 Touch Targets & Accessibility

- **ALL interactive elements:** Minimum 44x44px
- **Buttons:** `min-h-[44px]` on mobile, `h-9` (36px) on desktop acceptable
- **Icon buttons:** `p-3` minimum (creates 44x44 touch area with 18px icon)

```tsx
// ✅ CORRECT
<button className="min-h-[44px] md:h-9 px-4">
  Click me
</button>

// ❌ WRONG
<button className="h-8 px-2">
  Too small!
</button>
```

### 4.8 Images & Media

- **Responsive images:** Use `w-full h-auto` for fluid scaling
- **Object-fit:** Specify for consistent aspect ratios
  ```tsx
  <img className="w-full h-48 md:h-64 object-cover" />
  ```
- **Lazy loading:** Add `loading="lazy"` for below-fold images

### 4.9 Hidden/Visible Utilities

- **Hide on mobile:** `hidden md:block`
- **Show only on mobile:** `block md:hidden`
- **Hide on desktop:** `lg:hidden`

**Example - Responsive Actions:**

```tsx
<div className="flex gap-2">
  {/* Icon only on mobile, full text on desktop */}
  <Button className="md:hidden">
    <PlusIcon className="h-5 w-5" />
  </Button>
  <Button className="hidden md:flex">
    <PlusIcon className="h-4 w-4" />
    Add New
  </Button>
</div>
```

### 4.10 Testing Responsiveness

- **ALWAYS test** on these viewport sizes before marking complete:
  - Mobile: 375px (iPhone SE), 414px (iPhone 14 Pro Max)
  - Tablet: 768px (iPad), 834px (iPad Pro)
  - Desktop: 1280px, 1920px
- **Use Chrome DevTools Device Mode** for quick checks
- **Verify NO horizontal scroll** on any page (except data tables with explicit scroll)

### 4.11 Common Responsive Patterns

#### Pattern 1: Header with Actions

```tsx
<div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
  <h1 className="text-xl md:text-2xl font-medium">Page Title</h1>
  <div className="flex gap-2">
    <Button>Action</Button>
  </div>
</div>
```

#### Pattern 2: Filter/Search Bar

```tsx
<div className="flex flex-col md:flex-row gap-4 mb-6">
  <Input className="flex-1" placeholder="Search..." />
  <Select>
    <SelectTrigger className="w-full md:w-[180px]">
      <SelectValue placeholder="Filter" />
    </SelectTrigger>
  </Select>
</div>
```

#### Pattern 3: Detail View

```tsx
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  {/* Main content - 2/3 on desktop */}
  <div className="lg:col-span-2">{/* Primary content */}</div>

  {/* Sidebar content - 1/3 on desktop, stacks below on mobile */}
  <div className="lg:col-span-1">{/* Secondary content */}</div>
</div>
```

---

## 5. TypeScript Rules

1. **Strict Type Safety:** No `any`. Use `unknown` or specific interfaces.
2. **Feature-based Types:** Keep types close to the feature they belong to (`features/{name}/types.ts`).
3. **API Typing:** Define request/response interfaces for all API endpoints.

---

## 6. Architecture Rules

1. **Feature-Folder Pattern:** `src/features/{feature-name}` containing `components/`, `hooks/`, `api/`, `types.ts`, and `index.ts`.
2. **Hook-Logic Separation:** Keep complex logic in custom hooks, keep components focused on UI.
3. **API Centralization:** Use TanStack Query hooks in a dedicated `api/` folder within each feature.

---

## 7. AI Integration Rules

1. **Voice-to-Action:** Convert speech to text locally (Web Speech API) -> Send structured text to Backend.
2. **OCR-to-Data:** Compress images via `browser-image-compression` before sending to Backend OCR (Azure Document Intelligence).
3. **Confirmation Pattern:** AI-generated data must stay in "Draft" state until user clicks "Confirm".

---

## 8. Performance Rules

1. **Zero Perceived Latency:** Always use skeletons or optimistic UI for mutations.
2. **Payload Compression:** Aggressively compress images before upload.
3. **Asset Optimization:** Use Lucide icons (SVG) and minimal third-party libraries.
4. **Code Splitting:** Lazy load feature routes where possible (`React.lazy`).
5. **Image Optimization:** Compress all images before rendering (use `browser-image-compression` for user uploads).

---

## 9. Accessibility (A11y) Rules

### 9.1 General Accessibility

- **Semantic HTML:** Use proper elements (`<nav>`, `<main>`, `<header>`, `<section>`, `<article>`)
- **ARIA labels:** Add to all interactive elements without visible text
- **Keyboard navigation:** Ensure all features work with Tab/Enter/Escape
- **Focus management:** Visible focus states, trap focus in modals

### 9.2 Color Contrast

- **Normal text (14px):** Minimum 4.5:1 contrast ratio
- **Large text (18px+):** Minimum 3:1 contrast ratio
- **Test with:** WebAIM Contrast Checker or browser dev tools

### 9.3 Screen Reader Support

- **Alt text:** All meaningful images need descriptive alt text
- **Form labels:** Every input must have associated label
- **Error messages:** Use `aria-describedby` to link errors to inputs

### 9.4 Touch Targets (Reiterated)

- **Minimum:** 44x44px for ALL interactive elements
- **Spacing:** Minimum 8px gap between touch targets

---

## 10. Implementation Rules

1. **Compact Components:** Avoid excessively large buttons or inputs unless requested. Default height for inputs/buttons is ~36px (`h-9`).
2. **Never use Tesseract.js.** Use Backend API for OCR.
3. **Optimistic Updates:** Mandatory via TanStack Query for all mutations.
4. **Shadcn UI First:** Always use Shadcn components before custom ones.
5. **No Horizontal Overflow:** Pages MUST NOT cause horizontal scrolling on any viewport (test with `overflow-x-hidden` on body).
6. **Loading States:** Always show loading/skeleton states during data fetching.
7. **Error Handling:** Display user-friendly error messages with retry options.

---

## 11. Project Structure

- **`src/features/{feature-name}/`**: Main business logic and UI for a specific domain.
  - `components/`: UI components specific only to this feature.
  - `pages/`: Page-level components integrated with React Router.
  - `hooks/`: Custom hooks containing logic for this feature.
  - `api/`: Data fetching hooks using TanStack Query.
  - `types.ts`: Type and interface definitions for this feature.
  - `index.ts`: The public entry point (exports) for the feature.
- **`src/components/`**: Shared components across multiple features.
  - `ui/`: Base Shadcn/Radix components (primitives).
  - `shared/`: Reusable high-level components (Layouts, Sidebar, etc.).
- **`src/hooks/`**: Global utility hooks (e.g., `useMediaQuery`).
- **`src/store/`**: Global state management using Zustand stores.
- **`src/lib/`**: External library configurations (QueryClient, Axios instances).
- **`src/types/`**: Global/shared TypeScript definitions.

---

## 12. Documentation & Task Management

1. **Task Location:** All new tasks must be documented in `TASKS/TaskXXX.md`.
2. **Task Template:** Every task must follow this standard structure:
   - **Goal:** Clear business objective and link to project philosophy.
   - **Design Specs:** Direct citation of Design Tokens (Colors, Typography, Spacing).
   - **Technical Specs:** Folder location, tech stack requirements (Zod, TanStack, etc.).
   - **⚠️ Component Breakdown (MANDATORY):** List every component to create/modify:
     - Component name + file path
     - Props interface (if any)
     - Brief function description
     - Responsive behavior (mobile/tablet/desktop)
       > **Note:** Tasks WITHOUT Component Breakdown will be rejected. Learned from Task008 - missing component analysis causes rework.
   - **Step-by-Step Plan:** Granular implementation steps.
   - **Verification Checklist:** Mandatory "Verify against Rules.md" step including responsive testing.
3. **AI Compliance:** Every time a task is created or updated, the AI must explicitly verify it against the rules in `RULES.md` AND `RULES_BUG_FIX.md`.
4. **Tone:** Use professional, guiding, and authoritative language consistent with "The Guided Sanctuary".
5. **Definition of Done (DoD):** Một tác vụ chỉ được coi là hoàn thành (`Completed`) khi:
   - Mã nguồn tuân thủ 100% `RULES.md`.
   - Đã vượt qua kiểm tra Linting và Type-check.
   - Các logic tính toán quan trọng đã có Unit Test.
   - Đã cập nhật trạng thái trong file `TaskXXX.md` tương ứng.

---

## 13. Key Paths

Quick reference to essential locations in the codebase.

- **Shared Layouts:** `src/components/shared/layout/`
- **Shadcn UI:** `src/components/ui/`
- **Stores (Zustand):** `src/store/`
- **Features:** `src/features/{feature-name}/`
- **Entry Point:** `src/App.tsx`
- **Design Tokens:** `src/index.css` (@theme section)

---

## 14. Naming Conventions (Quy tắc đặt tên)

1. **Components:** PascalCase (ví dụ: `InventoryTable.tsx`).
2. **Hooks:** camelCase, bắt đầu bằng `use` (ví dụ: `useInventory.ts`).
3. **Folders:** kebab-case (ví dụ: `product-management`).
4. **Interfaces/Types:** PascalCase, KHÔNG dùng tiền tố `I` (ví dụ: `User`, không phải `IUser`).
5. **Variables/Functions:** camelCase (ví dụ: `calculateTotal`).

---

## 15. Testing Strategy (Chiến lược kiểm thử)

1. **Unit Testing:** Bắt buộc cho các logic nghiệp vụ lõi (tính tồn kho, lãi lỗ). Sử dụng **Vitest**.
2. **E2E Testing:** Tập trung vào các luồng quan trọng (Login -> Nhập kho -> Phê duyệt). Sử dụng **Playwright**.
3. **Quy tắc:** Mọi tiện ích (utility) chứa logic phức tạp phải có file `.test.ts` đi kèm.

---

## 16. Error Handling & Feedback (Xử lý lỗi)

1. **Toasts:** Sử dụng `sonner` cho tất cả thông báo thành công/thất bại.
2. **API Errors:**
   - `401`: Tự động điều hướng về `/login`.
   - `403`: Hiển thị Toast "Bạn không có quyền thực hiện hành động này".
   - `500`: Hiển thị Toast "Hệ thống đang bận, vui lòng thử lại sau".
3. **UI Safety:** Sử dụng `ErrorBoundary` cho các container tính năng quan trọng.

---

## 17. Localization (Tiêu chuẩn UI Tiếng Việt)

1. **100% Vietnamese UI:** Tất cả văn bản hiển thị cho người dùng phải là tiếng Việt.
2. **Tiền tệ:** Định dạng theo `vi-VN` (ví dụ: `1.200.000 ₫`).
3. **Ngày tháng:** Định dạng `DD/MM/YYYY`.
4. **Số liệu:** Dùng dấu `.` cho hàng nghìn và dấu `,` cho thập phân.

---

## 18. Git & Commit Guidelines

1. **Conventional Commits:** `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`.
2. **Branching:** `feature/TaskXXX` hoặc `bug/TaskXXX`.
3. **Commit:** Mỗi commit nên giải quyết một đơn vị công việc nhỏ hoặc hoàn thành một bước trong Task.

---

## 19. Quick Reference Checklist

Before submitting any UI code, verify:

- [ ] **Responsive across breakpoints:** Mobile (375px), Tablet (768px), Desktop (1280px)
- [ ] **Touch targets ≥ 44px:** All buttons, inputs, icon buttons
- [ ] **Mobile-first approach:** Base styles for mobile, enhance for larger screens
- [ ] **No horizontal overflow:** Page doesn't scroll horizontally unexpectedly
- [ ] **Proper spacing:** Responsive padding/gap values
- [ ] **Typography scales:** Headings appropriate for each viewport
- [ ] **Loading states:** Skeletons or spinners during data fetch
- [ ] **Error handling:** User-friendly error messages with retry
- [ ] **Accessibility:** ARIA labels, keyboard navigation, contrast ratios
- [ ] **Shadcn first:** Using existing components before custom
- [ ] **TypeScript strict:** No `any`, proper interfaces
- [ ] **Optimistic updates:** TanStack Query for mutations
- [ ] **Autonomous Workflow:** Follow the BA-to-DOC_SYNC flow per Section 20.

---

## 20. Agent System & Workflow Automation (MANDATORY) 🤖

The AI Assistant MUST operate as an autonomous agent system following the rules in **[`AGENTS/WORKFLOW_RULE.md`](AGENTS/WORKFLOW_RULE.md)**. 

### 20.1 Workflow Stages
1. **Agent BA (Business Analyst):** Mandatory first step. Handles Elicitation, PRD, Prototype, and User Story Spec.
   > **STOP:** Must provide a summary and wait for User's "Approve" before proceeding to Phase 2.
2. **Agent PM (Project Manager):** Triggered after Approval. Allocates Task IDs and creates 3 Task files (UNIT, FEATURE, E2E).
3. **Agent TECH_LEAD:** Writes ADRs (if architecture changed) and defines guardrails.
4. **Agent DEV (Developer):** Implements TDD (Red -> Green -> Refactor) with ≥ 80% coverage gate.
5. **Agent CODEBASE_ANALYST:** Performs 10-phase brownfield discovery and logic extraction.
6. **Agent DOC_SYNC:** Checks for documentation drift and updates `RULES_BUG_FIX.md` via Knowledge Harvesting.

### 20.2 Operational Rules
- **No Manual Triggers:** The AI will automatically switch roles and proceed through the sequence after the "Gate 1" approval.
- **Strict Adherence:** No stage can be skipped. Every stage must produce its defined output.
- **Reporting:** Each stage must report completion to the "Project Manager" (AI) before the next stage starts.
- **Context Loading:** Before starting any new task, read all relevant agent instructions in the `AGENTS/` directory to ensure full compliance with the specific role's standards.
