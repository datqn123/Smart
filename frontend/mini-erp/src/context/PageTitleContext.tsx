import { createContext, useContext, useCallback, useMemo, type ReactNode } from "react"

interface PageTitleContextType {
  title: string
  setTitle: (title: string) => void
}

const PageTitleContext = createContext<PageTitleContextType | undefined>(undefined)

export function PageTitleProvider({ children }: { children: ReactNode }) {
  const setTitle = useCallback((newTitle: string) => {
    const cleanTitle = newTitle.trim()
    document.title = cleanTitle ? `${cleanTitle} - Mini ERP` : "Mini ERP"
  }, [])

  const value = useMemo(() => ({ title: "", setTitle }), [setTitle])

  return (
    <PageTitleContext.Provider value={value}>
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
