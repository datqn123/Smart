export type QueryTableColumn = {
  key: string
  label?: string
  type?: string
}

export type QueryTablePayload = {
  title?: string
  columns: QueryTableColumn[]
  rows: Record<string, unknown>[]
  rowCount: number
  truncated: boolean
  maxDisplayRows: number
}
