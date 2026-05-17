import { useId, useMemo } from "react"
import { BarChart3, PieChart as PieChartIcon } from "lucide-react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { TooltipProps } from "recharts"
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent"

/** Shape produced by ai_python `chart_spec_final` (Recharts-friendly). */
type ChartSpecShape = {
  chartType?: string
  xKey?: string
  title?: string
  data?: Array<Record<string, unknown>>
  series?: Array<{ dataKey?: string; name?: string }>
}

const CHART_PRIMARY = "#2563eb"
const CHART_PRIMARY_MID = "#3b82f6"
/** High-contrast hues — adjacent slices must be easy to tell apart. */
const PIE_SLICE_COLORS = [
  "#2563eb",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#84cc16",
  "#f97316",
  "#6366f1",
]

type PieRow = Record<string, string | number> & {
  __rawX: string
  __fill: string
  __pct: number
}
const AXIS_TICK = { fontSize: 11, fill: "#64748b", fontWeight: 500 as const }
const TOOLTIP_STYLE = {
  borderRadius: 12,
  border: "1px solid #e2e8f0",
  boxShadow: "0 10px 25px -5px rgb(15 23 42 / 0.12)",
  padding: "10px 12px",
}

function isDataRow(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v)
}

/** Short month label for axis (e.g. T5/2026), not full timestamp. */
export function formatChartAxisLabel(value: unknown): string {
  if (value === null || value === undefined) return ""
  const s = String(value).trim()
  if (!s) return ""

  const iso = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (iso) {
    return `T${parseInt(iso[2], 10)}/${iso[1]}`
  }

  const dmy = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/)
  if (dmy) {
    return `T${parseInt(dmy[2], 10)}/${dmy[3]}`
  }

  const parsed = new Date(s)
  if (!Number.isNaN(parsed.getTime()) && /\d{4}/.test(s)) {
    return `T${parsed.getMonth() + 1}/${parsed.getFullYear()}`
  }

  return s.length > 14 ? `${s.slice(0, 14)}…` : s
}

function formatChartValue(v: number | string): string {
  if (typeof v === "number" && Number.isFinite(v)) {
    return v.toLocaleString("vi-VN")
  }
  return String(v)
}

function normalizeRows(
  rows: Array<Record<string, unknown>>,
  xKey: string,
  yKey: string,
): Array<Record<string, string | number>> {
  return rows.map((row) => {
    const xv = row[xKey]
    const yv = row[yKey]
    let yn: number
    if (typeof yv === "number" && Number.isFinite(yv)) yn = yv
    else if (typeof yv === "string") {
      const parsed = Number(String(yv).replace(/,/g, "").replace(/\s/g, ""))
      yn = Number.isFinite(parsed) ? parsed : 0
    } else yn = 0
    const raw = xv === null || xv === undefined ? "" : String(xv)
    return {
      [xKey]: formatChartAxisLabel(raw),
      __rawX: raw,
      [yKey]: yn,
    }
  })
}

function PieTooltipContent({
  active,
  payload,
  xKey,
}: TooltipProps<ValueType, NameType> & { xKey: string }) {
  if (!active || !payload?.length) return null
  const row = payload[0]
  const pl = row?.payload as PieRow | undefined
  const name = String(row?.name ?? pl?.[xKey] ?? "")
  const value = Number(row?.value ?? 0)
  const pct = typeof pl?.__pct === "number" ? pl.__pct : 0
  const color = pl?.__fill ?? row?.color ?? PIE_SLICE_COLORS[0]

  return (
    <div className="min-w-[148px] rounded-xl border border-slate-200/90 bg-white px-3.5 py-3 shadow-lg">
      <div className="flex items-center gap-2">
        <span
          className="h-3 w-3 shrink-0 rounded-full ring-2 ring-white"
          style={{ backgroundColor: String(color) }}
          aria-hidden
        />
        <p className="text-sm font-semibold leading-snug text-slate-800">{name}</p>
      </div>
      <p className="mt-2 text-xl font-bold tabular-nums tracking-tight text-slate-900">
        {formatChartValue(value)}
      </p>
      <p className="mt-0.5 text-sm font-medium text-blue-600 tabular-nums">
        {pct.toFixed(1)}% tổng
      </p>
    </div>
  )
}

