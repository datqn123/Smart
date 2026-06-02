import { create } from "zustand"

export type NavItemKey =
  | "dashboard"
  | "inventory"
  | "products"
  | "orders"
  | "cashflow"
  | "analytics"
  | "ai-tools"
  | "settings"
  | `custom-${string}`

interface SidebarStore {
  expandedItems: Set<NavItemKey>
  toggleItem: (key: NavItemKey) => void
  expandItem: (key: NavItemKey) => void
  collapseItem: (key: NavItemKey) => void
}

export const useSidebarStore = create<SidebarStore>((set) => ({
  expandedItems: new Set(),
  toggleItem: (key) =>
    set((state) => {
      const newSet = new Set(state.expandedItems)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return { expandedItems: newSet }
    }),
  expandItem: (key) =>
    set((state) => {
      const newSet = new Set(state.expandedItems)
      newSet.add(key)
      return { expandedItems: newSet }
    }),
  collapseItem: (key) =>
    set((state) => {
      const newSet = new Set(state.expandedItems)
      newSet.delete(key)
      return { expandedItems: newSet }
    }),
}))
