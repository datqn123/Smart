import { useId, useMemo, useState } from "react"
import { BarChart3, Maximize2, PieChart as PieChartIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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

function chartAxisProps(xKey: string, dataLength: number) {
  const shouldRotate = dataLength > 8
  return {
    dataKey: xKey,
    axisLine: false,
    tickLine: false,
    tick: shouldRotate
      ? { ...AXIS_TICK, angle: -30, textAnchor: "end" as const }
      : AXIS_TICK,
    dy: shouldRotate ? 4 : 8,
    dx: shouldRotate ? -4 : 0,
    interval: (dataLength > 15 ? "preserveStartEnd" : 0) as any,
    height: shouldRotate ? 64 : 36,
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


type ChartRenderProps = {
  gradientId: string
  chartType: "line" | "pie" | "bar"
  data: Array<Record<string, string | number>>
  pieData: PieRow[]
  xKey: string
  yKey: string
  metricLabel: string
  areaClassName: string
  pieOuterRadius?: number
}

function ChartCanvas({
  gradientId,
  chartType,
  data,
  pieData,
  xKey,
  yKey,
  metricLabel,
  areaClassName,
  pieOuterRadius = 82,
}: ChartRenderProps) {
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
    <div className={areaClassName}>
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
              <XAxis {...chartAxisProps(xKey, data.length)} />
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
                outerRadius={pieOuterRadius}
                paddingAngle={3}
                stroke="#fff"
                strokeWidth={2}
                label={false}
                activeShape={{ outerRadius: pieOuterRadius + 10, stroke: "#fff", strokeWidth: 2 }}
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
              <XAxis {...chartAxisProps(xKey, data.length)} />
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
  )
}

export function AiChatChartCard({ spec }: { spec: Record<string, unknown> }) {
  const [dialogOpen, setDialogOpen] = useState(false)
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

  const [activeChartType, setActiveChartType] = useState<"line" | "pie" | "bar">(chartType)
  const [showAll, setShowAll] = useState(false)

  const data = useMemo(() => {
    if (!xKey || !yKey || rawData.length === 0) return []
    return normalizeRows(rawData, xKey, yKey)
  }, [rawData, xKey, yKey])

  const isTimeBased = useMemo(() => {
    if (data.length === 0 || !xKey) return false
    return data.slice(0, 5).some((row) => {
      const v = String(row.__rawX || row[xKey] || "").trim()
      return (
        /^\d{4}-\d{2}-\d{2}/.test(v) ||
        /^\d{1,2}\/\d{1,2}\/\d{4}/.test(v) ||
        (!Number.isNaN(Date.parse(v)) && /\d{4}/.test(v))
      )
    })
  }, [data, xKey])

  // Group top 10 items + others to ensure readability when data.length > 10
  const processedData = useMemo(() => {
    if (data.length === 0 || !yKey || !xKey) return []
    if (isTimeBased || showAll || data.length <= 10) return data

    // Sort descending by value
    const sorted = [...data].sort((a, b) => Number(b[yKey]) - Number(a[yKey]))
    const top10 = sorted.slice(0, 10)
    const others = sorted.slice(10)
    const othersSum = others.reduce((sum, row) => sum + (Number(row[yKey]) || 0), 0)

    if (othersSum > 0) {
      return [
        ...top10,
        {
          [xKey]: "Khác",
          __rawX: "Khác",
          [yKey]: othersSum,
        },
      ]
    }
    return top10
  }, [data, yKey, xKey, isTimeBased, showAll])

  const pieData = useMemo((): PieRow[] => {
    if (!xKey || !yKey || processedData.length === 0) return []
    const total = processedData.reduce((sum, row) => sum + (Number(row[yKey]) || 0), 0)
    return processedData.map((row, i) => {
      const value = Number(row[yKey]) || 0
      return {
        ...row,
        __rawX: String(row.__rawX ?? row[xKey] ?? ""),
        __fill: PIE_SLICE_COLORS[i % PIE_SLICE_COLORS.length],
        __pct: total > 0 ? (value / total) * 100 : 0,
      }
    })
  }, [processedData, xKey, yKey])

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


  const chartTitle = title || "Biểu đồ dữ liệu"

  const canvasProps: ChartRenderProps = {
    gradientId,
    chartType: activeChartType,
    data: processedData,
    pieData,
    xKey,
    yKey,
    metricLabel,
    areaClassName: "",
  }

  return (
    <>
      <div className="w-full min-w-0 overflow-hidden rounded-2xl border border-slate-200/90 bg-gradient-to-b from-slate-50/80 to-white shadow-sm ring-1 ring-slate-900/[0.04]">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 bg-white/60 px-3 py-2">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              {activeChartType === "pie" ? (
                <PieChartIcon className="h-4 w-4" aria-hidden />
              ) : (
                <BarChart3 className="h-4 w-4" aria-hidden />
              )}
            </div>
            <div className="min-w-0">
              <h4 className="text-sm font-semibold leading-snug tracking-tight text-slate-800 line-clamp-1">
                {chartTitle}
              </h4>
              <p className="text-[10px] text-slate-500">
                {data.length} {activeChartType === "pie" ? "nhóm" : isTimeBased ? "mốc thời gian" : "mặt hàng"}
                {!isTimeBased && data.length > 10 && !showAll && " (đang hiển thị Top 10)"}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Grouping Toggle */}
            {!isTimeBased && data.length > 10 && (
              <button
                type="button"
                onClick={() => setShowAll(prev => !prev)}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-950 shadow-sm transition-all"
              >
                {showAll ? "Thu gọn (Top 10)" : "Hiển thị tất cả"}
              </button>
            )}

            {/* Interactive Chart Selector */}
            <div className="flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-50 p-0.5 shadow-sm">
              <button
                type="button"
                onClick={() => setActiveChartType("bar")}
                className={`rounded px-2 py-1 text-xs font-semibold transition-all ${
                  activeChartType === "bar"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Cột
              </button>
              <button
                type="button"
                onClick={() => setActiveChartType("line")}
                className={`rounded px-2 py-1 text-xs font-semibold transition-all ${
                  activeChartType === "line"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Đường
              </button>
              <button
                type="button"
                onClick={() => setActiveChartType("pie")}
                className={`rounded px-2 py-1 text-xs font-semibold transition-all ${
                  activeChartType === "pie"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Tròn
              </button>
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              className="shrink-0 bg-white h-7 text-xs font-semibold"
              onClick={() => setDialogOpen(true)}
            >
              <Maximize2 className="h-3.5 w-3.5 mr-1" />
              Phóng to
            </Button>
          </div>
        </div>
        
        <ChartCanvas
          {...canvasProps}
          areaClassName="h-[min(300px,38vh)] w-full min-w-[240px] px-1 pb-2 pt-3 md:h-[min(340px,42vh)]"
        />
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="flex max-h-[min(92dvh,720px)] w-full max-w-[min(96vw,900px)] flex-col gap-0 overflow-hidden p-0 sm:max-w-[min(96vw,900px)]">
          <DialogHeader className="border-b border-slate-100 px-5 py-4 text-left">
            <DialogTitle className="text-base">{chartTitle}</DialogTitle>
            <p className="text-xs text-slate-500">
              {data.length} {activeChartType === "pie" ? "nhóm" : isTimeBased ? "mốc thời gian" : "mặt hàng"}
              {!isTimeBased && data.length > 10 && !showAll && " (đang hiển thị Top 10)"}
            </p>
          </DialogHeader>
          <ChartCanvas
            {...canvasProps}
            gradientId={`${gradientId}-dlg`}
            areaClassName="h-[min(480px,62vh)] w-full px-2 pb-4 pt-2"
            pieOuterRadius={120}
          />
        </DialogContent>
      </Dialog>
    </>
  )
}
