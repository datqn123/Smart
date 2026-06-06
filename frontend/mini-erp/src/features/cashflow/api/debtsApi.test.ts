import { beforeEach, describe, expect, it, vi } from "vitest"

import { getDebtById, getDebtsList, patchDebt, postDebt } from "./debtsApi"

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal("fetch", fetchMock)
  sessionStorage.clear()
})

function mockEnvelope(data: unknown) {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    status: 200,
    text: async () => JSON.stringify({ success: true, data }),
  })
}

describe("debtsApi", () => {
  it("builds list query with search, filters, due date range and pagination", async () => {
    mockEnvelope({ items: [], page: 2, limit: 20, total: 0 })

    await getDebtsList({
      search: "KH-001",
      partnerType: "Customer",
      status: "InDebt",
      dueDateFrom: "2026-05-01",
      dueDateTo: "2026-05-31",
      page: 2,
      limit: 20,
    })

    const calledUrl = String(fetchMock.mock.calls[0][0])
    expect(calledUrl).toContain("/api/v1/debts?")
    expect(calledUrl).toContain("search=KH-001")
    expect(calledUrl).toContain("partnerType=Customer")
    expect(calledUrl).toContain("status=InDebt")
    expect(calledUrl).toContain("dueDateFrom=2026-05-01")
    expect(calledUrl).toContain("dueDateTo=2026-05-31")
    expect(calledUrl).toContain("page=2")
    expect(calledUrl).toContain("limit=20")
  })

  it("posts a debt create body to /api/v1/debts", async () => {
    mockEnvelope({ id: 1 })

    await postDebt({
      partnerType: "Supplier",
      supplierId: 3,
      customerId: null,
      totalAmount: 5000000,
      paidAmount: 0,
      dueDate: "2026-06-30",
      notes: "Nhap hang",
    })

    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/v1/debts")
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: "POST" })
    expect(JSON.parse(String(fetchMock.mock.calls[0][1].body))).toEqual({
      partnerType: "Supplier",
      supplierId: 3,
      customerId: null,
      totalAmount: 5000000,
      paidAmount: 0,
      dueDate: "2026-06-30",
      notes: "Nhap hang",
    })
  })

  it("gets and patches debt detail by id", async () => {
    mockEnvelope({ id: 9 })
    await getDebtById(9)
    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/v1/debts/9")
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: "GET" })

    mockEnvelope({ id: 9, paidAmount: 1000 })
    await patchDebt(9, { paymentAmount: 1000 })
    expect(String(fetchMock.mock.calls[1][0])).toContain("/api/v1/debts/9")
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: "PATCH" })
    expect(JSON.parse(String(fetchMock.mock.calls[1][1].body))).toEqual({ paymentAmount: 1000 })
  })
})
