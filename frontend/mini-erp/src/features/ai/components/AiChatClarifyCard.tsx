import { useMemo, useState } from "react"
import { HelpCircle, Pencil, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import type { DomainClarifyPayload } from "../api/aiDomainClarifyTypes"

type Props = {
  payload: DomainClarifyPayload
  onPickSuggestion?: (text: string) => void
}

export function AiChatClarifyCard({ payload, onPickSuggestion }: Props) {
  const {
    questions,
    issues,
    assistantIntro,
    originalQuestion,
    suggestedRewrite,
    suggestedNormalized,
  } = payload
  const intro = (assistantIntro || "").trim()
  const suggested = (suggestedRewrite || suggestedNormalized || "").trim()
  const original = (originalQuestion || "").trim()
  const hasRewrite = Boolean(suggested && original && suggested !== original)

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(suggested)

  const displayDraft = useMemo(() => {
    if (editing) return draft
    return suggested
  }, [editing, draft, suggested])

  const submit = (text: string) => {
    const t = text.trim()
    if (t && onPickSuggestion) onPickSuggestion(t)
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-slate-800 shadow-sm">
      <div className="mb-2 flex items-center gap-2 font-semibold text-amber-900">
        <HelpCircle className="h-4 w-4 shrink-0" />
        Cần làm rõ
      </div>
      {intro ? (
        <p className="mb-2 whitespace-pre-line text-slate-700">{intro.replace(/\*\*/g, "")}</p>
      ) : null}
      {issues.length > 0 ? (
        <ul className="mb-2 list-disc space-y-1 pl-5 text-slate-700">
          {issues.map((issue, i) => (
            <li key={i}>
              {issue.canonical_vi ? (
                <>
                  «{issue.user_text}» → <strong>{issue.canonical_vi}</strong>
                  {issue.canonical_en ? ` (${issue.canonical_en})` : null}
                </>
              ) : (
                issue.user_text || issue.type
              )}
            </li>
          ))}
        </ul>
      ) : null}
      {questions.length > 0 ? (
        <ul className="mb-3 space-y-1 text-slate-700">
          {questions.map((q, i) => (
            <li key={i}>• {q}</li>
          ))}
        </ul>
      ) : null}

      {hasRewrite && onPickSuggestion ? (
        <div className="space-y-2 rounded-lg border border-amber-200/80 bg-white/90 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-amber-800">
            Câu đề xuất (đã sửa thuật ngữ)
          </div>
          {original ? (
            <div className="text-xs text-slate-500 line-through decoration-slate-400">
              {original}
            </div>
          ) : null}
          {editing ? (
            <Textarea
              className="min-h-[72px] resize-y border-amber-200 text-sm"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
          ) : (
            <div className="text-sm font-medium leading-relaxed text-slate-900">
              {displayDraft}
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              className="h-8 gap-1.5 bg-blue-600 hover:bg-blue-700"
              onClick={() => submit(editing ? draft : suggested)}
            >
              <Send className="h-3.5 w-3.5" />
              Gửi câu đề xuất
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-8 gap-1.5 border-amber-300"
              onClick={() => {
                if (editing) {
                  setEditing(false)
                  setDraft(suggested)
                } else {
                  setDraft(suggested)
                  setEditing(true)
                }
              }}
            >
              <Pencil className="h-3.5 w-3.5" />
              {editing ? "Huỷ sửa" : "Chỉnh sửa"}
            </Button>
          </div>
        </div>
      ) : suggested && onPickSuggestion ? (
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="border-amber-300"
          onClick={() => submit(suggested)}
        >
          Gửi lại
        </Button>
      ) : null}
    </div>
  )
}
