# BRIDGE — Task062 — `GET /api/v1/approvals/history`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task062 |
| **Path** | `GET /api/v1/approvals/history` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + 200 | `API_Task062_approvals_history_get_list.md` §4–§6 | [`ApprovalsController`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/inventory/controller/ApprovalsController.java) `GET /approvals/history` | [`approvalsApi.ts`](../../../mini-erp/src/features/approvals/api/approvalsApi.ts) — `getApprovalsHistory`, `APPROVALS_HISTORY_QUERY_KEY`. [`ApprovalHistoryPage.tsx`](../../../mini-erp/src/features/approvals/pages/ApprovalHistoryPage.tsx) — `useQuery`. | **Y** | — |
| Query `resolution`, `search`, `type`, `fromDate`, `toDate`, `page`, `limit` | §5 | `ApprovalsService.listHistory` (default `limit=20`) | URLSearchParams; debounce search 400ms; `resolution` / `type` / ngày / phân trang. | **Y** | — |
| Cột `reviewedAt`, `resolution`, `rejectionReason`, `reviewerName` | §6 | `ApprovalsHistoryItemData` + JDBC SELECT | [`ApprovalHistoryTable.tsx`](../../../mini-erp/src/features/approvals/components/ApprovalHistoryTable.tsx) — bảng riêng (không dùng `OrderTable` vì thiếu cột nghiệp vụ). | **Y** | — |
| Lọc ngày theo `reviewed_at::date` | §5 | `buildHistoryWhere` | `fromDate` / `toDate` gửi lên BE. | **Y** | — |
| RBAC Owner/Admin; Staff 403 | §4 | `ApprovalsAccessPolicy` | `apiJson` + toast + khối Thử lại. | **Y** | — |
| MVP `type` chỉ Inbound / all | §3, §5 | `showsInboundHistory` | Select `all` \| `Inbound`. | **Y** | — |
| Làm mới lịch sử sau duyệt/từ chối | — | — | [`PendingApprovalsPage`](../../../mini-erp/src/features/approvals/pages/PendingApprovalsPage.tsx) invalidate `APPROVALS_HISTORY_QUERY_KEY` cùng pending. | **Y** | — |

## Kết luận (≤5 dòng)

1. **wire-fe** hoàn tất: `getApprovalsHistory` + `ApprovalHistoryPage` + `ApprovalHistoryTable` (đủ cột spec).  
2. **`OrderDetailDialog`** chỉ hiển thị tóm tắt map từ dòng lịch sử (không phải chi tiết phiếu nhập đầy đủ).  
3. **`useApprovalStore`** không còn được import — file store vẫn trong repo (có thể xóa/refactor sau).  
4. **`npm run build`** pass.  
5. Nếu cần UI chi tiết phiếu nhập từ lịch sử → nối `GET /stock-receipts/{id}` (Task015) trong dialog.
