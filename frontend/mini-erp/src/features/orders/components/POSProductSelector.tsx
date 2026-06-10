import { useEffect, useMemo, useRef, useState, type FormEvent } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useInfiniteQuery, useQuery } from "@tanstack/react-query"
import { Search, Plus, Loader2, Package, Barcode } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useOrderStore } from "../store/useOrderStore"
import { Card } from "@/components/ui/card"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"
import {
  numUnitPrice,
  POS_PRODUCTS_SEARCH_QUERY_KEY,
  searchPosProducts,
  type PosProductRowDto,
} from "../api/posProductsApi"
import {
  getCategoryList,
  mapNodeDtoToCategory,
} from "@/features/product-management/api/categoriesApi"
import type { Category } from "@/features/product-management/types"

const SEARCH_DEBOUNCE_MS = 400
const POS_PAGE_LIMIT = 40

function errToast(e: unknown) {
  if (e instanceof ApiRequestError) {
    toast.error(e.body?.message ?? e.message)
  } else {
    toast.error(e instanceof Error ? e.message : "Đã xảy ra lỗi")
  }
}

function flattenCategories(categories: Category[]): Category[] {
  const result: Category[] = []
  const walk = (items: Category[]) => {
    items.forEach((item) => {
      result.push(item)
      if (item.children?.length) walk(item.children)
    })
  }
  walk(categories)
  return result
}

