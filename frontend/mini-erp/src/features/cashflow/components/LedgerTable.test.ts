import { describe, expect, it } from "vitest"

import { calculateLedgerTotals } from "../lib/ledgerTotals"
import type { LedgerEntry } from "../types"

describe("calculateLedgerTotals", () => {
  it("totals signed amount, debit, credit and final balance", () => {
    const rows: LedgerEntry[] = [
      {
        id: 1,
        date: "2026-05-01",
        transactionCode: "FL-1",
        description: "Thu",
        amount: 3000,
        debit: 0,
        credit: 3000,
        balance: 3000,
      },
      {
        id: 2,
        date: "2026-05-02",
        transactionCode: "FL-2",
        description: "Chi",
        amount: -1000,
        debit: 1000,
        credit: 0,
        balance: 2000,
      },
    ]

    expect(calculateLedgerTotals(rows)).toEqual({
      amount: 2000,
      debit: 1000,
      credit: 3000,
      finalBalance: 2000,
    })
  })

  it("returns zero totals for empty data", () => {
    expect(calculateLedgerTotals([])).toEqual({
      amount: 0,
      debit: 0,
      credit: 0,
      finalBalance: 0,
    })
  })
})
