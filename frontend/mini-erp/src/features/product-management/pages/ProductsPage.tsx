import { useEffect, useMemo, useState, useRef } from "react"
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import type { Category, Product } from "../types"
import { ProductToolbar } from "../components/ProductToolbar"
import { ProductTable } from "../components/ProductTable"
import { ProductDetailDialog } from "../components/ProductDetailDialog"
import { ProductForm, ProductFormSubmitAborted, type ProductFormData } from "../components/ProductForm"
import { ConfirmDialog } from "@/components/shared/ConfirmDialog"
import { toast } from "sonner"
import { ApiRequestError } from "@/lib/api/http"
import {
  getCategoryList,
  mapNodeDtoToCategory,
  type GetCategoryListParams,
} from "../api/categoriesApi"
import {
  buildProductCreateBody,
  buildProductPatchBody,
  deleteProduct,
  getProductById,
  getProductList,
  getStagedProductFilesTotalSizeError,
  mapProductListItemDtoToProduct,
  patchProduct,
  postProduct,
  postProductCreateMultipart,
  postProductImageJson,
  postProductImageMultipart,
  postProductsBulkDelete,
  productDetailToEditSnapshot,
  PRODUCT_LIST_SORT_LABEL_VI,
  PRODUCT_LIST_SORT_WHITELIST,
  type GetProductListParams,
  type ProductEditSnapshot,
  type ProductImageDto,
  type ProductListSort,
  type StagedProductImages,
} from "../api/productsApi"
import { useTableColumnOrder } from "@/features/inventory/hooks/useTableVisibleColumns"

const SEARCH_DEBOUNCE_MS = 400
const PAGE_SIZE = 20

function flattenCategories(categories: Category[]): Category[] {
  let result: Category[] = []
  categories.forEach((c) => {
    result.push(c)
    if (c.children?.length) {
      result = result.concat(flattenCategories(c.children))
    }
  })
  return result
}

function errToast(e: unknown) {
  if (e instanceof ApiRequestError) {
    toast.error(e.body?.message ?? e.message)
  } else {
    toast.error(e instanceof Error ? e.message : "Đã xảy ra lỗi")
  }
}

/**
 * Task037 / Task032-style: **409** và **400** không có `details` → toast.
 * **400** + `details`: `ProductForm` map field + toast khi có `details` không thuộc form (vd. `file` kích thước) — onError bên dưới bỏ qua để tránh toast trùng với field validation.
 */
function toastProductMutationEnvelope(e: unknown) {
  if (!(e instanceof ApiRequestError)) {
    errToast(e)
    return
  }
  const { status, body } = e
  const detailKeys = body.details ? Object.keys(body.details) : []
  if (status === 400 && detailKeys.length > 0) {
    return
  }
  if (status === 409) {
    // Chỉ hiển thị message từ server (đã là tiếng Việt, theo từng reason). Không nối failedId/reason thô — tránh toast kỹ thuật.
    toast.error(body.message ?? e.message)
    return
  }
  if (status === 403) {
    toast.error(body.message ?? e.message)
    return
  }
  if (status === 400 && detailKeys.length === 0) {
    toast.error(body.message ?? e.message)
    return
  }
  errToast(e)
}

