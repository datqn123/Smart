# BUG ELICITATION - Bug025_03: Tách Header ra khỏi khối cuộn (Standalone Header)

**Status: Open**
**User Suggestion**: "Đặt thanh header ra khỏi table thử, lúc này table chỉ có dữ liệu thôi".

## 1. Phân tích Kỹ thuật
- **Vấn đề hiện tại**: Header đang nằm trong khối cuộn. Khi có nhiều lớp container lồng nhau (MainLayout vs InboundPage), trình duyệt khó xác định context sticky chính xác, dẫn đến lỗi "trôi" header.
- **Giải pháp**: 
  - Tạo một khối Header tĩnh nằm trên Scroll Container.
  - Sử dụng chung cấu trúc columns (Width cố định) giữa Header và Body để đảm bảo căn lề.
  - Loại bỏ hoàn toàn phức hợp `sticky` vốn dễ gây lỗi trên các trình duyệt/container khác nhau.

## 2. Thay đổi cấu trúc UI
```
[Filter Bar]
[Standalone Table Header] (Tĩnh)
[Scroll Container]
   [Table Body Only] (Cuộn)
```

## 3. Fix Requirement
- Header không bao giờ biến mất khi cuộn dọc.
- Các cột Header và Body phải thẳng hàng tuyệt đối.
- Duy trì style hiện tại (bg-slate-50 cho header).

---
**Agent BA done.** Chuyển Agent PM điều phối.
