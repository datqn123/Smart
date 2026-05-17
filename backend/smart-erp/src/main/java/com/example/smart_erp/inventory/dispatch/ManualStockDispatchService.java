package com.example.smart_erp.inventory.dispatch;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.Year;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchCreatedData;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchDetailData;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchDetailLineData;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchListItemData;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchListPageData;
import com.example.smart_erp.finance.ledger.BusinessFinanceLedgerPostingService;
import com.example.smart_erp.finance.ledger.dispatch.DispatchLedgerPostingService;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.example.smart_erp.sales.repository.SalesOrderJdbcRepository;
import com.example.smart_erp.sales.stock.RetailStockJdbcRepository;

@Service
public class ManualStockDispatchService {

	private final StockDispatchJdbcRepository dispatchRepo;
	private final RetailStockJdbcRepository retailStockRepo;
	private final StockDispatchNotifier dispatchNotifier;
	private final DispatchLedgerPostingService dispatchLedgerPostingService;

	private final BusinessFinanceLedgerPostingService financeLedgerPostingService;

	private final SalesOrderJdbcRepository salesOrderJdbcRepository;

	public ManualStockDispatchService(StockDispatchJdbcRepository dispatchRepo, RetailStockJdbcRepository retailStockRepo,
			StockDispatchNotifier dispatchNotifier, DispatchLedgerPostingService dispatchLedgerPostingService,
			BusinessFinanceLedgerPostingService financeLedgerPostingService,
			SalesOrderJdbcRepository salesOrderJdbcRepository) {
		this.dispatchRepo = dispatchRepo;
		this.retailStockRepo = retailStockRepo;
		this.dispatchNotifier = dispatchNotifier;
		this.dispatchLedgerPostingService = dispatchLedgerPostingService;
		this.financeLedgerPostingService = financeLedgerPostingService;
		this.salesOrderJdbcRepository = salesOrderJdbcRepository;
	}

	@Transactional(readOnly = true)
	public StockDispatchListPageData list(String search, String status, String dateFrom, String dateTo, boolean mineOnly,
			int page, int limit, Jwt jwt) {
		if (page < 1) {
			page = 1;
		}
		if (limit < 1 || limit > 100) {
			limit = 20;
		}
		String s = search == null ? "" : search;
		Integer creatorFilter = mineOnly ? Integer.valueOf(StockReceiptAccessPolicy.parseUserId(jwt)) : null;
		long total = dispatchRepo.countDispatches(s, status, dateFrom, dateTo, creatorFilter);
		int offset = (page - 1) * limit;
		var items = dispatchRepo.listDispatches(s, status, dateFrom, dateTo, creatorFilter, limit, offset).stream()
				.map(it -> applyListPolicies(jwt, it))
				.toList();
		return new StockDispatchListPageData(items, page, limit, total);
	}

	private static StockDispatchListItemData applyListPolicies(Jwt jwt, StockDispatchListItemData row) {
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		boolean manual = row.manualDispatch();
		boolean locked = DispatchMutationPolicy.isCompletedLockedForMutation(row.status());
		boolean awaitingApproval = dispatchAwaitingApprovalList(row);
		boolean elevated = StockDispatchAccessPolicy.isElevatedDispatchManager(jwt);
		boolean admin = StockDispatchAccessPolicy.isAdmin(jwt);
		boolean creator = uid == row.createdByUserId();
		boolean canMutate = !locked && (awaitingApproval ? (creator || admin) : (creator || elevated));
		return new StockDispatchListItemData(row.id(), row.dispatchCode(), row.orderCode(), row.customerName(),
				row.dispatchDate(), row.userName(), row.itemCount(), row.status(), row.createdByUserId(), manual,
				row.hasStockDispatchLines(), row.shortageWarning(), canMutate, canMutate);
	}

	/** Chờ duyệt / thiếu hàng — áp cho cả phiếu tay và gắn đơn (có stockdispatch_lines). */
	private static boolean dispatchAwaitingApprovalList(StockDispatchListItemData row) {
		if (!row.hasStockDispatchLines()) {
			return false;
		}
		String s = row.status();
		return "Pending".equalsIgnoreCase(s) || "Partial".equalsIgnoreCase(s);
	}

