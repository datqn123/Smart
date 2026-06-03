# Technical Specification - Khắc phục các lỗi nghẽn hiệu năng render (UI Rendering Bottlenecks)

> **File**: `docs/fix-bug/002_tech-spec-ui-rendering-bottlenecks.md`  
> **Người viết**: Agent TECH_SPEC_WRITER  
> **Ngày cập nhật**: 03/06/2026  
> **Trạng thái**: Approved  
> **Readiness**: `READY_FOR_CODING`

---

## 1. Tham chiếu & Tài liệu liên quan
- **Tài liệu SRS**: [001_srs-ui-rendering-bottlenecks.md](file:///d:/do_an_tot_nghiep/project/docs/fix-bug/001_srs-ui-rendering-bottlenecks.md)
- **Tài liệu phân tích**: [ui_rendering_analysis.md](file:///C:/Users/Admin/.gemini/antigravity/brain/fbfca5d3-7889-4732-b719-f00cbd281be3/ui_rendering_analysis.md)

---

## 2. Kế hoạch Hiện thực hóa & Thiết kế Chi tiết (Detailed Technical Design)

### Giai đoạn 1: Khắc phục `PageTitleContext.tsx`
Để triệt tiêu hiện tượng double-render trên tất cả các trang, chúng ta loại bỏ state React (`title`) khỏi Context vì không có bất kỳ component nào tiêu thụ giá trị này. Hàm `setTitle` sẽ được tối giản thành một callback tĩnh cập nhật trực tiếp `document.title` (DOM API) và không thay đổi tham chiếu qua mỗi lần render.

**Mã nguồn đề xuất thay đổi trong [PageTitleContext.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/context/PageTitleContext.tsx):**
```tsx
import { createContext, useContext, useCallback, type ReactNode } from "react"

interface PageTitleContextType {
  title: string
  setTitle: (title: string) => void
}

const PageTitleContext = createContext<PageTitleContextType | undefined>(undefined)

export function PageTitleProvider({ children }: { children: ReactNode }) {
  // Hàm setTitle tĩnh, chỉ cập nhật document.title trực tiếp
  const setTitle = useCallback((newTitle: string) => {
    const cleanTitle = newTitle.trim()
    document.title = cleanTitle ? `${cleanTitle} - Mini ERP` : "Mini ERP"
  }, [])

  // Trả về đối tượng tĩnh luôn ổn định về mặt tham chiếu
  return (
    <PageTitleContext.Provider value={{ title: "", setTitle }}>
      {children}
    </PageTitleContext.Provider>
  )
}

export function usePageTitle() {
  const context = useContext(PageTitleContext)
  if (context === undefined) {
    throw new Error("usePageTitle must be used within PageTitleProvider")
  }
  return context
}
```

*Lợi ích:* 
- Context value `{ title: "", setTitle }` sẽ hoàn toàn tĩnh (stable reference) vì `setTitle` được bọc bởi `useCallback` với mảng dependency rỗng.
- Tất cả 29 trang tiêu thụ `usePageTitle()` sẽ **chỉ render đúng 1 lần duy nhất** khi chuyển hướng, hoàn toàn miễn dịch với các cập nhật tiêu đề.

---

### Giai đoạn 2: Tối ưu hóa Selector của Zustand Store trong Layout
Khắc phục lỗi `MainLayout` và `Header` bị re-render liên tục khi kéo giãn độ rộng Sidebar (`sidebarWidth`).

#### 2.1 Chỉnh sửa trong [MainLayout.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/MainLayout.tsx)
```tsx
// Thay thế dòng 7:
// const { sidebarOpen, setSidebarOpen } = useUIStore()

// Bằng:
const sidebarOpen = useUIStore((s) => s.sidebarOpen)
const setSidebarOpen = useUIStore((s) => s.setSidebarOpen)
```

#### 2.2 Chỉnh sửa trong [Header.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Header.tsx)
```tsx
// Thay thế dòng 75:
// const { sidebarOpen, setSidebarOpen } = useUIStore()

// Bằng:
const sidebarOpen = useUIStore((s) => s.sidebarOpen)
const setSidebarOpen = useUIStore((s) => s.setSidebarOpen)
```

---

### Giai đoạn 3: Tối ưu hóa cập nhật trạng thái Sidebar
Trong [Sidebar.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Sidebar.tsx), chúng ta chỉ gọi cập nhật mở rộng menu cha nếu menu cha đó thực sự chưa nằm trong tập hợp các phần tử đang được mở rộng.

**Mã nguồn đề xuất thay đổi (dòng 221-229):**
```tsx
  // Trước đây:
  useEffect(() => {
    // Find parent of current route and expand it automatically
    const activeParent = filteredNavItems.find(item => 
      item.subItems?.some(sub => isActiveRoute(sub.path))
    )
    if (activeParent) {
      expandItem(activeParent.id)
    }
  }, [location.pathname, expandItem, filteredNavItems])

  // Giải pháp:
  useEffect(() => {
    // Tìm nhóm cha chứa route hiện tại để tự động mở rộng
    const activeParent = filteredNavItems.find(item => 
      item.subItems?.some(sub => isActiveRoute(sub.path))
    )
    if (activeParent && !expandedItems.has(activeParent.id)) {
      expandItem(activeParent.id)
    }
  }, [location.pathname, expandItem, filteredNavItems, expandedItems])
```

---

## 3. Danh sách các file cần chỉnh sửa (Files to Read & Edit)

- **Đọc & Ghi (Read & Edit)**:
  * [frontend/mini-erp/src/context/PageTitleContext.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/context/PageTitleContext.tsx)
  * [frontend/mini-erp/src/components/shared/layout/MainLayout.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/MainLayout.tsx)
  * [frontend/mini-erp/src/components/shared/layout/Header.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Header.tsx)
  * [frontend/mini-erp/src/components/shared/layout/Sidebar.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Sidebar.tsx)

---

## 4. Kế hoạch Kiểm thử & Xác thực (Verification Plan)

### 4.1 Automated Tests (Kiểm thử tự động)
Chạy bộ kiểm thử tự động của frontend để đảm bảo cấu trúc Layout và các trang liên quan không bị lỗi render:
```powershell
# Chạy các bài test đơn vị liên quan đến Layout và Pages để đảm bảo tính đúng đắn cấu trúc
npm run test --prefix frontend/mini-erp
```
Đặc biệt, đảm bảo dự án build thành công:
```powershell
npm run build --prefix frontend/mini-erp
```

### 4.2 Manual Verification (Kiểm thử thủ công)
1. **Kiểm tra FPS khi resize Sidebar**:
   - Sử dụng Performance Panel của Chrome DevTools. Thực hiện kéo giãn Sidebar liên tục. Xác minh mức sử dụng CPU tối thiểu và FPS không bị giảm sâu (duy trì trên 55 FPS).
2. **Kiểm tra số lần render**:
   - Gắn log `console.log("Render Layout")` hoặc dùng React Profiler để xác nhận khi chuyển hướng trang, `MainLayout` chỉ commit render 1 lần.
