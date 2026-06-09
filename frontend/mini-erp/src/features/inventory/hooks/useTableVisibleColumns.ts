import { useEffect, useRef, useState } from "react"
import {
  TABLE_COLUMN_SETTINGS_UPDATED_EVENT,
  type TableKey,
  getTableColumnSettings,
} from "@/lib/table-column-settings"

export function useTableColumnOrder(tableKey: TableKey, defaultColumnKeys: string[]) {
  const [visibleKeys, setVisibleKeys] = useState<string[]>(defaultColumnKeys)

  // Call sites pass an inline array literal, so `defaultColumnKeys` has a new
  // reference on every render. Depend on its content signature (a stable string)
  // instead of the reference, and read the latest array via a ref. Otherwise the
  // effect re-runs every render and fires the table-columns request in a loop.
  const defaultColumnKeysRef = useRef(defaultColumnKeys)
  defaultColumnKeysRef.current = defaultColumnKeys
  const defaultColumnKeysSignature = defaultColumnKeys.join("|")

  useEffect(() => {
    let mounted = true
    const load = async () => {
      const settings = await getTableColumnSettings()
      const table = settings.find((item) => item.tableKey === tableKey)
      if (!mounted || !table) {
        return
      }
      const keys = table.columns
        .filter((column) => column.visible)
        .sort((a, b) => a.order - b.order)
        .map((column) => column.key)
      setVisibleKeys(keys.length > 0 ? keys : defaultColumnKeysRef.current)
    }
    void load()
    const onUpdated = () => {
      void load()
    }
    window.addEventListener(TABLE_COLUMN_SETTINGS_UPDATED_EVENT, onUpdated)
    return () => {
      mounted = false
      window.removeEventListener(TABLE_COLUMN_SETTINGS_UPDATED_EVENT, onUpdated)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableKey, defaultColumnKeysSignature])

  return visibleKeys
}