	@Transactional(readOnly = true)
	public StockDispatchDetailData getDetail(long dispatchId, Jwt jwt) {
		var header = dispatchRepo.loadDispatchDetailHeader(dispatchId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy phiếu xuất."));
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		boolean manual = header.orderId() == null;
		boolean stockLinesFulfillment = dispatchRepo.dispatchHasPendingLines(dispatchId);
		boolean locked = DispatchMutationPolicy.isCompletedLockedForMutation(header.status());
		boolean elevated = StockDispatchAccessPolicy.isElevatedDispatchManager(jwt);
		boolean admin = StockDispatchAccessPolicy.isAdmin(jwt);
		boolean creator = uid == header.userId();
		boolean awaitingApproval = dispatchAwaitingApprovalDetail(dispatchId, header.status());
		boolean canEdit = !locked && (awaitingApproval ? (creator || admin) : (creator || elevated));
		boolean canDelete = canEdit;
		boolean shortage = dispatchRepo.detailHasShortage(dispatchId);
		List<StockDispatchDetailLineData> lines = resolveDetailLines(dispatchId);
		String deletedByName = StringUtils.hasText(header.deletedByDisplayName()) ? header.deletedByDisplayName() : null;
		return new StockDispatchDetailData(header.id(), header.dispatchCode(), header.orderCode(),
				header.customerName(), header.dispatchDate(), header.userId(), header.userName(), header.status(),
				header.notes(), header.referenceLabel(), manual, stockLinesFulfillment, shortage, lines, canEdit,
				canDelete, header.deletedAt(), header.deletedByUserId(), deletedByName, header.deleteReason());
	}

	private List<StockDispatchDetailLineData> resolveDetailLines(long dispatchId) {
		List<StockDispatchDetailLineData> outbound = dispatchRepo.loadOutboundLinesForDispatchDetail(dispatchId);
		if (!outbound.isEmpty()) {
			return outbound;
		}
		if (dispatchRepo.dispatchHasPendingLines(dispatchId)) {
			return dispatchRepo.loadManualDetailLines(dispatchId);
		}
		return List.of();
	}

	private boolean dispatchAwaitingApprovalDetail(long dispatchId, String status) {
		if (!dispatchRepo.dispatchHasPendingLines(dispatchId)) {
			return false;
		}
		return "Pending".equalsIgnoreCase(status) || "Partial".equalsIgnoreCase(status);
	}

	@Transactional
	public StockDispatchCreatedData createManual(StockDispatchCreateRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		if (req.lines() == null || req.lines().isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một dòng xuất kho.");
		}
		Map<String, String> errors = new LinkedHashMap<>();
		for (int i = 0; i < req.lines().size(); i++) {
			var line = req.lines().get(i);
			if (line.quantity() <= 0) {
				errors.put("lines[" + i + "].quantity", "Số lượng phải > 0");
			}
		}
		if (!errors.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ.", errors);
		}

		String tmpCode = "TMP-" + UUID.randomUUID().toString().replace("-", "");
		LocalDate dispatchDate = req.dispatchDate();
		String notes = req.notes() == null ? "" : req.notes().trim();
		String ref = req.referenceLabel() == null ? "" : req.referenceLabel().trim();
		long dispatchId = dispatchRepo.insertManualDispatchHeader(tmpCode, userId, dispatchDate,
				ManualDispatchStatuses.PENDING, notes, ref);

		List<String> shortageLines = new ArrayList<>();
		for (var line : req.lines()) {
			var lockedInv = dispatchRepo.lockInventoryRowForUpdate(line.inventoryId())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND,
							"Không tìm thấy dòng tồn kho id=" + line.inventoryId()));
			if (line.quantity() > lockedInv.quantity()) {
				int miss = line.quantity() - lockedInv.quantity();
				String pname = StringUtils.hasText(lockedInv.productName()) ? lockedInv.productName() : "—";
				String sku = StringUtils.hasText(lockedInv.skuCode()) ? lockedInv.skuCode() : "—";
				shortageLines.add(pname + " (" + sku + "): yêu cầu " + line.quantity() + ", tồn "
						+ lockedInv.quantity() + " (thiếu " + miss + ")");
			}
			dispatchRepo.insertDispatchLine(dispatchId, line.inventoryId(), line.quantity(), line.unitPriceSnapshot());
		}