export function ProductsPage() {
  const { setTitle } = usePageTitle()
  const queryClient = useQueryClient()
  const isOwner = useAuthStore((s) => s.user?.role === "Owner")
  const editSnapshotRef = useRef<ProductEditSnapshot | null>(null)
  const [stagedImages, setStagedImages] = useState<StagedProductImages>({ files: [], urlAdds: [] })

  const [search, setSearch] = useState("")
  const visibleColumnKeys = useTableColumnOrder("product_list", [
    "skuCode",
    "productName",
    "categoryName",
    "stock",
    "price",
    "status",
  ])
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [sort, setSort] = useState<ProductListSort>("updatedAt:desc")
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const scrollRootRef = useRef<HTMLDivElement>(null)
  const loadMoreSentinelRef = useRef<HTMLDivElement>(null)

  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null)
  const [isDeletingBulk, setIsDeletingBulk] = useState(false)

  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | undefined>()

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setSelectedIds([])
  }, [debouncedSearch, statusFilter, categoryFilter, sort])

  useEffect(() => {
    setTitle("Quản lý sản phẩm")
  }, [setTitle])

  const categoryListParams: GetCategoryListParams = useMemo(
    () => ({ format: "tree", status: "Active" }),
    [],
  )

  const { data: categoryListData } = useQuery({
    queryKey: ["product-management", "categories", "tree-for-products-toolbar"] as const,
    queryFn: () => getCategoryList(categoryListParams),
    staleTime: 5 * 60 * 1000,
  })

  const categoryOptions = useMemo(() => {
    const roots = (categoryListData?.items ?? []).map(mapNodeDtoToCategory)
    return flattenCategories(roots).map((c) => ({ id: c.id, name: c.name }))
  }, [categoryListData])

  const categoryIdParam = useMemo(() => {
    if (categoryFilter === "all") return undefined
    const n = Number(categoryFilter)
    return Number.isFinite(n) && n > 0 ? n : undefined
  }, [categoryFilter])

  const listQueryKey = useMemo(
    () =>
      [
        "product-management",
        "products",
        "list",
        debouncedSearch,
        categoryIdParam,
        statusFilter,
        sort,
        PAGE_SIZE,
      ] as const,
    [debouncedSearch, categoryIdParam, statusFilter, sort],
  )

  const {
    data: listInfinite,
    isPending,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: listQueryKey,
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      getProductList({
        search: debouncedSearch.trim() || undefined,
        categoryId: categoryIdParam,
        status: statusFilter as GetProductListParams["status"],
        page: pageParam,
        limit: PAGE_SIZE,
        sort,
      }),
    getNextPageParam: (lastPage) => {
      if (lastPage.items.length < lastPage.limit) {
        return undefined
      }
      if (lastPage.page * lastPage.limit >= lastPage.total) {
        return undefined
      }
      return lastPage.page + 1
    },
  })

  useEffect(() => {
    const root = scrollRootRef.current
    const sentinel = loadMoreSentinelRef.current
    if (!root || !sentinel) {
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const e = entries[0]
        if (e?.isIntersecting && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      },
      { root, rootMargin: "80px", threshold: 0 },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, listInfinite?.pages])

  const {
    data: productDetail,
    isLoading: isProductDetailLoading,
    isError: isProductDetailError,
    error: productDetailError,
  } = useQuery({
    queryKey: ["product-management", "products", "detail", editingProduct?.id ?? 0] as const,
    queryFn: () => getProductById(editingProduct!.id),
    enabled: isFormOpen && !!editingProduct,
  })

  useEffect(() => {
    if (!isFormOpen || !editingProduct) {
      editSnapshotRef.current = null
      return
    }
    if (productDetail && productDetail.id === editingProduct.id) {
      editSnapshotRef.current = productDetailToEditSnapshot(productDetail)
    }
  }, [isFormOpen, editingProduct, productDetail])

  useEffect(() => {
    if (!isProductDetailError) return
    errToast(productDetailError)
  }, [isProductDetailError, productDetailError])

  useEffect(() => {
    if (isFormOpen) {
      setStagedImages({ files: [], urlAdds: [] })
    }
  }, [isFormOpen, editingProduct?.id])

  const createProductMutation = useMutation({
    mutationFn: async (args: { body: ReturnType<typeof buildProductCreateBody>; staged: StagedProductImages }) => {
      const { body, staged } = args
      if (staged.files.length > 0) {
        const created = await postProductCreateMultipart(body, staged.files, { primaryImageIndex: 0 })
        for (const u of staged.urlAdds) {
          await postProductImageJson(created.id, {
            url: u.url,
            sortOrder: u.sortOrder,
            isPrimary: u.isPrimary,
          })
        }
        return created
      }
      const created = await postProduct(body)
      for (const u of staged.urlAdds) {
        await postProductImageJson(created.id, {
          url: u.url,
          sortOrder: u.sortOrder,
          isPrimary: u.isPrimary,
        })
      }
      return created
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "list"] })
      toast.success("Đã tạo sản phẩm")
    },
    onError: toastProductMutationEnvelope,
  })

  const patchMutation = useMutation({
    mutationFn: (args: { id: number; body: Record<string, unknown> }) => patchProduct(args.id, args.body),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["product-management", "products", "list"] })
      queryClient.invalidateQueries({ queryKey: ["product-management", "products", "detail", variables.id] })
      toast.success("Đã cập nhật sản phẩm")
    },
    onError: toastProductMutationEnvelope,
  })

  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => postProductsBulkDelete(ids),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "list"] })
      setSelectedIds([])
      toast.success(
        data.deletedCount > 0 ? `Đã xóa ${data.deletedCount} sản phẩm` : "Đã xóa sản phẩm",
      )
    },
    onError: toastProductMutationEnvelope,
  })

  const deleteProductMutation = useMutation({
    mutationFn: (id: number) => deleteProduct(id),
    onSuccess: (_data, deletedId) => {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "detail", deletedId] })
      setSelectedIds((prev) => prev.filter((i) => i !== deletedId))
      setSelectedProduct((p) => {
        if (p?.id === deletedId) {
          setIsDetailOpen(false)
          return null
        }
        return p
      })
      setEditingProduct((p) => {
        if (p?.id === deletedId) {
          setIsFormOpen(false)
          return undefined
        }
        return p
      })
      toast.success("Đã xóa sản phẩm")
    },
    onError: toastProductMutationEnvelope,
  })

  const products: Product[] = useMemo(
    () =>
      listInfinite?.pages
        ? listInfinite.pages.flatMap((p) => p.items).map(mapProductListItemDtoToProduct)
        : [],
    [listInfinite],
  )

  const firstListPage = listInfinite?.pages[0]
  const total = firstListPage?.total ?? 0

  useEffect(() => {
    if (!isError) return
    errToast(error)
  }, [isError, error])

  const handleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? products.map((p) => p.id) : [])
  }

  const handleToolbarAction = (action: string) => {
    switch (action) {
      case "edit":
        toast.info(`Chỉnh sửa ${selectedIds.length} sản phẩm`)
        break
      case "delete":
        if (!isOwner) {
          toast.error("Chỉ tài khoản Owner mới được xóa hàng loạt sản phẩm.")
          return
        }
        setIsDeletingBulk(true)
        break
      case "create":
        setEditingProduct(undefined)
        setIsFormOpen(true)
        break
    }
  }

  const handleView = (item: Product) => {
    setSelectedProduct(item)
    setIsDetailOpen(true)
  }

  const handleEdit = (item: Product) => {
    setEditingProduct(item)
    setIsFormOpen(true)
  }

  const handleDelete = (item: Product) => {
    if (!isOwner) {
      toast.error("Chỉ tài khoản Owner mới được xóa sản phẩm.")
      return
    }
    setDeleteTarget(item)
  }

  const confirmDelete = () => {
    const target = deleteTarget
    if (!target) return
    void deleteProductMutation.mutateAsync(target.id)
  }

  const confirmBulkDelete = () => {
    if (!isOwner) {
      return
    }
    const ids = [...selectedIds]
    if (ids.length === 0) {
      return
    }
    bulkDeleteMutation.mutate(ids)
  }

  const formCategoryOptions = useMemo(() => categoryOptions, [categoryOptions])

  const handleProductImageAdded = (d: ProductImageDto) => {
    void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "list"] })
    void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "detail"] })
    setSelectedProduct((p) =>
      p?.id === d.productId ? { ...p, imageUrl: d.isPrimary ? d.url : p.imageUrl } : p,
    )
    setEditingProduct((prev) =>
      prev && prev.id === d.productId ? { ...prev, imageUrl: d.isPrimary ? d.url : prev.imageUrl } : prev,
    )
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Quản lý sản phẩm</h1>
        <p className="text-sm text-slate-500 mt-1">Quản lý danh sách sản phẩm, SKU, giá cả</p>
      </div>

      <ProductToolbar
        searchStr={search}
        onSearch={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        categoryFilter={categoryFilter}
        onCategoryChange={setCategoryFilter}
        categoryOptions={categoryOptions}
        selectedIds={selectedIds}
        onAction={handleToolbarAction}
        canBulkDelete={isOwner}
      />

      <div className="flex flex-col sm:flex-row sm:items-center gap-3 shrink-0 text-sm">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-500 whitespace-nowrap">Sắp xếp</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as ProductListSort)}
            className="h-9 px-2 border border-slate-200 bg-white rounded-md text-slate-900 min-w-[180px]"
          >
            {PRODUCT_LIST_SORT_WHITELIST.map((s) => (
              <option key={s} value={s}>
                {PRODUCT_LIST_SORT_LABEL_VI[s]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
        {isPending && !listInfinite ? (
          <div className="p-8 text-center text-slate-500 flex-1" role="status">
            Đang tải danh sách…
          </div>
        ) : isError && !listInfinite ? (
          <div className="p-8 text-center text-red-600 flex-1" role="alert">
            Không tải được danh sách sản phẩm.
          </div>
        ) : (
          <>
            <div
              ref={scrollRootRef}
              className="flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"
            >
              <ProductTable
                data={products}
                visibleColumnKeys={visibleColumnKeys}
                selectedIds={selectedIds}
                onSelect={handleSelect}
                onSelectAll={handleSelectAll}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                canDelete={isOwner}
              />
              <div ref={loadMoreSentinelRef} className="h-1 w-full shrink-0" aria-hidden />
            </div>
            {listInfinite && total > 0 && (
              <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11">
                <span>
                  Đang hiển thị {products.length} / {total} sản phẩm
                </span>
                {isFetchingNextPage && <span className="text-slate-500">Đang tải thêm…</span>}
                {hasNextPage && !isFetchingNextPage && (
                  <span className="text-slate-400 text-xs hidden sm:inline">Cuộn xuống để tải thêm</span>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Xác nhận xóa"
        description={`Bạn có chắc chắn muốn xóa sản phẩm "${deleteTarget?.name}"? Hành động này không thể hoàn tác.`}
      />

      <ConfirmDialog
        open={isDeletingBulk}
        onOpenChange={setIsDeletingBulk}
        onConfirm={confirmBulkDelete}
        title="Xác nhận xóa nhiều"
        description={`Bạn có chắc chắn muốn xóa ${selectedIds.length} sản phẩm đã chọn?`}
      />

      <ProductDetailDialog
        product={selectedProduct}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onImageAdded={handleProductImageAdded}
        onRequestEdit={(p) => {
          setIsDetailOpen(false)
          handleEdit(p)
        }}
      />

      <ProductForm
        key={editingProduct ? `edit-${editingProduct.id}` : "create"}
        open={isFormOpen}
        onOpenChange={(open) => {
          setIsFormOpen(open)
          if (!open) {
            setEditingProduct(undefined)
          }
        }}
        product={editingProduct}
        productDetail={editingProduct ? (productDetail ?? null) : null}
        isProductDetailLoading={Boolean(editingProduct && isProductDetailLoading)}
        hasProductDetailError={Boolean(editingProduct && isProductDetailError)}
        categories={formCategoryOptions}
        onImageAdded={handleProductImageAdded}
        stagedImages={stagedImages}
        onStagedImagesChange={setStagedImages}
        onSubmit={async (data: ProductFormData) => {
          if (editingProduct) {
            const snap = editSnapshotRef.current
            if (!snap) {
              if (isProductDetailLoading) {
                toast.error("Vui lòng đợi tải xong chi tiết sản phẩm")
                throw new ProductFormSubmitAborted()
              }
              toast.error("Không có dữ liệu chi tiết để lưu. Thử đóng và mở lại form.")
              throw new ProductFormSubmitAborted()
            }
            const body = buildProductPatchBody(snap, {
              name: data.name,
              skuCode: data.skuCode,
              barcode: data.barcode,
              categoryId: data.categoryId ?? 0,
              description: data.description,
              weight: data.weight,
              status: data.status,
              salePrice: data.salePrice,
              costPrice: data.costPrice,
              priceEffectiveDate: data.priceEffectiveDate,
            })
            const hasFieldPatch = Object.keys(body).length > 0
            const hasStaged =
              stagedImages.files.length > 0 || stagedImages.urlAdds.length > 0
            if (!hasFieldPatch && !hasStaged) {
              toast.info("Không có thay đổi để lưu")
              throw new ProductFormSubmitAborted()
            }
            if (hasFieldPatch) {
              await patchMutation.mutateAsync({ id: editingProduct.id, body })
            }
            for (let i = 0; i < stagedImages.files.length; i++) {
              const f = stagedImages.files[i]!
              await postProductImageMultipart(editingProduct.id, f, {
                sortOrder: i,
                isPrimary: i === 0,
              })
            }
            for (const u of stagedImages.urlAdds) {
              await postProductImageJson(editingProduct.id, {
                url: u.url,
                sortOrder: u.sortOrder,
                isPrimary: u.isPrimary,
              })
            }
            if (hasStaged) {
              void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "list"] })
              void queryClient.invalidateQueries({ queryKey: ["product-management", "products", "detail"] })
              if (!hasFieldPatch) {
                toast.success("Đã cập nhật ảnh sản phẩm")
              }
            }
            return
          }
          const createBody = buildProductCreateBody({
            skuCode: data.skuCode,
            name: data.name,
            barcode: data.barcode,
            categoryId: data.categoryId && data.categoryId > 0 ? data.categoryId : undefined,
            description: data.description,
            weight: data.weight,
            status: data.status,
            baseUnitName: "Cái",
            costPrice: data.costPrice,
            salePrice: data.salePrice,
            priceEffectiveDate: data.priceEffectiveDate,
          })
          const stagedTotalErr = getStagedProductFilesTotalSizeError(stagedImages.files)
          if (stagedTotalErr) {
            toast.error(stagedTotalErr)
            throw new ProductFormSubmitAborted()
          }
          await createProductMutation.mutateAsync({ body: createBody, staged: stagedImages })
        }}
      />
    </div>
  )
}
