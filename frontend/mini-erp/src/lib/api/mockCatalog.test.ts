import { describe, expect, it } from "vitest"

import {
  frontendApiMockCatalog,
  getMockCatalogEntry,
  mockError,
  mockList,
  mockSuccess,
  type MockHttpMethod,
} from "./mockCatalog"

const requiredEndpoints: Array<[MockHttpMethod, string]> = [
  ["POST", "/api/v1/auth/login"],
  ["POST", "/api/v1/auth/refresh"],
  ["POST", "/api/v1/auth/logout"],
  ["GET", "/api/v1/notifications"],
  ["PATCH", "/api/v1/notifications/{id}"],
  ["GET", "/api/v1/inventory/summary"],
  ["GET", "/api/v1/inventory"],
  ["GET", "/api/v1/inventory/{id}"],
  ["PATCH", "/api/v1/inventory/{id}"],
  ["PATCH", "/api/v1/inventory/bulk"],
  ["GET", "/api/v1/stock-receipts"],
  ["POST", "/api/v1/stock-receipts"],
  ["POST", "/api/v1/stock-receipts/{id}/approve"],
  ["GET", "/api/v1/stock-dispatches"],
  ["POST", "/api/v1/stock-dispatches/from-order"],
  ["POST", "/api/v1/stock-dispatches/{id}/approve"],
  ["GET", "/api/v1/inventory/audit-sessions"],
  ["POST", "/api/v1/inventory/audit-sessions/{id}/complete"],
  ["GET", "/api/v1/categories"],
  ["GET", "/api/v1/products"],
  ["POST", "/api/v1/products"],
  ["POST", "/api/v1/products/{id}/images"],
  ["GET", "/api/v1/suppliers"],
  ["GET", "/api/v1/customers"],
  ["GET", "/api/v1/sales-orders"],
  ["GET", "/api/v1/sales-orders/retail/history"],
  ["POST", "/api/v1/sales-orders/retail/checkout"],
  ["GET", "/api/v1/pos/products"],
  ["GET", "/api/v1/vouchers"],
  ["GET", "/api/v1/approvals/pending"],
  ["GET", "/api/v1/cash-funds"],
  ["GET", "/api/v1/cash-transactions"],
  ["GET", "/api/v1/store-profile"],
  ["GET", "/api/v1/roles"],
  ["GET", "/api/v1/users"],
  ["GET", "/api/v1/alert-settings"],
  ["GET", "/api/v1/system-logs"],
  ["GET", "/api/v1/interface-settings/table-columns"],
  ["PUT", "/api/v1/interface-settings/table-columns"],
  ["POST", "/api/v1/ai/chat/stream"],
  ["POST", "/api/v1/ai/chat/transcribe"],
  ["POST", "/api/v1/ai/chat/synthesize"],
  ["POST", "/api/v1/ai/catalog-drafts/validate"],
  ["POST", "/api/v1/ai/catalog-drafts/{id}/commit"],
  ["POST", "/api/v1/ai/inventory-drafts/validate"],
  ["POST", "/api/v1/ai/inventory-drafts/{id}/commit"],
]

describe("frontendApiMockCatalog", () => {
  it("wraps success and error envelopes with the shared frontend API shape", () => {
    expect(mockSuccess({ ok: true })).toEqual({
      success: true,
      data: { ok: true },
    })

    expect(mockError("BAD_REQUEST", "Du lieu khong hop le", { name: "Bat buoc" })).toEqual({
      success: false,
      error: "BAD_REQUEST",
      message: "Du lieu khong hop le",
      details: { name: "Bat buoc" },
    })
  })

  it("builds deterministic list pages", () => {
    expect(mockList([1, 2, 3], 2, 2)).toEqual({
      items: [1, 2, 3],
      page: 2,
      limit: 2,
      total: 3,
      totalPages: 2,
    })
  })

  it("contains the endpoint coverage required by the SRS", () => {
    for (const [method, path] of requiredEndpoints) {
      expect(getMockCatalogEntry(method, path), `${method} ${path}`).toBeDefined()
    }
  })

  it("keeps every entry API-shaped and uniquely addressable", () => {
    const endpointKeys = new Set<string>()

    for (const entry of frontendApiMockCatalog) {
      expect(entry.path.startsWith("/api/v1/"), entry.path).toBe(true)
      expect(["json", "multipart", "sse"]).toContain(entry.kind)
      expect(entry.description.length, `${entry.method} ${entry.path}`).toBeGreaterThan(0)
      expect(endpointKeys.has(`${entry.method} ${entry.path}`), `${entry.method} ${entry.path}`).toBe(false)
      endpointKeys.add(`${entry.method} ${entry.path}`)
    }
  })

  it("normalizes query strings when looking up catalog entries", () => {
    expect(getMockCatalogEntry("GET", "/api/v1/interface-settings/table-columns?scope=inventory")).toMatchObject({
      method: "GET",
      path: "/api/v1/interface-settings/table-columns",
    })
  })

  it("marks AI chat streaming as SSE and upload endpoints as multipart", () => {
    expect(getMockCatalogEntry("POST", "/api/v1/ai/chat/stream")).toMatchObject({ kind: "sse" })
    expect(getMockCatalogEntry("POST", "/api/v1/ai/chat/transcribe")).toMatchObject({ kind: "multipart" })
    expect(getMockCatalogEntry("POST", "/api/v1/products/{id}/images")).toMatchObject({ kind: "multipart" })
  })
})