		String finalCode = buildDispatchCode(dispatchId);
		dispatchRepo.updateDispatchCode(dispatchId, finalCode);
		String createdStatus = ManualDispatchStatuses.PENDING;
		if (!shortageLines.isEmpty()) {
			createdStatus = ManualDispatchStatuses.PARTIAL;
			dispatchRepo.updateDispatchStatus(dispatchId, ManualDispatchStatuses.PARTIAL);
		}
		if (!shortageLines.isEmpty()) {
			dispatchNotifier.notifyDispatchShortage(userId, dispatchId, finalCode, shortageLines);
		}
		else {
			dispatchNotifier.notifyManualDispatchCreated(userId, dispatchId, finalCode, ref);
		}
		return new StockDispatchCreatedData(dispatchId, finalCode, dispatchDate, createdStatus, ref);
	}

	@Transactional
	public StockDispatchDetailData patchManual(long dispatchId, StockDispatchPatchRequest patch, Jwt jwt) {
		if (patch == null || !patchHasAny(patch)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Không có thay đổi để cập nhật.");
		}
		var locked = dispatchRepo.lockManualDispatch(dispatchId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy phiếu xuất."));
		if (locked.deletedAt() != null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Phiếu đã bị xóa mềm.");
		}
		if (DispatchMutationPolicy.isCompletedLockedForMutation(locked.status())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Phiếu đã giao hoặc đã hoàn tất xuất — không được sửa.");
		}
		boolean awaitingApproval = dispatchAwaitingApprovalDetail(dispatchId, locked.status());
		if (awaitingApproval) {
			StockDispatchAccessPolicy.assertCreatorOrAdmin(locked.creatorUserId(), jwt);
			return patchAwaitingOwnerDispatch(dispatchId, patch, locked, jwt);
		}

		StockDispatchAccessPolicy.assertCreatorOrElevatedForDispatchEdit(locked.creatorUserId(), jwt);

		if (locked.orderId() != null && !supportsFullManualWorkflow(locked)) {
			patchDispatchHeaderOnly(dispatchId, patch, locked.status(),
					"Phiếu gắn đơn hàng: chỉ sửa được ngày xuất, ghi chú và nhãn tham chiếu (không đổi trạng thái hay dòng qua API này).");
			return getDetail(dispatchId, jwt);
		}

		if (!supportsFullManualWorkflow(locked)) {
			patchDispatchHeaderOnly(dispatchId, patch, locked.status(),
					"Phiếu xuất thủ công (dạng cũ): chỉ sửa được ngày xuất, ghi chú và nhãn tham chiếu.");
			return getDetail(dispatchId, jwt);
		}

		String curr = locked.status();
		if (!ManualDispatchStatuses.isManualLifecycle(curr)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trạng thái phiếu không hợp lệ cho luồng chờ giao.");
		}
		String requested = patch.getStatus();
		String target = !StringUtils.hasText(requested) ? curr : requested.trim();
		if (StringUtils.hasText(requested) && !requested.trim().equalsIgnoreCase(curr)) {
			StockDispatchAccessPolicy.assertCreatorOrAdmin(locked.creatorUserId(), jwt);
		}
		if (!isManualForwardAllowed(curr, target)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Chuyển trạng thái không hợp lệ (" + curr + " → " + target + ").");
		}

		if (patch.getDispatchDate() != null) {
			dispatchRepo.updateDispatchDate(dispatchId, patch.getDispatchDate());
		}
		if (patch.getNotes() != null) {
			dispatchRepo.updateDispatchNotes(dispatchId, patch.getNotes().trim());
		}
		if (patch.getReferenceLabel() != null) {
			dispatchRepo.updateDispatchReference(dispatchId, patch.getReferenceLabel().trim());
		}

		if (patch.getLines() != null) {
			if (patch.getLines().isEmpty()) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách dòng hàng không được rỗng.");
			}
			replaceDispatchLines(dispatchId, patch.getLines(), true);
		}

		if (ManualDispatchStatuses.DELIVERED.equals(target) && !ManualDispatchStatuses.DELIVERED.equals(curr)) {
			finalizeDelivered(dispatchId, StockReceiptAccessPolicy.parseUserId(jwt));
		}
		else if (!curr.equals(target)) {
			dispatchRepo.updateDispatchStatus(dispatchId, target);
		}

		return getDetail(dispatchId, jwt);
	}

	private boolean supportsFullManualWorkflow(StockDispatchJdbcRepository.LockedManualDispatchRow locked) {
		if (!ManualDispatchStatuses.isManualLifecycle(locked.status())) {
			return false;
		}
		if (locked.orderId() == null) {
			return true;
		}
		return dispatchRepo.dispatchHasPendingLines(locked.id());
	}

	private StockDispatchDetailData patchAwaitingOwnerDispatch(long dispatchId, StockDispatchPatchRequest patch,
			StockDispatchJdbcRepository.LockedManualDispatchRow locked, Jwt jwt) {
		if (patch.getStatus() != null && !patch.getStatus().trim().equalsIgnoreCase(locked.status())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Chờ duyệt / thiếu hàng: không đổi trạng thái qua PATCH — dùng API duyệt phiếu khi đủ điều kiện.");
		}
		boolean hadShortage = dispatchRepo.detailHasShortage(dispatchId);
		if (patch.getDispatchDate() != null) {
			dispatchRepo.updateDispatchDate(dispatchId, patch.getDispatchDate());
		}
		if (patch.getNotes() != null) {
			dispatchRepo.updateDispatchNotes(dispatchId, patch.getNotes().trim());
		}
		if (patch.getReferenceLabel() != null) {
			dispatchRepo.updateDispatchReference(dispatchId, patch.getReferenceLabel().trim());
		}
		if (patch.getLines() != null) {
			if (patch.getLines().isEmpty()) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách dòng hàng không được rỗng.");
			}
			replaceDispatchLines(dispatchId, patch.getLines(), false);
			reconcilePendingPartialStatus(dispatchId);
			boolean hasShortage = dispatchRepo.detailHasShortage(dispatchId);
			if (hasShortage && !hadShortage) {
				String code = dispatchRepo.loadDispatchDetailHeader(dispatchId)
						.map(h -> h.dispatchCode())
						.orElse("PX");
				dispatchNotifier.notifyDispatchShortage(StockReceiptAccessPolicy.parseUserId(jwt), dispatchId, code,
						buildShortageLineMessages(dispatchId));
			}
		}
		return getDetail(dispatchId, jwt);
	}

	private void reconcilePendingPartialStatus(long dispatchId) {
		var header = dispatchRepo.loadDispatchDetailHeader(dispatchId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy phiếu xuất."));
		boolean shortage = dispatchRepo.detailHasShortage(dispatchId);
		String st = header.status();
		if (shortage && ManualDispatchStatuses.PENDING.equalsIgnoreCase(st)) {
			dispatchRepo.updateDispatchStatus(dispatchId, ManualDispatchStatuses.PARTIAL);
		}
		else if (!shortage && ManualDispatchStatuses.PARTIAL.equalsIgnoreCase(st)) {
			dispatchRepo.updateDispatchStatus(dispatchId, ManualDispatchStatuses.PENDING);
		}
	}

	private List<String> buildShortageLineMessages(long dispatchId) {
		return dispatchRepo.loadManualDetailLines(dispatchId).stream().filter(StockDispatchDetailLineData::shortageLine)
				.map(l -> {
					int miss = l.quantity() - l.availableQuantity();
					String pname = StringUtils.hasText(l.productName()) ? l.productName() : "—";
					String sku = StringUtils.hasText(l.skuCode()) ? l.skuCode() : "—";
					return pname + " (" + sku + "): yêu cầu " + l.quantity() + ", tồn " + l.availableQuantity()
							+ " (thiếu " + miss + ")";
				}).toList();
	}

	private void patchDispatchHeaderOnly(long dispatchId, StockDispatchPatchRequest patch, String currentStatus,
			String rejectLinesOrStatusHint) {
		if (patch.getLines() != null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, rejectLinesOrStatusHint);
		}
		if (patch.getStatus() != null && !patch.getStatus().trim().equalsIgnoreCase(currentStatus)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, rejectLinesOrStatusHint);
		}
		if (patch.getDispatchDate() != null) {
			dispatchRepo.updateDispatchDate(dispatchId, patch.getDispatchDate());
		}
		if (patch.getNotes() != null) {
			dispatchRepo.updateDispatchNotes(dispatchId, patch.getNotes().trim());
		}
		if (patch.getReferenceLabel() != null) {
			dispatchRepo.updateDispatchReference(dispatchId, patch.getReferenceLabel().trim());
		}
	}

	private static boolean patchHasAny(StockDispatchPatchRequest p) {
		return p.getDispatchDate() != null || p.getNotes() != null || p.getReferenceLabel() != null
				|| StringUtils.hasText(p.getStatus()) || p.getLines() != null;
	}

	private void replaceDispatchLines(long dispatchId, List<StockDispatchLineRequest> lines,
			boolean requireFullStockCoverage) {
		Map<String, String> errors = new LinkedHashMap<>();
		for (int i = 0; i < lines.size(); i++) {
			var line = lines.get(i);
			if (line.quantity() <= 0) {
				errors.put("lines[" + i + "].quantity", "Số lượng phải > 0");
			}
		}
		if (!errors.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ.", errors);
		}

		dispatchRepo.deleteLinesByDispatch(dispatchId);
		for (var line : lines) {
			var lockedInv = dispatchRepo.lockInventoryRowForUpdate(line.inventoryId())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND,
							"Không tìm thấy dòng tồn kho id=" + line.inventoryId()));
			if (requireFullStockCoverage && line.quantity() > lockedInv.quantity()) {
				errors.put("inventoryId", "Thiếu hàng: inventory id=" + line.inventoryId() + " — yêu cầu "
						+ line.quantity() + ", trong kho " + lockedInv.quantity());
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không đủ tồn cho ít nhất một dòng (kiểm tra số lượng).", errors);
			}
			dispatchRepo.insertDispatchLine(dispatchId, line.inventoryId(), line.quantity(), line.unitPriceSnapshot());
		}
	}

	private void finalizeDelivered(long dispatchId, int userId) {
		if (dispatchRepo.countOutboundLogs(dispatchId) > 0) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Phiếu đã ghi nhận xuất kho trước đó.");
		}
		var lines = new ArrayList<>(dispatchRepo.loadPendingLinesOrdered(dispatchId));
		if (lines.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Phiếu không có dòng hàng để giao.");
		}
		for (var row : lines) {
			var locked = dispatchRepo.lockInventoryRowForUpdate(row.inventoryId())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND,
							"Không tìm thấy dòng tồn id=" + row.inventoryId()));
			if (row.quantity() > locked.quantity()) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Thiếu hàng tại thời điểm xác nhận đã giao: tồn "
						+ locked.quantity() + ", cần " + row.quantity());
			}
			BigDecimal rate = locked.lineConversionRate() == null ? BigDecimal.ONE : locked.lineConversionRate();
			int baseQty = rate.multiply(BigDecimal.valueOf(row.quantity())).setScale(0, RoundingMode.DOWN).intValue();
			if (baseQty <= 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST,
						"Số lượng quy đổi đơn vị cơ sở không hợp lệ cho inventory id=" + row.inventoryId());
			}
			dispatchRepo.deductInventoryQuantity(locked.id(), row.quantity());
			String logNote = "MANUAL_DISPATCH_DELIVERED invId=" + locked.id();
			retailStockRepo.insertInventoryLogOutbound(locked.productId(), baseQty, locked.baseUnitId(), userId,
					dispatchId, locked.locationId(), logNote);
		}
		dispatchRepo.updateDispatchStatus(dispatchId, ManualDispatchStatuses.DELIVERED);
		dispatchLedgerPostingService.postPrimaryCogsIfAbsent(dispatchId, userId);
		dispatchRepo.findOrderIdByDispatchId(dispatchId).flatMap(salesOrderJdbcRepository::loadOrderFinancialForLedger)
				.ifPresent(fin -> financeLedgerPostingService.tryPostOrderLedgerOnFinancialState(fin, userId));
	}

	private static boolean isManualForwardAllowed(String curr, String next) {
		if (!StringUtils.hasText(next)) {
			return true;
		}
		if (curr.equalsIgnoreCase(next)) {
			return true;
		}
		if (ManualDispatchStatuses.DELIVERED.equalsIgnoreCase(curr)) {
			return false;
		}
		if (ManualDispatchStatuses.WAITING_DISPATCH.equalsIgnoreCase(curr)) {
			return ManualDispatchStatuses.DELIVERING.equalsIgnoreCase(next)
					|| ManualDispatchStatuses.DELIVERED.equalsIgnoreCase(next);
		}
		if (ManualDispatchStatuses.DELIVERING.equalsIgnoreCase(curr)) {
			return ManualDispatchStatuses.DELIVERED.equalsIgnoreCase(next);
		}
		return false;
	}

	@Transactional
	public void softDeleteManual(long dispatchId, StockDispatchSoftDeleteRequest body, Jwt jwt) {
		var locked = dispatchRepo.lockManualDispatch(dispatchId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy phiếu xuất."));
		if (locked.deletedAt() != null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Phiếu đã bị xóa mềm.");
		}
		if (DispatchMutationPolicy.isCompletedLockedForMutation(locked.status())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Không xóa mềm phiếu đã giao hoặc đã hoàn tất xuất.");
		}
		boolean awaitingApproval = dispatchAwaitingApprovalDetail(dispatchId, locked.status());
		if (awaitingApproval) {
			StockDispatchAccessPolicy.assertCreatorOrAdmin(locked.creatorUserId(), jwt);
		}
		else {
			StockDispatchAccessPolicy.assertCreatorOrElevatedForSoftDelete(locked.creatorUserId(), jwt);
		}
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		dispatchRepo.markSoftDeleted(dispatchId, uid, body.reason().trim());
	}

	@Transactional
	public StockDispatchDetailData approveOrderLinkedDispatch(long dispatchId, Jwt jwt) {
		if (!StockDispatchAccessPolicy.isAdmin(jwt)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Chỉ Admin được duyệt phiếu xuất.");
		}
		var locked = dispatchRepo.lockManualDispatch(dispatchId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy phiếu xuất."));
		if (locked.deletedAt() != null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Phiếu đã bị xóa mềm.");
		}
		if (!dispatchRepo.dispatchHasPendingLines(dispatchId)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Phiếu không có dòng stockdispatch_lines — không duyệt qua API này.");
		}
		String st = locked.status();
		if (!ManualDispatchStatuses.PENDING.equalsIgnoreCase(st) && !ManualDispatchStatuses.PARTIAL.equalsIgnoreCase(st)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Chỉ duyệt khi phiếu đang Chờ duyệt (Pending) hoặc Một phần (Partial).");
		}
		if (dispatchRepo.detailHasShortage(dispatchId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Còn thiếu tồn — không duyệt được.");
		}
		dispatchRepo.updateDispatchStatus(dispatchId, ManualDispatchStatuses.WAITING_DISPATCH);
		return getDetail(dispatchId, jwt);
	}

	private static String buildDispatchCode(long dispatchId) {
		int year = Year.now(ZoneId.systemDefault()).getValue();
		return "PX-" + year + "-" + String.format("%06d", dispatchId);
	}
}
