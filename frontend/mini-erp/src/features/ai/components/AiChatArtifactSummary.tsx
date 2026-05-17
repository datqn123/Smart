import type { ReactNode } from "react"
import { Maximize2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type Props = {
  icon: ReactNode
  title: string
  description?: string
  badges?: ReactNode
  preview?: ReactNode
  openLabel?: string
  onOpen: () => void
  className?: string
}

/** Compact in-chat preview; full editor opens in Sheet/Dialog. */
export function AiChatArtifactSummary({
  icon,
  title,
  description,
  badges,
  preview,
  openLabel = "Mở rộng",
  onOpen,
  className,
}: Props) {
  return (
    <div
      className={cn(
        "w-full rounded-2xl border border-slate-200/90 bg-white shadow-sm ring-1 ring-slate-900/[0.04]",
        className
      )}
    >
      <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              {icon}
            </span>
            <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
            {badges}
          </div>
          {description ? (
            <p className="text-xs leading-relaxed text-slate-500">{description}</p>
          ) : null}
          {preview ? (
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2 text-xs text-slate-600">
              {preview}
            </div>
          ) : null}
        </div>
        <Button
          type="button"
          size="sm"
          className="shrink-0 bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
          onClick={onOpen}
        >
          <Maximize2 className="h-4 w-4" />
          {openLabel}
        </Button>
      </div>
    </div>
  )
}
