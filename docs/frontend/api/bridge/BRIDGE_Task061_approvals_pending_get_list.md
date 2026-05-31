# BRIDGE — Task061 — `GET /api/v1/approvals/pending`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task061 |
| **Path** | `GET /api/v1/approvals/pending` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + 200 envelope | `API_Task061_approvals_pending_get_list.md` §4–§6 | [`ApprovalsController.java`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/inventory/controller/ApprovalsController.java) `GET /approvals/pending` | [`approvalsApi.ts`](../../../mini-erp/src/features/approvals/api/approvalsApi.ts) — `getPendingApprovals`, `APPROVALS_PENDING_QUERY_KEY`. [`PendingApprovalsPage.tsx`](../../../mini-erp/src/features/approvals/pages/PendingApprovalsPage.tsx) — `useQuery` + map → `OrderTable`. | **Y** | — |
| Query `search`, `type`, `fromDate`, `toDate`, `page`, `limit` | §5 | `ApprovalsService.listPending` | `getPendingApprovals` build `URLSearchParams`; UI: debounce search 400ms; lọc loại `all` \| `Inbound`; ngày → `fromDate`/`toDate`; `page` + `limit=50`. | **Y** | Mở rộng loại khi BE có UNION. |
| `summary` / `items` | §6 | `ApprovalsPendingPageData` | Badge dùng `summary.totalPending` (fallback `total`); bảng `data.items`. | **Y** | — |
| RBAC Staff 403 | §4 | `ApprovalsAccessPolicy` | `apiJson` → toast lỗi; khối “Thử lại” khi `isError`. | **Y** | Guard route/menu Owner/Admin (tùy PM). |
| `fromDate` > `toDate` → 400 | §5 | `assertDateOrder` | FE không chặn trước; BE trả 400 → toast. | **Y** | Có thể thêm validate client. |
| Duyệt / từ chối → Task019/020 | §2 bảng | `POST …/stock-receipts/{id}/approve` \| `reject` | [`stockReceiptsApi.ts`](../../../mini-erp/src/features/inventory/api/stockReceiptsApi.ts) — `approveStockReceipt`, `rejectStockReceipt`; dialog chọn `inboundLocationId` (seed options); `invalidateQueries(APPROVALS_PENDING_QUERY_KEY)`. | **Y** (Inbound MVP) | Outbound/Return/Debt chờ API sau. |

## Kết luận (≤5 dòng)

1. **wire-fe** hoàn tất: `features/approvals/api/approvalsApi.ts` + `PendingApprovalsPage` dùng TanStack Query, không còn mock pending trên màn này.  
2. **Phê duyệt** gọi Task019 kèm dialog chọn vị trí nhập; **từ chối** gọi Task020 + lý do.  
3. **`npm run build`** (mini-erp) pass.  
4. **`useApprovalStore`** vẫn phục vụ mock **Lịch sử** (`ApprovalHistoryPage`) — Task062 `wire-fe` tách riêng.  
5. Cập nhật bridge sau khi bật guard menu/route nếu team yêu cầu.
