export type DomainClarifyIssue = {
  type?: string
  user_text?: string
  canonical_vi?: string | null
  canonical_en?: string | null
  guide_ref?: string | null
  severity?: string
}

export type DomainClarifyPayload = {
  clarifyId?: string
  clarifyKind?: string
  questions: string[]
  /** Main explanation text (inventory/catalog clarify). */
  assistantIntro?: string
  issues: DomainClarifyIssue[]
  guideRefs: string[]
  /** Original user message (may contain wrong terms). */
  originalQuestion?: string
  /** Suggested corrected question — use this for resubmit. */
  suggestedRewrite?: string
  /** @deprecated use suggestedRewrite */
  suggestedNormalized?: string
  matchedModules?: string[]
  continuationContext?: Record<string, unknown>
  requiredChoices?: string[]
}
