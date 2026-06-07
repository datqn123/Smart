import { describe, expect, it, vi, beforeEach } from "vitest"
import { toast } from "sonner"
import { ApiRequestError } from "./http"
import { toastApiError, toastMutationEnvelope } from "./toastApiError"

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
  },
}))

describe("toastApiError", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("shows body.message when ApiRequestError has body", () => {
    const err = new ApiRequestError(400, { message: "SKU da ton tai" }, "Bad Request")

    toastApiError(err)

    expect(toast.error).toHaveBeenCalledWith("SKU da ton tai")
  })

  it("shows e.message when body.message is absent", () => {
    const err = new ApiRequestError(500, {
      success: false,
      error: "HTTP_ERROR",
      message: "",
    })
    err.message = "Internal Server Error"

    toastApiError(err)

    expect(toast.error).toHaveBeenCalledWith("Internal Server Error")
  })

  it("shows error.message for non ApiRequestError values", () => {
    toastApiError(new Error("network timeout"), "Khong ket noi duoc")

    expect(toast.error).toHaveBeenCalledWith("network timeout")
  })

  it("shows fallback for unknown non-error values", () => {
    toastApiError("some string error", "Loi khong xac dinh")

    expect(toast.error).toHaveBeenCalledWith("Loi khong xac dinh")
  })
})

describe("toastMutationEnvelope", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("is silent for 400 with details", () => {
    const err = new ApiRequestError(
      400,
      { message: "Loi", details: { name: "Ten bat buoc" } },
      "Bad Request",
    )

    toastMutationEnvelope(err)

    expect(toast.error).not.toHaveBeenCalled()
  })

  it("shows message for 409", () => {
    const err = new ApiRequestError(409, { message: "Ma SKU da ton tai" }, "Conflict")

    toastMutationEnvelope(err)

    expect(toast.error).toHaveBeenCalledWith("Ma SKU da ton tai")
  })

  it("shows message for 403", () => {
    const err = new ApiRequestError(403, { message: "Khong co quyen" }, "Forbidden")

    toastMutationEnvelope(err)

    expect(toast.error).toHaveBeenCalledWith("Khong co quyen")
  })
})
