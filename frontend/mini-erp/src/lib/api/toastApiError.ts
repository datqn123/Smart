import { toast } from "sonner"
import { ApiRequestError } from "./http"

export function toastApiError(error: unknown, fallback = "Da xay ra loi"): void {
  if (error instanceof ApiRequestError) {
    const message = error.body?.message?.trim()
    toast.error(message || error.message)
    return
  }
  toast.error(error instanceof Error ? error.message : fallback)
}

export function toastMutationEnvelope(error: unknown): void {
  if (!(error instanceof ApiRequestError)) {
    toastApiError(error)
    return
  }

  const detailKeys = error.body?.details ? Object.keys(error.body.details) : []
  if (error.status === 400 && detailKeys.length > 0) {
    return
  }

  if (error.status === 409 || error.status === 403 || error.status === 400) {
    toast.error(error.body?.message ?? error.message)
    return
  }

  toastApiError(error)
}
