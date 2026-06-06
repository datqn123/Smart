import { useEffect, useMemo } from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import { Toaster } from "sonner"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import { LoginPage } from "./features/auth/pages/LoginPage"
import { DashboardPage } from "./features/dashboard/pages/DashboardPage"
import { MainLayout } from "./components/shared/layout/MainLayout"

// Inventory
import { InboundPage } from "./features/inventory/pages/InboundPage"
import { StockPage } from "./features/inventory/pages/StockPage"
import { DispatchPage } from "./features/inventory/pages/DispatchPage"

// Product Management
import { CategoriesPage } from "./features/product-management/pages/CategoriesPage"
import { ProductsPage } from "./features/product-management/pages/ProductsPage"
import { SuppliersPage } from "./features/product-management/pages/SuppliersPage"
import { CustomersPage } from "./features/product-management/pages/CustomersPage"

// Orders
import { RetailPage } from "./features/orders/pages/RetailPage"
import { WholesalePage } from "./features/orders/pages/WholesalePage"
import { ReturnsPage } from "./features/orders/pages/ReturnsPage"

// Cashflow
import { TransactionsPage } from "./features/cashflow/pages/TransactionsPage"
import { DebtPage } from "./features/cashflow/pages/DebtPage"
import { LedgerPage } from "./features/cashflow/pages/LedgerPage"

// Approvals
import PendingApprovalsPage from "./features/approvals/pages/PendingApprovalsPage"
import ApprovalHistoryPage from "./features/approvals/pages/ApprovalHistoryPage"

// Analytics
import { RevenuePage } from "./features/analytics/pages/RevenuePage"
import { TopProductsPage } from "./features/analytics/pages/TopProductsPage"

// Settings
import { StoreInfoPage } from "./features/settings/pages/StoreInfoPage"
import { EmployeesPage } from "./features/settings/pages/EmployeesPage"
import { AlertSettingsPage } from "./features/settings/pages/AlertSettingsPage"
import { LogsPage } from "./features/settings/pages/LogsPage"
import { InterfaceSettingsPage } from "./features/settings/pages/InterfaceSettingsPage"
import { CustomBuilderPage } from "./features/custom-builder/pages/CustomBuilderPage"
import { CustomRuntimePage } from "./features/custom-builder/pages/CustomRuntimePage"
import { WarehouseLocationsPage } from "./features/inventory/pages/WarehouseLocationsPage"
import { ChatBotPage } from "./features/ai/pages/ChatBotPage"

import { PageTitleProvider } from "./context/PageTitleContext"
import { hasResumeSessionInSessionStorage } from "@/features/auth/lib/clientSessionResume"

// Placeholder pages - TODO: Implement these
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="p-6">
    <h1 className="text-2xl font-medium text-slate-900 mb-4">{title}</h1>
    <p className="text-slate-600">Trang đang được phát triển...</p>
  </div>
)

/** Task101 — F5: đồng bộ user + claim `mp` từ sessionStorage. */
function AuthSessionHydration() {
  const hydrate = useAuthStore((s) => s.hydrateFromSession)
  useEffect(() => {
    hydrate()
  }, [hydrate])
  return null
}

/** `/` → dashboard nếu sessionStorage còn phiên hợp lệ, không ép qua màn login. */
function RootEntryRedirect() {
  const to = useMemo(() => (hasResumeSessionInSessionStorage() ? "/dashboard" : "/login"), [])
  return <Navigate to={to} replace />
}

function App() {
  return (
    <PageTitleProvider>
      <AuthSessionHydration />
      <Toaster position="top-right" richColors />
      <Routes>
        {/* Auth Routes (No Sidebar) */}
        <Route path="/login" element={<LoginPage />} />

        {/* Main Layout Routes (With Sidebar) */}
        <Route element={<MainLayout />}>
          {/* Dashboard */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Inventory Routes */}
          <Route path="/inventory/stock" element={<StockPage />} />
          <Route path="/inventory/locations" element={<WarehouseLocationsPage />} />
          <Route path="/inventory/inbound" element={<InboundPage />} />
          <Route path="/inventory/dispatch" element={<DispatchPage />} />
          <Route path="/inventory/audit" element={<Navigate to="/inventory/stock" replace />} />

          {/* Products Routes */}
          <Route path="/products/categories" element={<CategoriesPage />} />
          <Route path="/products/list" element={<ProductsPage />} />
          <Route path="/products/suppliers" element={<SuppliersPage />} />
          <Route path="/products/customers" element={<CustomersPage />} />

          {/* Orders Routes */}
          <Route path="/orders/retail" element={<RetailPage />} />
          <Route path="/orders/wholesale" element={<WholesalePage />} />
          <Route path="/orders/returns" element={<ReturnsPage />} />

          {/* Approvals hub removed — old URLs redirect */}
          <Route path="/approvals/pending" element={<PendingApprovalsPage />} />
          <Route path="/approvals/history" element={<ApprovalHistoryPage />} />

          {/* Cashflow Routes */}
          <Route path="/cashflow/transactions" element={<TransactionsPage />} />
          <Route path="/cashflow/debt" element={<DebtPage />} />
          <Route path="/cashflow/ledger" element={<LedgerPage />} />

          {/* Analytics Routes */}
          <Route path="/analytics/revenue" element={<RevenuePage />} />
          <Route path="/analytics/top-products" element={<TopProductsPage />} />

          {/* AI Tools Routes */}
          <Route path="/ai/chat" element={<ChatBotPage />} />

          {/* Custom Runtime Routes */}
          <Route path="/custom/:pageKey" element={<CustomRuntimePage />} />
          <Route path="/custom/:pageKey/:recordId" element={<CustomRuntimePage />} />

          {/* Settings Routes */}
          <Route path="/settings/store-info" element={<StoreInfoPage />} />
          <Route path="/settings/employees" element={<EmployeesPage />} />
          <Route path="/settings/alerts" element={<AlertSettingsPage />} />
          <Route path="/settings/interface" element={<InterfaceSettingsPage />} />
          <Route path="/settings/custom-builder" element={<CustomBuilderPage />} />
          <Route path="/settings/system-logs" element={<LogsPage />} />
        </Route>

        {/* Default and 404 Routes */}
        <Route path="/" element={<RootEntryRedirect />} />
        <Route path="*" element={
          <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 font-medium">
            404 - Trang không tồn tại
          </div>
        } />
      </Routes>
    </PageTitleProvider>
  )
}

export default App