function ChartTooltipContent({
  active,
  payload,
  label,
  metricLabel,
}: TooltipProps<ValueType, NameType> & { metricLabel: string }) {
  if (!active || !payload?.length) return null
  const row = payload[0]
  const rawX =
    row?.payload && typeof row.payload === "object" && "__rawX" in row.payload
      ? String((row.payload as { __rawX?: string }).__rawX ?? label)
      : String(label ?? "")
  const displayX = formatChartAxisLabel(rawX) || String(label ?? "")
  const value = row?.value

  return (
    <div className="min-w-[120px]">
      <p className="text-[11px] font-medium text-slate-500">{displayX}</p>
      <p className="mt-0.5 text-base font-semibold tabular-nums tracking-tight text-slate-900">
        {formatChartValue(value as number | string)}
      </p>
      {metricLabel && metricLabel !== displayX ? (
        <p className="mt-1 max-w-[220px] truncate text-[10px] text-slate-400">{metricLabel}</p>
      ) : null}
    </div>
  )
}

function chartAxisProps(xKey: string) {
  return {
    dataKey: xKey,
    axisLine: false,
    tickLine: false,
    tick: AXIS_TICK,
    dy: 8,
    interval: 0 as const,
    height: 36,
  }
}

function chartYAxisProps() {
  return {
    axisLine: false,
    tickLine: false,
    tick: AXIS_TICK,
    width: 48,
    tickFormatter: (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)}k` : String(v)),
  }
}

export function AiChatChartCard({ spec }: { spec: Record<string, unknown> }) {
  const gradientId = useId().replace(/:/g, "")
  const s = spec as ChartSpecShape
  const rawData = Array.isArray(s.data) ? s.data.filter(isDataRow) : []
  const xKey = typeof s.xKey === "string" && s.xKey.trim() ? s.xKey.trim() : null
  const seriesArr = Array.isArray(s.series) ? s.series : []
  const yKey =
    typeof seriesArr[0]?.dataKey === "string" && seriesArr[0].dataKey.trim()
      ? seriesArr[0].dataKey.trim()
      : null
  const chartType =
    s.chartType === "line" ? "line" : s.chartType === "pie" ? "pie" : "bar"
  const title = typeof s.title === "string" ? s.title.trim() : ""
  const metricLabel =
    typeof seriesArr[0]?.name === "string" && seriesArr[0].name.trim()
      ? seriesArr[0].name.trim()
      : yKey ?? "Giá trị"

  const data = useMemo(() => {
    if (!xKey || !yKey || rawData.length === 0) return []
    return normalizeRows(rawData, xKey, yKey)
  }, [rawData, xKey, yKey])

  const pieData = useMemo((): PieRow[] => {
    if (!xKey || !yKey || data.length === 0) return []
    const total = data.reduce((sum, row) => sum + (Number(row[yKey]) || 0), 0)
    return data.map((row, i) => {
      const value = Number(row[yKey]) || 0
      return {
        ...row,
        __rawX: String(row.__rawX ?? row[xKey] ?? ""),
        __fill: PIE_SLICE_COLORS[i % PIE_SLICE_COLORS.length],
        __pct: total > 0 ? (value / total) * 100 : 0,
      }
    })
  }, [data, xKey, yKey])

  if (!xKey || !yKey) {
    return (
      <div className="rounded-xl border border-amber-200/80 bg-amber-50/90 px-3 py-2.5 text-xs text-amber-950">
        Thiếu cấu hình trục biểu đồ từ server (xKey / series.dataKey).
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs text-slate-600">
        Không có dữ liệu để vẽ biểu đồ.
      </div>
    )
  }

  const tooltip = (
    <Tooltip
      content={<ChartTooltipContent metricLabel={metricLabel} />}
      cursor={{ fill: "rgba(37, 99, 235, 0.06)" }}
      wrapperStyle={{ outline: "none" }}
      contentStyle={TOOLTIP_STYLE}
    />
  )

  const grid = <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />

  return (
    <div className="w-full min-w-0 overflow-hidden rounded-2xl border border-slate-200/90 bg-gradient-to-b from-slate-50/80 to-white shadow-sm ring-1 ring-slate-900/[0.04]">
      <div className="flex items-start gap-2 border-b border-slate-100 bg-white/60 px-3 py-2.5">
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          {chartType === "pie" ? (
            <PieChartIcon className="h-4 w-4" aria-hidden />
          ) : (
            <BarChart3 className="h-4 w-4" aria-hidden />
          )}
        </div>
        <div className="min-w-0 flex-1">
          {title ? (
            <h4 className="text-sm font-semibold leading-snug tracking-tight text-slate-800 line-clamp-2">
              {title}
            </h4>
          ) : (
            <h4 className="text-sm font-semibold text-slate-800">Biểu đồ dữ liệu</h4>
          )}
          <p className="mt-0.5 text-[11px] text-slate-500">
            {data.length} {chartType === "pie" ? "nhóm" : "mốc thời gian"}
          </p>
        </div>
      </div>

      <div className="h-[260px] w-full min-w-[220px] px-1 pb-2 pt-3">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "line" ? (
            <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <defs>
                <linearGradient id={`line-${gradientId}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={CHART_PRIMARY} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={CHART_PRIMARY} stopOpacity={0} />
                </linearGradient>
              </defs>
              {grid}
              <XAxis {...chartAxisProps(xKey)} />
              <YAxis {...chartYAxisProps()} />
              {tooltip}
              <Line
                type="monotone"
                dataKey={yKey}
                name={metricLabel}
                stroke={CHART_PRIMARY}
                strokeWidth={2.5}
                dot={{ r: 4, fill: CHART_PRIMARY, strokeWidth: 2, stroke: "#fff" }}
                activeDot={{ r: 6, fill: CHART_PRIMARY_MID, stroke: "#fff", strokeWidth: 2 }}
              />
            </LineChart>
          ) : chartType === "pie" ? (
            <PieChart margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
              <Pie
                data={pieData}
                dataKey={yKey}
                nameKey={xKey}
                cx="50%"
                cy="44%"
                innerRadius={0}
                outerRadius={82}
                paddingAngle={3}
                stroke="#fff"
                strokeWidth={2}
                label={false}
                activeShape={{ outerRadius: 92, stroke: "#fff", strokeWidth: 2 }}
              >
                {pieData.map((entry, i) => (
                  <Cell key={`pie-${entry.__rawX}-${i}`} fill={entry.__fill} />
                ))}
              </Pie>
              <Tooltip
                content={<PieTooltipContent xKey={xKey} />}
                wrapperStyle={{ outline: "none", zIndex: 20 }}
                offset={16}
              />
              <Legend
                verticalAlign="bottom"
                height={52}
                content={() => (
                  <ul className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 px-2 pb-1">
                    {pieData.map((entry) => (
                      <li
                        key={String(entry.__rawX)}
                        className="flex items-center gap-1.5 text-[11px] text-slate-700"
                      >
                        <span
                          className="h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ backgroundColor: entry.__fill }}
                          aria-hidden
                        />
                        <span className="font-medium">{String(entry[xKey])}</span>
                        <span className="tabular-nums text-slate-500">
                          {formatChartValue(Number(entry[yKey]))} ({entry.__pct.toFixed(0)}%)
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              />
            </PieChart>
          ) : (
            <BarChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }} barCategoryGap="18%">
              <defs>
                <linearGradient id={`bar-${gradientId}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={CHART_PRIMARY_MID} />
                  <stop offset="100%" stopColor={CHART_PRIMARY} />
                </linearGradient>
              </defs>
              {grid}
              <XAxis {...chartAxisProps(xKey)} />
              <YAxis {...chartYAxisProps()} />
              {tooltip}
              <Bar dataKey={yKey} name={metricLabel} radius={[6, 6, 0, 0]} maxBarSize={48}>
                {data.map((_, i) => (
                  <Cell key={`cell-${i}`} fill={`url(#bar-${gradientId})`} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}
