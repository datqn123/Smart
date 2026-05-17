export type DomainClarifyIssue = {
  type?: string
  user_text?: string
  canonical_vi?: string | null
  canonical_en?: string | null
  guide_ref?: string | null
  severity?: string
}

export type DomainClarifyPayload = {
  questions: string[]
  issues: DomainClarifyIssue[]
  guideRefs: string[]
  /** Original user message (may contain wrong terms). */
  originalQuestion?: string
  /** Suggested corrected question — use this for resubmit. */
  suggestedRewrite?: string
  /** @deprecated use suggestedRewrite */
  suggestedNormalized?: string
  matchedModules?: string[]
}
