import type { ReactElement } from "react"
import { render } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { TransactionsPage } from "./TransactionsPage"
import { describe, it, expect, vi } from "vitest"
import { PageTitleProvider } from "@/context/PageTitleContext"

function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <PageTitleProvider>{ui}</PageTitleProvider>
    </QueryClientProvider>,
  )
}

// Mock lucide-react
vi.mock("lucide-react", () => ({
  Banknote: () => <div data-testid="banknote-icon" />,
  TrendingUp: () => <div data-testid="trending-up-icon" />,
  TrendingDown: () => <div data-testid="trending-down-icon" />,
  DollarSign: () => <div data-testid="dollar-sign-icon" />,
  Info: () => <div data-testid="info-icon" />,
}))

// Mock components
vi.mock("../components/TransactionToolbar", () => ({
  TransactionToolbar: () => <div data-testid="transaction-toolbar" />,
}))

vi.mock("../components/TransactionTable", () => ({
  TransactionTable: () => <table data-testid="transaction-table" />,
}))

vi.mock("../components/TransactionDetailDialog", () => ({
  TransactionDetailDialog: () => <div data-testid="transaction-detail-dialog" />,
}))

vi.mock("../components/TransactionFormDialog", () => ({
  TransactionFormDialog: () => <div data-testid="transaction-form-dialog" />,
}))

describe("TransactionsPage Runtime Test", () => {
  it("should render without crashing", () => {
    const { getByText } = renderWithProviders(<TransactionsPage />)
    
    expect(getByText("Giao dịch thu chi")).toBeTruthy()
  })

  it("should display the summary cards", () => {
    const { getByText } = renderWithProviders(<TransactionsPage />)
    
    expect(getByText("Tổng thu")).toBeTruthy()
    expect(getByText("Tổng chi")).toBeTruthy()
    expect(getByText("Số dư")).toBeTruthy()
  })
})
