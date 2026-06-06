import type { LedgerEntry } from "../types"

export function signedLedgerAmount(entry: LedgerEntry): number | null {
  if (typeof entry.amount === "number" && !Number.isNaN(entry.amount)) {
    return entry.amount
  }
  if (entry.credit > 0) return entry.credit
  if (entry.debit > 0) return -entry.debit
  return null
}

export function calculateLedgerTotals(data: LedgerEntry[]) {
  const amount = data.reduce((sum, entry) => sum + (signedLedgerAmount(entry) ?? 0), 0)
  const debit = data.reduce((sum, entry) => sum + entry.debit, 0)
  const credit = data.reduce((sum, entry) => sum + entry.credit, 0)
  const finalBalance = data.at(-1)?.balance ?? 0
  return { amount, debit, credit, finalBalance }
}