export function POSProductSelector() {
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS)
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)
  const [barcodeInput, setBarcodeInput] = useState("")
  const [barcodeError, setBarcodeError] = useState<string | null>(null)
  const [barcodeCandidates, setBarcodeCandidates] = useState<PosProductRowDto[]>([])
  const [isBarcodeSearching, setIsBarcodeSearching] = useState(false)
  const addItem = useOrderStore((state) => state.addItem)
  const barcodeInputRef = useRef<HTMLInputElement>(null)
  const lineIdSeq = useRef(0)

  const categoriesQuery = useQuery({
    queryKey: ["product-management", "categories", "pos-tabs"] as const,
    queryFn: () => getCategoryList({ format: "flat", status: "Active" }),
    staleTime: 60_000,
  })

  const productQuery = useInfiniteQuery({
    queryKey: [...POS_PRODUCTS_SEARCH_QUERY_KEY, debouncedSearch, selectedCategoryId, POS_PAGE_LIMIT],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      searchPosProducts({
        search: debouncedSearch.trim() || undefined,
        categoryId: selectedCategoryId ?? undefined,
        page: pageParam,
        limit: POS_PAGE_LIMIT,
      }),
    getNextPageParam: (lastPage, allPages) => {
      if ((lastPage.items?.length ?? 0) < POS_PAGE_LIMIT) return undefined
      return allPages.length + 1
    },
    staleTime: 30_000,
  })

  useEffect(() => {
    if (productQuery.isError) errToast(productQuery.error)
  }, [productQuery.isError, productQuery.error])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "F2") return
      event.preventDefault()
      barcodeInputRef.current?.focus()
      barcodeInputRef.current?.select()
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const categoryItems = useMemo(
    () => flattenCategories((categoriesQuery.data?.items ?? []).map(mapNodeDtoToCategory)),
    [categoriesQuery.data],
  )

  const items: PosProductRowDto[] = useMemo(() => {
    const seen = new Set<string>()
    const result: PosProductRowDto[] = []
    for (const item of productQuery.data?.pages.flatMap((page) => page.items) ?? []) {
      const key = `${item.productId}-${item.unitId}`
      if (seen.has(key)) continue
      seen.add(key)
      result.push(item)
    }
    return result
  }, [productQuery.data])

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(val)

  const handleAddProduct = (p: PosProductRowDto) => {
    const unitPrice = numUnitPrice(p.unitPrice)
    if (unitPrice <= 0) {
      toast.error("Sản phẩm chưa có giá bán cho đơn vị này.")
      return
    }
    if (p.availableQty <= 0) {
      toast.error("Hết hàng — không thể thêm vào giỏ.")
      return
    }
    lineIdSeq.current += 1
    addItem({
      id: lineIdSeq.current,
      productId: p.productId,
      unitId: p.unitId,
      productName: p.productName,
      skuCode: p.skuCode,
      quantity: 1,
      unitName: p.unitName,
      unitPrice,
      lineTotal: unitPrice,
    })
    toast.success(`Đã thêm ${p.productName}`)
  }

  const handleBarcodeSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const code = barcodeInput.trim()
    if (!code) return

    setBarcodeError(null)
    setBarcodeCandidates([])
    setIsBarcodeSearching(true)
    try {
      const result = await searchPosProducts({ search: code, limit: 5 })
      const normalizedCode = code.toLowerCase()
      const exactMatches = result.items.filter((item) =>
        [item.skuCode, item.barcode]
          .filter((val): val is string => Boolean(val))
          .some((val) => val.toLowerCase() === normalizedCode),
      )
      const candidates = exactMatches.length > 0 ? exactMatches : result.items

      if (candidates.length === 0) {
        setBarcodeError("Không tìm thấy sản phẩm theo mã vừa nhập.")
        return
      }

      if (candidates.length === 1) {
        handleAddProduct(candidates[0])
        setBarcodeInput("")
        return
      }

      setBarcodeCandidates(candidates)
      setBarcodeError("Có nhiều sản phẩm phù hợp, chọn một sản phẩm để thêm vào giỏ.")
    } catch (err) {
      errToast(err)
      setBarcodeError("Không thể tìm sản phẩm theo mã lúc này.")
    } finally {
      setIsBarcodeSearching(false)
    }
  }

  const handlePickBarcodeCandidate = (candidate: PosProductRowDto) => {
    handleAddProduct(candidate)
    setBarcodeInput("")
    setBarcodeError(null)
    setBarcodeCandidates([])
  }

  return (
    <div className="flex flex-col h-full space-y-3">
      <form onSubmit={(event) => void handleBarcodeSubmit(event)} className="shrink-0 space-y-2">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Barcode className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              ref={barcodeInputRef}
              placeholder="Quét/Nhập mã barcode hoặc SKU (F2)"
              className="pl-9 h-10 text-sm bg-white border-slate-200 focus-visible:ring-1 focus-visible:ring-slate-400 focus-visible:border-slate-400"
              value={barcodeInput}
              disabled={isBarcodeSearching}
              onChange={(e) => {
                setBarcodeInput(e.target.value)
                setBarcodeError(null)
                setBarcodeCandidates([])
              }}
            />
          </div>
          <Button
            type="submit"
            variant="secondary"
            className="h-10 px-4 bg-slate-900 text-white hover:bg-slate-800"
            disabled={isBarcodeSearching || barcodeInput.trim().length === 0}
          >
            {isBarcodeSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Thêm"}
          </Button>
        </div>
        {barcodeError && <p className="text-xs font-medium text-amber-700">{barcodeError}</p>}
        {barcodeCandidates.length > 0 && (
          <div className="rounded-lg border border-slate-200 bg-white p-2 shadow-sm">
            <ul className="space-y-1">
              {barcodeCandidates.map((candidate) => (
                <li key={`${candidate.productId}-${candidate.unitId}`}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left hover:bg-slate-50"
                    onClick={() => handlePickBarcodeCandidate(candidate)}
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-semibold text-slate-900">
                        {candidate.productName}
                      </span>
                      <span className="block text-xs text-slate-500">
                        {candidate.skuCode} · {candidate.unitName} · Tồn: {candidate.availableQty}
                      </span>
                    </span>
                    <Plus className="h-4 w-4 shrink-0 text-slate-500" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </form>

      <div className="flex gap-2 shrink-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Tìm sản phẩm (Tên, SKU, Barcode)..."
            className="pl-9 h-10 text-sm bg-white border-slate-200 focus-visible:ring-1 focus-visible:ring-slate-400 focus-visible:border-slate-400"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="shrink-0 overflow-x-auto pb-1 custom-scrollbar">
        <div className="flex min-w-max gap-1.5">
          <Button
            type="button"
            size="sm"
            variant={selectedCategoryId == null ? "default" : "outline"}
            className={selectedCategoryId == null ? "h-8 bg-slate-900 text-white hover:bg-slate-800" : "h-8 border-slate-200 bg-white"}
            onClick={() => setSelectedCategoryId(null)}
          >
            Tất cả
          </Button>
          {categoryItems.map((category) => (
            <Button
              key={category.id}
              type="button"
              size="sm"
              variant={selectedCategoryId === category.id ? "default" : "outline"}
              className={
                selectedCategoryId === category.id
                  ? "h-8 bg-slate-900 text-white hover:bg-slate-800"
                  : "h-8 border-slate-200 bg-white"
              }
              onClick={() => setSelectedCategoryId(category.id)}
            >
              {category.name}
            </Button>
          ))}
          {categoriesQuery.isLoading && (
            <span className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-xs text-slate-500">
              <Loader2 className="h-3 w-3 animate-spin" />
              Đang tải danh mục
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar min-h-[200px]">
        {productQuery.isLoading && (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500 gap-2">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            <p className="text-sm">Đang tải sản phẩm…</p>
          </div>
        )}

        {!productQuery.isLoading && productQuery.isError && (
          <div className="flex flex-col items-center justify-center py-12 gap-3 text-center px-4">
            <p className="text-sm text-slate-600">Không tải được danh sách POS.</p>
            <Button variant="outline" size="sm" type="button" onClick={() => void productQuery.refetch()}>
              Thử lại
            </Button>
          </div>
        )}

        {!productQuery.isLoading && !productQuery.isError && items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400 gap-2">
            <Package className="h-12 w-12 opacity-20" />
            <p className="text-sm">Không có sản phẩm phù hợp.</p>
          </div>
        )}

        {!productQuery.isLoading && !productQuery.isError && items.length > 0 && (
          <div className="space-y-3 pb-4">
            <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
              {items.map((p) => {
                const unitPrice = numUnitPrice(p.unitPrice)
                const outOfStock = p.availableQty <= 0
                const lowStock = !outOfStock && p.availableQty <= 5
                return (
                  <Card
                    key={`${p.productId}-${p.unitId}`}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault()
                        if (!outOfStock && unitPrice > 0) handleAddProduct(p)
                      }
                    }}
                    className={`group transition-all duration-200 overflow-hidden flex flex-col border-slate-200 shadow-sm ${
                      outOfStock || unitPrice <= 0
                        ? "opacity-60 cursor-not-allowed"
                        : "cursor-pointer hover:scale-[1.02] hover:shadow-md"
                    }`}
                    onClick={() => {
                      if (!outOfStock && unitPrice > 0) handleAddProduct(p)
                    }}
                  >
                    <div className="aspect-[4/3] bg-slate-100 relative">
                      {p.imageUrl ? (
                        <img src={p.imageUrl} alt="" className="absolute inset-0 h-full w-full object-cover" />
                      ) : (
                        <div className="absolute inset-0 flex items-center justify-center text-slate-300">
                          <Badge variant="secondary" className="bg-white/80 backdrop-blur-sm text-[9px] px-1">
                            {p.skuCode}
                          </Badge>
                        </div>
                      )}
                      {outOfStock && (
                        <Badge variant="destructive" className="absolute top-1 right-1 text-[8px] h-4 px-1">
                          Hết
                        </Badge>
                      )}
                      {lowStock && (
                        <Badge variant="destructive" className="absolute top-1 right-1 text-[8px] h-4 px-1">
                          Sắp hết
                        </Badge>
                      )}
                    </div>
                    <div className="p-1.5 flex flex-col flex-1">
                      <h3 className="text-[11px] font-semibold text-slate-900 line-clamp-2 leading-tight flex-1">
                        {p.productName}
                      </h3>
                      <p className="text-[9px] text-slate-500 mt-0.5 line-clamp-1">
                        {p.unitName} · {p.availableQty}
                      </p>
                      <div className="mt-1 flex items-center justify-between gap-1">
                        <span className="text-[11px] font-bold text-slate-900 tabular-nums">
                          {formatCurrency(unitPrice)}
                        </span>
                        {!outOfStock && unitPrice > 0 && (
                          <div className="h-5 w-5 shrink-0 rounded-full bg-slate-900 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Plus className="h-2.5 w-2.5" />
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
            {productQuery.hasNextPage && (
              <Button
                type="button"
                variant="outline"
                className="h-10 w-full border-slate-200 bg-white"
                disabled={productQuery.isFetchingNextPage}
                onClick={() => void productQuery.fetchNextPage()}
              >
                {productQuery.isFetchingNextPage ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Tải thêm sản phẩm
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
