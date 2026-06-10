import { useEffect, useState } from "react"

/**
 * Trả về phiên bản trễ (debounced) của `value`: chỉ cập nhật sau khi `value`
 * ngừng thay đổi trong `delayMs` mili-giây. Dùng cho ô tìm kiếm để tránh gọi
 * API/đổi queryKey trên mỗi lần gõ phím.
 *
 * Thay thế pattern lặp lại trước đây ở ~14 trang:
 *   const [debounced, setDebounced] = useState("")
 *   useEffect(() => {
 *     const t = setTimeout(() => setDebounced(value), 400)
 *     return () => clearTimeout(t)
 *   }, [value])
 */
export function useDebouncedValue<T>(value: T, delayMs = 400): T {
  const [debounced, setDebounced] = useState<T>(value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}
