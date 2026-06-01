import { useEffect, useState } from "react"
import {
  TABLE_COLUMN_SETTINGS_UPDATED_EVENT,
  type TableKey,
  getTableColumnSettings,
} from "@/lib/table-column-settings"

export function useTableColumnOrder(tableKey: TableKey, defaultColumnKeys: string[]) {
  const [visibleKeys, setVisibleKeys] = useState<string[]>(defaultColumnKeys)

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
      setVisibleKeys(keys.length > 0 ? keys : defaultColumnKeys)
    }
    void load()
    const onStorage = (event: StorageEvent) => {
      if (event.key == null || event.key.includes("table_column_settings")) {
        void load()
      }
    }
    const onUpdated = () => {
      void load()
    }
    window.addEventListener("storage", onStorage)
    window.addEventListener(TABLE_COLUMN_SETTINGS_UPDATED_EVENT, onUpdated)
    return () => {
      mounted = false
      window.removeEventListener("storage", onStorage)
      window.removeEventListener(TABLE_COLUMN_SETTINGS_UPDATED_EVENT, onUpdated)
    }
  }, [tableKey, defaultColumnKeys])

  return visibleKeys
}

