import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

/** Shape produced by ai_python `chart_spec_final` (Recharts-friendly). */
type ChartSpecShape = {
  chartType?: string
  xKey?: string
  title?: string
  data?: Array<Record<string, unknown>>
  series?: Array<{ dataKey?: string; name?: string }>
}

function isDataRow(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v)
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
    const xs = xv === null || xv === undefined ? "" : String(xv)
    return { [xKey]: xs, [yKey]: yn }
  })
}

export function AiChatChartCard({ spec }: { spec: Record<string, unknown> }) {
  const s = spec as ChartSpecShape
  const rawData = Array.isArray(s.data) ? s.data.filter(isDataRow) : []
  const xKey = typeof s.xKey === "string" && s.xKey.trim() ? s.xKey.trim() : null
  const seriesArr = Array.isArray(s.series) ? s.series : []
  const yKey =
    typeof seriesArr[0]?.dataKey === "string" && seriesArr[0].dataKey.trim()
      ? seriesArr[0].dataKey.trim()
      : null
  const chartType = s.chartType === "line" ? "line" : "bar"
  const title = typeof s.title === "string" ? s.title.trim() : ""
  const yName =
    typeof seriesArr[0]?.name === "string" && seriesArr[0].name.trim()
      ? seriesArr[0].name.trim()
      : yKey ?? "Giá trị"

  if (!xKey || !yKey) {
    return (
      <div className="mt-3 rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-950">
        Thiếu cấu hình trục biểu đồ từ server (xKey / series.dataKey).
      </div>
    )
  }

  if (rawData.length === 0) {
    return (
      <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        Không có dữ liệu để vẽ biểu đồ (mảng <span className="font-mono">data</span> rỗng).
      </div>
    )
  }

  const data = normalizeRows(rawData, xKey, yKey)

  return (
    <div className="mt-3 w-full min-w-0 rounded-xl border border-slate-200 bg-white px-1 pb-2 pt-2 shadow-sm">
      {title ? (
        <div className="mb-1 px-2 text-sm font-semibold tracking-tight text-slate-800">{title}</div>
      ) : null}
      <div className="h-[240px] w-full min-w-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "line" ? (
            <LineChart data={data} margin={{ top: 8, right: 12, bottom: 8, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="#64748b" interval={0} angle={-20} height={50} textAnchor="end" />
              <YAxis tick={{ fontSize: 11 }} stroke="#64748b" width={56} />
              <Tooltip formatter={(v: number | string) => [typeof v === "number" ? v.toLocaleString("vi-VN") : v, yName]} />
              <Legend />
              <Line type="monotone" dataKey={yKey} name={yName} stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          ) : (
            <BarChart data={data} margin={{ top: 8, right: 12, bottom: 8, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="#64748b" interval={0} angle={-20} height={50} textAnchor="end" />
              <YAxis tick={{ fontSize: 11 }} stroke="#64748b" width={56} />
              <Tooltip formatter={(v: number | string) => [typeof v === "number" ? v.toLocaleString("vi-VN") : v, yName]} />
              <Legend />
              <Bar dataKey={yKey} name={yName} fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <p className="mt-1 px-2 text-[10px] text-slate-400">
        {data.length} {data.length === 1 ? "dòng" : "dòng"} dữ liệu từ truy vấn
      </p>
    </div>
  )
}
