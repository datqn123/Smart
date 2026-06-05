import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  sidebarWidth: number
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarWidth: (width: number) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: typeof window !== 'undefined' ? window.innerWidth >= 768 : false,
      sidebarWidth: 256, // default w-64 is 256px
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarWidth: (width) => set({ sidebarWidth: width }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({ sidebarWidth: state.sidebarWidth }), // Only persist sidebarWidth
    }
  )
)
